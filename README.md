# Wordle Solver

This is a powerful and flexible solver for Wordle and similar word puzzles. It provides a graphical user interface (GUI) to help you find the correct word based on the clues you've gathered, with advanced features for suggesting the most strategic next moves.

## Features

*   **Graphical User Interface**: An intuitive interface built with `tkinter` for easy input of puzzle clues.
*   **Variable Word Length**: Solves puzzles with any word length, not just the standard 5-letter Wordle.
*   **Advanced Filtering**: Filters a comprehensive word list using bitmasking for high performance, based on:
    *   **Green letters**: Correct letters in the correct position.
    *   **Yellow letters**: Correct letters in the wrong position.
    *   **Gray letters**: Letters not in the word.
*   **Frequency-Based Sorting**: Displays potential answers sorted by word frequency, showing the most common words first.
*   **Letter Distribution Analysis**: Shows the frequency of letters within the remaining possible words to help you make strategic guesses.
*   **Optimal Guess Suggestions**: Recommends the best words for your next guess using one of two strategies:
    *   **Weighted Entropy**: For smaller lists of possible answers, this calculates the information gain of each guess to narrow down the options most effectively.
    *   **Coverage Score**: For larger lists, this faster heuristic suggests words that cover the most frequent letters among the remaining possibilities.
*   **Strategic Probes**: Suggests "probe" words made from letters you haven't tried yet to gather maximum information.
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
        *   **White/Gray (Default)**: The letter is not in the word (a "gray" letter). You can also add these letters to the "Letters not in word" field.
        *   **Yellow**: The letter is in the word but in the wrong position.
        *   **Green**: The letter is correct and in the right position.

4.  **Filter Words**:
    Click the **"Filter Words"** button. The application will process the clues and display the results.

5.  **Analyze the Results**:
    *   **Filtered Words Preview**: Shows all possible words that fit your clues, sorted by how common they are.
    *   **Overall Letter Distribution**: Displays the frequency of each letter in the list of possible words.
    *   **Best Guesses**: Provides suggestions for your next guess, color-coded to distinguish between possible answers (light green) and strategic probes (light gray).
    *   **Words from Remaining Letters**: Shows words made from letters you haven't used yet, which can be useful for breaking a deadlock.

6.  **Reset**:
    Click the **"Reset"** button to clear all inputs and start a new puzzle.

## Project Files

*   [`gui.py`](d:/Wordle/WordleSolver/gui.py:1): The main application file that defines the `WordleUI` class and runs the `tkinter` GUI.
*   [`solver.py`](d:/Wordle/WordleSolver/solver.py:1): Defines the `WordleSolver` class, which encapsulates the core logic for loading the word list, filtering words, and scoring guesses.
*   [`frequency.txt`](d:/Wordle/WordleSolver/frequency.txt): The dictionary file, containing a list of words and their corresponding frequencies. This file is required for the solver to work.
*   [`sorted_filtered_words.txt`](d:/Wordle/WordleSolver/sorted_filtered_words.txt): An output file where the results of the last filtering operation are saved.

## Technical Implementation

*   **UI Framework**: The graphical interface is built with Python's standard `tkinter` library.
*   **Concurrency**: Filtering operations are run in a separate thread using `concurrent.futures.ThreadPoolExecutor` to prevent the UI from freezing during intensive calculations.
*   **Performance**: The solver uses bitmasking to perform high-speed filtering of the word list. Each word and the set of excluded letters are represented as bitmasks, allowing for rapid checks using bitwise operations.
*   **Guess Scoring**: The "Best Guesses" are determined by one of two algorithms, depending on the number of possible words remaining:
    *   `score_weighted_entropy`: Calculates the expected information gain for each potential guess, weighted by word frequency. This is computationally intensive and used when the list of possibilities is small.
    *   `score_coverage`: A faster heuristic that scores guesses based on the frequency of their letters in the remaining word list. This is used for larger possibility sets.

## Requirements

*   Python 3.x
*   `tkinter` (usually included with standard Python installations)