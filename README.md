# Wordle Solver

This is a powerful and flexible solver for Wordle and similar word puzzles. It provides a graphical user interface (GUI) to help you find the correct word based on the clues you've gathered.

## Features

*   **Graphical User Interface**: An intuitive interface built with `tkinter` for easy input of puzzle clues.
*   **Variable Word Length**: Solves puzzles with any word length, not just the standard 5-letter Wordle.
*   **Advanced Filtering**: Filters a comprehensive word list based on:
    *   **Green letters**: Correct letters in the correct position.
    *   **Yellow letters**: Correct letters in the wrong position.
    *   **Gray letters**: Letters not in the word.
*   **Frequency-Based Sorting**: Displays potential answers sorted by word frequency, showing the most common words first.
*   **Letter Distribution Analysis**: Shows the frequency of letters within the remaining possible words to help you make strategic guesses.
*   **Optimal Guess Suggestions**: Recommends words to use for your next guess, including words made from letters you haven't tried yet.
*   **Responsive UI**: Performs the heavy lifting of word filtering in a separate thread to ensure the user interface remains responsive.
*   **Saves Results**: Writes the list of filtered words to `sorted_filtered_words.txt` for your reference.

## How to Use

1.  **Run the Application**:
    Execute the `gui.py` script from your terminal:
    ```bash
    python gui.py
    ```

2.  **Set Word Length**:
    Enter the length of the word in the "Word Length" box. The grid will automatically adjust.

3.  **Enter Your Guesses**:
    *   Type the letters of your guess into the grid.
    *   Click on each letter's cell to cycle through the clue colors:
        *   **Green**: The letter is correct and in the right position.
        *   **Yellow**: The letter is in the word but in the wrong position.
        *   **Default (White/Gray)**: The letter is not in the word (a "gray" letter). You can also add these letters to the "Letters not in word" field.

4.  **Filter Words**:
    Click the **"Filter Words"** button. The application will process the clues and display the results.

5.  **Analyze the Results**:
    *   **Filtered Words Preview**: Shows all possible words that fit your clues, sorted by how common they are.
    *   **Overall Letter Distribution**: Displays the frequency of each letter in the list of possible words, helping you choose letters for your next guess.
    *   **Best Guesses / Words from Remaining Letters**: Provides suggestions for what to guess next. (Best Guesses is not implemented yet)

6.  **Reset**:
    Click the **"Reset"** button to clear all inputs and start a new puzzle.

## Project Files

*   [`gui.py`](d:/Wordle/WordleSolver/gui.py:1): The main application file that runs the `tkinter` GUI.
*   [`filters.py`](d:/Wordle/WordleSolver/filters.py:1): Contains the core logic for loading the word list and filtering it based on user-provided clues.
*   [`frequency.txt`](d:/Wordle/WordleSolver/frequency.txt): A text file containing a list of words and their corresponding frequencies. This is the dictionary the solver uses.
*   [`sorted_filtered_words.txt`](d:/Wordle/WordleSolver/sorted_filtered_words.txt): An output file where the results of the last filtering operation are saved.

## Dependencies

*   Python 3.x
*   `tkinter` (usually included with standard Python installations)