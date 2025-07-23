import tkinter as tk
from tkinter import ttk, messagebox
import filters  # Import the filtering module
import concurrent.futures

# --- Constants for UI colors ---
COLORS = {
    "default": ("white", "black"),
    "green": ("#6aaa64", "white"),
    "yellow": ("#c9b458", "white"),
}

# --- LetterCell Class for the input grid ---
class LetterCell(tk.Frame):
    def __init__(self, master, width=40, height=40):
        super().__init__(master, width=width, height=height, borderwidth=1, relief="solid")
        self.pack_propagate(False)

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
            current_index = letter_cells.index(self)
            word_length = int(word_length_var.get())
            up_index = current_index - word_length
            if up_index >= 0:
                letter_cells[up_index].entry.focus_set()
        elif event.keysym == "Down":
            # Manually navigate down
            current_index = letter_cells.index(self)
            word_length = int(word_length_var.get())
            down_index = current_index + word_length
            if down_index < len(letter_cells):
                letter_cells[down_index].entry.focus_set()
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

# Thread pool for running filtering in background
executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

def run_full_filter(word_length, pattern, not_allowed, misplaced_input, used_letters, not_allowed_letters):
    """
    Wrapper to run filtering and return all necessary data for the UI update.
    """
    word_list = filters._load_word_list("frequency.txt")
    
    filtered_results = filters.filter_words(
        "frequency.txt",
        word_length,
        pattern,
        not_allowed,
        misplaced_input,
    )

    # --- Best Guesses Calculation ---
    overall_distribution, _ = filters.compute_letter_distributions(filtered_results)
    
    best_guess_list = filters.best_guesses(
        filtered_results,
        word_list,
        overall_distribution
    )
    
    return filtered_results, word_list, used_letters, not_allowed_letters, word_length, best_guess_list, overall_distribution

def apply_filter():
    # Retrieve user inputs from the GUI.
    word_length_input = word_length_entry.get().strip()
    # --- Derive filter inputs from the grid state ---
    # --- Derive filter inputs from the grid state ---
    word_length = int(word_length_var.get())
    pattern_list = ["_"] * word_length
    not_allowed_letters = set(not_allowed_entry.get().strip().lower())
    misplaced_map = {}
    
    # Process all cells in the grid
    for i, cell in enumerate(letter_cells):
        letter, state = cell.get_state()
        pos_1_based = (i % word_length) + 1

        if not letter or state == "ignored":
            continue

        if state == "green":
            # If a different letter is already locked in, it's a contradiction.
            if pattern_list[pos_1_based - 1] != "_" and pattern_list[pos_1_based - 1] != letter:
                messagebox.showerror("Input Error", f"Contradiction at position {pos_1_based}.")
                return
            pattern_list[pos_1_based - 1] = letter
        elif state == "yellow":
            if letter not in misplaced_map:
                misplaced_map[letter] = set()
            misplaced_map[letter].add(pos_1_based)
        else:  # "default"
            not_allowed_letters.add(letter)

    # A letter in the pattern cannot also be disallowed.
    for p_letter in pattern_list:
        if p_letter != "_" and p_letter in not_allowed_letters:
            not_allowed_letters.remove(p_letter)

    pattern_input = "".join(pattern_list)
    not_allowed_input = "".join(sorted(list(not_allowed_letters)))
    
    misplaced_input = "; ".join(
        f"{letter}:{','.join(map(str, sorted(positions)))}"
        for letter, positions in misplaced_map.items()
    )

    # Convert word length to integer if provided.
    word_length = None
    if word_length_input:
        try:
            word_length = int(word_length_input)
        except ValueError:
            messagebox.showerror("Input Error", "Word Length must be an integer.")
            return

    # Disable filter button and show status
    filter_button.config(state=tk.DISABLED)
    status_text.set("Filtering...")

    # Clear existing results
    for item in output_tree.get_children():
        output_tree.delete(item)
    for item in letter_tree.get_children():
        letter_tree.delete(item)
    if 'best_guesses_tree' in globals():
        for item in best_guesses_tree.get_children():
            best_guesses_tree.delete(item)
    if 'remaining_words_tree' in globals():
        for item in remaining_words_tree.get_children():
            remaining_words_tree.delete(item)

    # Submit filtering to background thread
    future = executor.submit(
        run_full_filter,
        word_length,
        pattern_input,
        not_allowed_input,
        misplaced_input,
        {l for l, s in misplaced_map.items()} | {p for p in pattern_list if p != "_"},
        not_allowed_letters
    )
    future.add_done_callback(on_filter_complete)

