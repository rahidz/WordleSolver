import tkinter as tk
from tkinter import ttk, messagebox
from solver import WordleSolver, Results, Distribution
import concurrent.futures
from typing import List, Tuple, Dict, Set, Optional, Any

# --- Constants for UI colors ---
COLORS: Dict[str, Tuple[str, str]] = {
    "default": ("white", "black"),
    "green": ("#6aaa64", "white"),
    "yellow": ("#c9b458", "white"),
    "gray": ("#808080", "white"),  # Not in word
}

class WordleUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.solver = WordleSolver()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.letter_cells: List['LetterCell'] = []

        self.setup_ui()

    def setup_ui(self) -> None:
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
    def create_treeview(self, parent: tk.Widget, text: str, columns: Tuple[str, ...], row: int) -> ttk.Treeview:
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

    def on_word_length_change(self, *args: Any) -> None:
        try:
            length = int(self.word_length_var.get())
            if length > 0:
                self.rebuild_grid(length)
        except ValueError:
            pass # Ignore non-integer input

    def rebuild_grid(self, word_length: int, rows: int = 6) -> None:
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

    def reset_all(self) -> None:
        for cell in self.letter_cells:
            cell.reset()
        self.not_allowed_entry.delete(0, tk.END)
        self.status_text.set("")
        for tree in [self.output_tree, self.letter_tree, self.best_guesses_tree, self.remaining_words_tree]:
            for item in tree.get_children():
                tree.delete(item)

    def apply_filter(self) -> None:
        try:
            word_length = int(self.word_length_var.get())
        except ValueError:
            messagebox.showerror("Input Error", "Word Length must be an integer.")
            return

        pattern_list: List[str] = ["_"] * word_length
        not_allowed_letters: Set[str] = set(self.not_allowed_entry.get().strip().lower())
        misplaced_map: Dict[str, Set[int]] = {}

        for i, cell in enumerate(self.letter_cells):
            letter, state = cell.get_state()
            pos_1_based = (i % word_length) + 1

            if not letter or state == "default":
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
            elif state == "gray":
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

    def run_full_filter(self, word_length: int, pattern: str, not_allowed: str, misplaced_input: str, used_letters: Set[str], not_allowed_letters: Set[str]) -> Tuple[Results, Set[str], Set[str], int, List[Tuple[str, float]], Distribution]:
        min_freq = int(self.min_freq_var.get())
        filtered_results = self.solver.filter_words(
            word_length, pattern, not_allowed, misplaced_input
        )
        overall_distribution, _ = self.solver.compute_letter_distributions(filtered_results)
        best_guess_list = self.solver.best_guesses(filtered_results, overall_distribution, min_frequency=min_freq)
        
        return filtered_results, used_letters, not_allowed_letters, word_length, best_guess_list, overall_distribution

    def on_filter_complete(self, future: concurrent.futures.Future) -> None:
        try:
            results, used_letters, not_allowed_letters, word_length, best_guess_list, overall_distribution = future.result()
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"An error occurred: {e}"))
            self.root.after(0, lambda: self.filter_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.status_text.set("Error during filtering"))
            return

        self.root.after(0, self.update_ui, results, best_guess_list, overall_distribution, used_letters, not_allowed_letters, word_length)

    def update_ui(self, results: Results, best_guess_list: List[Tuple[str, float]], overall_distribution: Distribution, used_letters: Set[str], not_allowed_letters: Set[str], word_length: int) -> None:
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

    def reset_results(self) -> None:
        for tree in [self.output_tree, self.letter_tree, self.best_guesses_tree, self.remaining_words_tree]:
            for item in tree.get_children():
                tree.delete(item)



# --- LetterCell Class for the input grid ---
class LetterCell(tk.Frame):
    def __init__(self, master: tk.Widget, width: int = 40, height: int = 40, app: Optional['WordleUI'] = None) -> None:
        super().__init__(master, width=width, height=height, borderwidth=1, relief="solid")
        self.pack_propagate(False)
        self.app = app

        self.char_var = tk.StringVar()
        self._trace_id = self.char_var.trace_add("write", self._on_text_change)

        self.entry = tk.Entry(
            self,
            textvariable=self.char_var,
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

        self.color_state: str = "default"
        self.entry.bind("<KeyRelease>", self.on_key_release)
        self.entry.bind("<Button-1>", self.on_click)

    def _on_text_change(self, *args: Any) -> None:
        text = self.char_var.get()
        new_text = ""
        if text:
            char = text[-1]
            if char.isalpha():
                new_text = char.upper()

        if self.char_var.get() != new_text:
            self.char_var.trace_vdelete("w", self._trace_id)
            self.char_var.set(new_text)
            self.entry.icursor(tk.END)
            self._trace_id = self.char_var.trace_add("write", self._on_text_change)

    def on_key_release(self, event: tk.Event) -> None:
        # Set initial color to gray if a letter is typed, or back to default if empty
        if self.char_var.get() and self.color_state == "default":
            self.set_color("gray")
        elif not self.char_var.get():
            self.set_color("default")

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
        # Auto-tab to next cell only on character entry
        elif self.char_var.get() and event.keysym not in ["BackSpace", "Delete", "Tab", "Shift_L", "Shift_R"]:
            next_widget = self.tk_focusNext()
            if next_widget:
                next_widget.focus_set()

    def on_click(self, event: tk.Event) -> None:
        # Cycle through colors on click: Gray -> Yellow -> Green -> Gray
        if self.color_state == "gray":
            self.set_color("yellow")
        elif self.color_state == "yellow":
            self.set_color("green")
        elif self.color_state == "green":
            self.set_color("gray")
        # Do nothing if state is "default" (cell is empty)

    def set_color(self, color_name: str) -> None:
        self.color_state = color_name
        bg, fg = COLORS[color_name]
        self.entry.config(bg=bg, fg=fg, insertbackground=fg)

    def get_letter(self) -> str:
        return self.char_var.get().lower()

    def get_state(self) -> Tuple[str, str]:
        return self.get_letter(), self.color_state

    def reset(self) -> None:
        self.char_var.set("")
        self.set_color("default")

if __name__ == "__main__":
    root = tk.Tk()
    app = WordleUI(root)
    root.mainloop()