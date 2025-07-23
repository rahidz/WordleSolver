import tkinter as tk
from tkinter import ttk, messagebox
from solver import WordleSolver
import concurrent.futures

# --- Constants for UI colors ---
COLORS = {
    "default": ("white", "black"),
    "green": ("#6aaa64", "white"),
    "yellow": ("#c9b458", "white"),
}

class WordleUI:
    def __init__(self, root):
        self.root = root
        self.solver = WordleSolver()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.letter_cells = []

        self.setup_ui()

    def setup_ui(self):
        self.root.title("Wordle Helper")
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")

        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky="nsew")
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=10)

        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # --- Word Length ---
        tk.Label(left_frame, text="Word Length:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.word_length_var = tk.StringVar(value="5")
        self.word_length_var.trace_add("write", self.on_word_length_change)
        word_length_entry = ttk.Entry(left_frame, width=10, textvariable=self.word_length_var)
        word_length_entry.grid(row=0, column=1, pady=2)

        # --- Input Grid ---
        tk.Label(left_frame, text="Pattern:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.grid_frame = ttk.Frame(left_frame)
        self.grid_frame.grid(row=1, column=1, pady=2, sticky=tk.W)
        self.rebuild_grid(5)

        # --- Not Allowed Letters ---
        tk.Label(left_frame, text="Letters not in word:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.not_allowed_entry = ttk.Entry(left_frame, width=20)
        self.not_allowed_entry.grid(row=2, column=1, pady=2)

        # --- Action Buttons ---
        action_frame = ttk.Frame(left_frame)
        action_frame.grid(row=3, column=0, columnspan=2, pady=10)
        self.filter_button = ttk.Button(action_frame, text="Filter Words", command=self.apply_filter)
        self.filter_button.pack(side="left", padx=5)
        reset_button = ttk.Button(action_frame, text="Reset", command=self.reset_all)
        reset_button.pack(side="left", padx=5)

        # --- Status Label ---
        self.status_text = tk.StringVar()
        status_label = ttk.Label(left_frame, textvariable=self.status_text)
        status_label.grid(row=4, column=0, columnspan=2, pady=5)

        # --- Treeviews ---
        self.output_tree = self.create_treeview(left_frame, "Filtered Words Preview", ("Word", "Frequency"), 6)
        self.letter_tree = self.create_treeview(left_frame, "Overall Letter Distribution", ("Letter", "Count"), 7)
        self.best_guesses_tree = self.create_treeview(right_frame, "Best Guesses", ("Word", "Score"), 0)
        self.best_guesses_tree.tag_configure("possible", background="#d5f5d5")
        self.best_guesses_tree.tag_configure("probe", background="#e0e0e0")

        # --- Remaining Words ---
        remaining_words_frame = ttk.LabelFrame(right_frame, text="Words from Remaining Letters", padding="5")
        remaining_words_frame.grid(row=1, column=0, pady=10, sticky="nsew")
        min_freq_frame = ttk.Frame(remaining_words_frame)
        min_freq_frame.pack(fill="x", pady=(0, 5))
        ttk.Label(min_freq_frame, text="Minimum Frequency:").pack(side="left", padx=(0, 5))
        self.min_freq_var = tk.StringVar(value="100000")
        min_freq_entry = ttk.Entry(min_freq_frame, textvariable=self.min_freq_var, width=10)
        min_freq_entry.pack(side="left")
        self.remaining_words_tree = self.create_treeview(remaining_words_frame, "", ("Word", "Score"), -1) # No grid row

        right_frame.rowconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=2)
        right_frame.columnconfigure(0, weight=1)
    def create_treeview(self, parent, text, columns, row):
        frame = ttk.LabelFrame(parent, text=text, padding="5")
        if row != -1:
            frame.grid(row=row, column=0, columnspan=2, pady=10, sticky="we")
        else:
            frame.pack(fill="both", expand=True)

        tree = ttk.Treeview(frame, columns=columns, show="headings", height=10)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        
        vsb.pack(side="right", fill="y")
        tree.pack(side="left", fill="both", expand=True)
        return tree

    def on_word_length_change(self, *args):
        try:
            length = int(self.word_length_var.get())
            if length > 0:
                self.rebuild_grid(length)
        except ValueError:
            pass # Ignore non-integer input

    def rebuild_grid(self, word_length, rows=6):
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        self.letter_cells.clear()

        for r in range(rows):
            row_frame = tk.Frame(self.grid_frame)
            row_frame.pack(side="top", pady=2)
            for c in range(word_length):
                cell = LetterCell(row_frame, app=self)
                cell.pack(side="left", padx=2)
                self.letter_cells.append(cell)

    def reset_all(self):
        for cell in self.letter_cells:
            cell.reset()
        self.not_allowed_entry.delete(0, tk.END)
        self.status_text.set("")
        for tree in [self.output_tree, self.letter_tree, self.best_guesses_tree, self.remaining_words_tree]:
            for item in tree.get_children():
                tree.delete(item)

    def apply_filter(self):
        try:
            word_length = int(self.word_length_var.get())
        except ValueError:
            messagebox.showerror("Input Error", "Word Length must be an integer.")
            return

        pattern_list = ["_"] * word_length
        not_allowed_letters = set(self.not_allowed_entry.get().strip().lower())
        misplaced_map = {}

        for i, cell in enumerate(self.letter_cells):
            letter, state = cell.get_state()
            pos_1_based = (i % word_length) + 1

            if not letter or state == "ignored":
                continue

            if state == "green":
                if pattern_list[pos_1_based - 1] != "_" and pattern_list[pos_1_based - 1] != letter:
                    messagebox.showerror("Input Error", f"Contradiction at position {pos_1_based}.")
                    return
                pattern_list[pos_1_based - 1] = letter
            elif state == "yellow":
                if letter not in misplaced_map:
                    misplaced_map[letter] = set()
                misplaced_map[letter].add(pos_1_based)
            else:
                not_allowed_letters.add(letter)

        for p_letter in pattern_list:
            if p_letter != "_" and p_letter in not_allowed_letters:
                not_allowed_letters.remove(p_letter)

        pattern_input = "".join(pattern_list)
        not_allowed_input = "".join(sorted(list(not_allowed_letters)))
        misplaced_input = "; ".join(
            f"{letter}:{','.join(map(str, sorted(positions)))}"
            for letter, positions in misplaced_map.items()
        )

        self.filter_button.config(state=tk.DISABLED)
        self.status_text.set("Filtering...")
        self.reset_results()

        future = self.executor.submit(
            self.run_full_filter,
            word_length,
            pattern_input,
            not_allowed_input,
            misplaced_input,
            {l for l, s in misplaced_map.items()} | {p for p in pattern_list if p != "_"},
            not_allowed_letters
        )
        future.add_done_callback(self.on_filter_complete)

    def run_full_filter(self, word_length, pattern, not_allowed, misplaced_input, used_letters, not_allowed_letters):
        filtered_results = self.solver.filter_words(
            word_length, pattern, not_allowed, misplaced_input
        )
        overall_distribution, _ = self.solver.compute_letter_distributions(filtered_results)
        best_guess_list = self.solver.best_guesses(filtered_results, overall_distribution)
        
        return filtered_results, used_letters, not_allowed_letters, word_length, best_guess_list, overall_distribution

    def on_filter_complete(self, future):
        try:
            results, used_letters, not_allowed_letters, word_length, best_guess_list, overall_distribution = future.result()
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"An error occurred: {e}"))
            self.root.after(0, lambda: self.filter_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.status_text.set("Error during filtering"))
            return

        self.root.after(0, self.update_ui, results, best_guess_list, overall_distribution, used_letters, not_allowed_letters, word_length)

    def update_ui(self, results, best_guess_list, overall_distribution, used_letters, not_allowed_letters, word_length):
        try:
            with open("sorted_filtered_words.txt", "w") as outfile:
                for word, freq in results:
                    outfile.write(f"{word},{freq}\n")
        except Exception as e:
            messagebox.showerror("File Error", f"An error occurred while writing the output file: {e}")

        self.status_text.set(f"Found {len(results)} words. Results saved to sorted_filtered_words.txt")

        for word, frequency in results:
            self.output_tree.insert("", tk.END, values=(word, frequency))

        for letter, freq in sorted(overall_distribution.items(), key=lambda x: x[1], reverse=True):
            self.letter_tree.insert("", tk.END, values=(letter, freq))

        possible_answers = {word for word, _ in results}
        for word, score in best_guess_list:
            tag = "possible" if word in possible_answers else "probe"
            self.best_guesses_tree.insert("", tk.END, values=(word, f"{score:.2f}"), tags=(tag,))

        try:
            min_freq = int(self.min_freq_var.get())
        except ValueError:
            min_freq = 0
            
        remaining_words = self.solver.find_words_from_remaining_letters(
            used_letters, not_allowed_letters, overall_distribution, word_length, min_freq
        )
        for word, score in remaining_words:
            self.remaining_words_tree.insert("", tk.END, values=(word, score))

        self.filter_button.config(state=tk.NORMAL)

    def reset_results(self):
        for tree in [self.output_tree, self.letter_tree, self.best_guesses_tree, self.remaining_words_tree]:
            for item in tree.get_children():
                tree.delete(item)