def on_filter_complete(future):
    try:
        results, word_list, used_letters, not_allowed_letters, word_length, best_guess_list, overall_distribution = future.result()
    except FileNotFoundError as e:
        root.after(0, lambda: messagebox.showerror("File Error", str(e)))
        root.after(0, lambda: filter_button.config(state=tk.NORMAL))
        root.after(0, lambda: status_text.set("Error: file not found"))
        return
    except Exception as e:
        root.after(0, lambda: messagebox.showerror("Error", f"An error occurred: {e}"))
        root.after(0, lambda: filter_button.config(state=tk.NORMAL))
        root.after(0, lambda: status_text.set("Error during filtering"))
        return

    def update_ui(results, best_guess_list, overall_distribution):
        # Write results to an output file.
        try:
            with open("sorted_filtered_words.txt", "w") as outfile:
                for word, freq in results:
                    outfile.write(f"{word},{freq}\n")
        except Exception as e:
            messagebox.showerror("File Error", f"An error occurred while writing the output file: {e}")
            return

        # Update status label
        status_text.set(
            f"Filtering complete. {len(results)} words found. Results saved to sorted_filtered_words.txt"
        )

        # Update the Filtered Words Treeview
        for word, frequency in results:
            output_tree.insert("", tk.END, values=(word, frequency))

        # Update the Letter Distribution Treeview
        for letter, freq in sorted(overall_distribution.items(), key=lambda x: x[1], reverse=True):
            letter_tree.insert("", tk.END, values=(letter, freq))

        # --- Best Guesses (with color-coding) ---
        possible_answers = {word for word, _ in results}
        for word, score in best_guess_list:
            tag = "possible" if word in possible_answers else "probe"
            best_guesses_tree.insert("", tk.END, values=(word, f"{score:.2f}"), tags=(tag,))

        # --- Update Words from Remaining Letters ---
        try:
            min_freq = int(min_freq_var.get())
        except ValueError:
            min_freq = 0 # Default to 0 if input is invalid
            
        remaining_words = filters.find_words_from_remaining_letters(
            word_list, used_letters, not_allowed_letters, overall_distribution, word_length, min_freq
        )
        for word, score in remaining_words:
            remaining_words_tree.insert("", tk.END, values=(word, score))

        # Re-enable filter button
        filter_button.config(state=tk.NORMAL)

    root.after(0, update_ui, results, best_guess_list, overall_distribution)

def rebuild_grid(word_length, rows=6):
    # Clear existing widgets from the grid_frame
    for widget in grid_frame.winfo_children():
        widget.destroy()
    letter_cells.clear()

    # Create new cells in a grid
    for r in range(rows):
        row_frame = tk.Frame(grid_frame)
        row_frame.pack(side="top", pady=2)
        for c in range(word_length):
            cell = LetterCell(row_frame)
            cell.pack(side="left", padx=2)
            letter_cells.append(cell)

# --- Main GUI Setup ---
root = tk.Tk()
root.title("Wordle Helper")

main_frame = ttk.Frame(root, padding="10")
main_frame.grid(row=0, column=0, sticky="nsew")

# --- Main layout frames ---
left_frame = ttk.Frame(main_frame)
left_frame.grid(row=0, column=0, sticky="nsew")

right_frame = ttk.Frame(main_frame)
right_frame.grid(row=0, column=1, sticky="nsew", padx=10)

main_frame.columnconfigure(0, weight=1)
main_frame.columnconfigure(1, weight=1)

# Word Length
tk.Label(left_frame, text="Word Length:").grid(row=0, column=0, sticky=tk.W, pady=2)
word_length_var = tk.StringVar(value="5")
word_length_entry = ttk.Entry(left_frame, width=10, textvariable=word_length_var)
word_length_entry.grid(row=0, column=1, pady=2)

def on_word_length_change(*args):
    try:
        length = int(word_length_var.get())
        if length > 0:
            rebuild_grid(length)
    except ValueError:
        pass # Ignore non-integer input

word_length_var.trace_add("write", on_word_length_change)

# Grid for letter input
tk.Label(left_frame, text="Pattern:").grid(row=1, column=0, sticky=tk.W, pady=2)
grid_frame = ttk.Frame(left_frame)
grid_frame.grid(row=1, column=1, pady=2, sticky=tk.W)
letter_cells = []  # This will hold LetterCell widgets
rebuild_grid(5) # Initial grid

# Letters not in word
tk.Label(left_frame, text="Letters not in word:").grid(row=2, column=0, sticky=tk.W, pady=2)
not_allowed_entry = ttk.Entry(left_frame, width=20)
not_allowed_entry.grid(row=2, column=1, pady=2)

# --- Action Buttons ---
action_frame = ttk.Frame(left_frame)
action_frame.grid(row=3, column=0, columnspan=2, pady=10)

filter_button = ttk.Button(action_frame, text="Filter Words", command=apply_filter)
filter_button.pack(side="left", padx=5)

def reset_all():
    for cell in letter_cells:
        cell.reset()
    not_allowed_entry.delete(0, tk.END)
    status_text.set("")
    if 'best_guesses_tree' in globals():
        for item in best_guesses_tree.get_children():
            best_guesses_tree.delete(item)
    if 'remaining_words_tree' in globals():
        for item in remaining_words_tree.get_children():
            remaining_words_tree.delete(item)

reset_button = ttk.Button(action_frame, text="Reset", command=reset_all)
reset_button.pack(side="left", padx=5)

# Status label
status_text = tk.StringVar()
status_label = ttk.Label(left_frame, textvariable=status_text)
status_label.grid(row=4, column=0, columnspan=2, pady=5)

# Output Treeview for filtered words
output_frame = ttk.LabelFrame(left_frame, text="Filtered Words Preview", padding="5")
output_frame.grid(row=6, column=0, columnspan=2, pady=10, sticky="we")
output_tree = ttk.Treeview(
    output_frame,
    columns=("Word", "Frequency"),
    show="headings",
    height=10
)
output_tree.heading("Word", text="Word")
output_tree.heading("Frequency", text="Frequency")
output_tree.column("Word", width=150)
output_tree.column("Frequency", width=100)
vsb = ttk.Scrollbar(output_frame, orient="vertical", command=output_tree.yview)
output_tree.configure(yscrollcommand=vsb.set)
vsb.pack(side="right", fill="y")
output_tree.pack(side="left", fill="both", expand=True)

# Letter Distribution Treeview
letter_frame = ttk.LabelFrame(left_frame, text="Overall Letter Distribution", padding="5")
letter_frame.grid(row=7, column=0, columnspan=2, pady=10, sticky="we")
letter_tree = ttk.Treeview(
    letter_frame,
    columns=("Letter", "Count"),
    show="headings",
    height=10
)
letter_tree.heading("Letter", text="Letter")
letter_tree.heading("Count", text="Count")
letter_tree.column("Letter", width=50, anchor=tk.CENTER)
letter_tree.column("Count", width=100, anchor=tk.CENTER)
vsb2 = ttk.Scrollbar(letter_frame, orient="vertical", command=letter_tree.yview)
letter_tree.configure(yscrollcommand=vsb2.set)
vsb2.pack(side="right", fill="y")
letter_tree.pack(side="left", fill="both", expand=True)


# --- Best Guesses List ---
best_guesses_frame = ttk.LabelFrame(right_frame, text="Best Guesses", padding="5")
best_guesses_frame.grid(row=0, column=0, pady=10, sticky="nsew")
best_guesses_tree = ttk.Treeview(
    best_guesses_frame,
    columns=("Word", "Score"),
    show="headings",
    height=5
)
best_guesses_tree.heading("Word", text="Word")
best_guesses_tree.heading("Score", text="Score")
best_guesses_tree.column("Word", width=120)
best_guesses_tree.column("Score", width=80, anchor=tk.CENTER)
best_guesses_sb = ttk.Scrollbar(best_guesses_frame, orient="vertical", command=best_guesses_tree.yview)
best_guesses_tree.configure(yscrollcommand=best_guesses_sb.set)
best_guesses_sb.pack(side="right", fill="y")
best_guesses_tree.pack(side="left", fill="both", expand=True)

# --- UI Polish: Color-coding for Best Guesses ---
best_guesses_tree.tag_configure("possible", background="#d5f5d5")  # A light green
best_guesses_tree.tag_configure("probe", background="#e0e0e0")     # A light gray

# --- Words from Unused Letters ---
remaining_words_frame = ttk.LabelFrame(right_frame, text="Words from Remaining Letters", padding="5")
remaining_words_frame.grid(row=1, column=0, pady=10, sticky="nsew")

# Add min frequency input
min_freq_frame = ttk.Frame(remaining_words_frame)
min_freq_frame.pack(fill="x", pady=(0, 5))
ttk.Label(min_freq_frame, text="Minimum Frequency:").pack(side="left", padx=(0, 5))
min_freq_var = tk.StringVar(value="100000")
min_freq_entry = ttk.Entry(min_freq_frame, textvariable=min_freq_var, width=10)
min_freq_entry.pack(side="left")

remaining_words_tree = ttk.Treeview(
    remaining_words_frame,
    columns=("Word", "Score"),
    show="headings",
    height=10
)
remaining_words_tree.heading("Word", text="Word")
remaining_words_tree.heading("Score", text="Score")
remaining_words_tree.column("Word", width=120)
remaining_words_tree.column("Score", width=80, anchor=tk.CENTER)
remaining_words_sb = ttk.Scrollbar(remaining_words_frame, orient="vertical", command=remaining_words_tree.yview)
remaining_words_tree.configure(yscrollcommand=remaining_words_sb.set)
remaining_words_sb.pack(side="right", fill="y")
remaining_words_tree.pack(side="left", fill="both", expand=True)

right_frame.rowconfigure(0, weight=1)
right_frame.rowconfigure(1, weight=2)
right_frame.columnconfigure(0, weight=1)


root.mainloop()