# --- LetterCell Class for the input grid ---
class LetterCell(tk.Frame):
    def __init__(self, master, width=40, height=40, app=None):
        super().__init__(master, width=width, height=height, borderwidth=1, relief="solid")
        self.pack_propagate(False)
        self.app = app

        self.entry = tk.Entry(
            self,
            justify="center",
            font=("Helvetica", 16, "bold"),
            borderwidth=0,
            highlightthickness=0,
            bg=COLORS["default"][0],
            fg=COLORS["default"][1],
            insertbackground=COLORS["default"][1], # cursor color
            width=2,
        )
        self.entry.pack(expand=True, fill="both")

        self.color_state = "default"
        self.entry.bind("<KeyRelease>", self.on_key_release)
        self.entry.bind("<Button-1>", self.on_click)

    def on_key_release(self, event):
        if not self.app:
            return

        # Move focus based on key press
        if event.keysym == "Left":
            prev_widget = self.tk_focusPrev()
            if prev_widget:
                prev_widget.focus_set()
        elif event.keysym == "Right":
            next_widget = self.tk_focusNext()
            if next_widget:
                next_widget.focus_set()
        elif event.keysym == "Up":
            # Manually navigate up
            current_index = self.app.letter_cells.index(self)
            word_length = int(self.app.word_length_var.get())
            up_index = current_index - word_length
            if up_index >= 0:
                self.app.letter_cells[up_index].entry.focus_set()
        elif event.keysym == "Down":
            # Manually navigate down
            current_index = self.app.letter_cells.index(self)
            word_length = int(self.app.word_length_var.get())
            down_index = current_index + word_length
            if down_index < len(self.app.letter_cells):
                self.app.letter_cells[down_index].entry.focus_set()
        elif self.entry.get():
            next_widget = self.tk_focusNext()
            if next_widget:
                next_widget.focus_set()

    def on_click(self, event):
        # Cycle through colors on click
        if self.color_state == "default":
            self.set_color("ignored")
        elif self.color_state == "ignored":
            self.set_color("yellow")
        elif self.color_state == "yellow":
            self.set_color("green")
        else:  # Green
            self.set_color("default")

    def set_color(self, color_name):
        self.color_state = color_name
        
        # Use "default" colors for the "ignored" state
        effective_color_name = "default" if color_name == "ignored" else color_name
        bg, fg = COLORS[effective_color_name]
        
        self.entry.config(bg=bg, fg=fg, insertbackground=fg)

    def get_letter(self):
        return self.entry.get().lower()

    def get_state(self):
        return self.get_letter(), self.color_state

    def reset(self):
        self.entry.delete(0, tk.END)
        self.set_color("default")

if __name__ == "__main__":
    root = tk.Tk()
    app = WordleUI(root)
    root.mainloop()