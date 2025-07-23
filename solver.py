import os
import math
from collections import Counter

class WordleSolver:
    """
    Encapsulates the logic for loading, filtering, and suggesting words for a Wordle-like game.
    """
    def __init__(self, word_list_path="frequency.txt"):
        """
        Initializes the solver by loading and pre-processing the word list.
        """
        self.word_data_list = self._load_word_list(word_list_path)

    # --- Private Helper Methods ---
    def _get_char_mask(self, char):
        """Returns a 26-bit integer mask for a single character."""
        return 1 << (ord(char) - ord('a'))

    def _get_word_mask(self, word):
        """Computes a bitmask representing the set of unique letters in a word."""
        mask = 0
        for char in word.lower():
            mask |= 1 << (ord(char) - ord('a'))
        return mask

    def _load_word_list(self, filename):
        """
        Loads word data from the given file once and returns the list.
        Each entry is a dictionary containing the word, its frequency, and a pre-computed bitmask.
        """
        data = []
        filepath = os.path.join(os.path.dirname(__file__), filename)
        with open(filepath, encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(",")
                if len(parts) != 2:
                    continue
                word, freq_str = parts[0].strip(), parts[1].strip()
                try:
                    frequency = int(freq_str)
                except ValueError:
                    continue
                
                data.append({
                    "word": word,
                    "freq": frequency,
                    "mask": self._get_word_mask(word),
                })
        return data

    def parse_misplaced_letters(self, s):
        """
        Parses the misplaced letters input.
        Example input: "a:1,3; e:2"
        Returns a dictionary mapping each letter to a set of 0-indexed positions
        where it must NOT appear, but must appear somewhere else.
        """
        misplaced = {}
        if not s.strip():
            return misplaced

        entries = s.split(";")
        for entry in entries:
            if ":" in entry:
                letter_part, pos_part = entry.split(":")
                letter = letter_part.strip().lower()
                # Collect positions (convert from 1-based to 0-based)
                positions = {
                    int(p.strip()) - 1
                    for p in pos_part.split(",")
                    if p.strip().isdigit()
                }
                if letter in misplaced:
                    misplaced[letter].update(positions)
                else:
                    misplaced[letter] = positions

        return misplaced

    def _filter_word_with_mask(self, word_data, word_length, pattern, not_allowed_mask, misplaced_dict):
        """
        Returns True if the word from `word_data` satisfies all constraints.
        Uses pre-computed bitmasks for faster filtering.
        """
        word = word_data["word"]
        word_mask = word_data["mask"]

        # 1) Length check
        if word_length is not None and len(word) != word_length:
            return False

        # 2) Excluded letters (fast check)
        if word_mask & not_allowed_mask:
            return False

        # 3) Pattern check
        lower = word.lower()
        for i, p_char in enumerate(pattern):
            if p_char != "_" and lower[i] != p_char.lower():
                return False

        # 4) Misplaced letters check
        for letter, bad_positions in misplaced_dict.items():
            # Check if letter is present in the word (fast)
            if not (word_mask & self._get_char_mask(letter)):
                return False
            # Check if it's in a bad spot (slower)
            for pos in bad_positions:
                if 0 <= pos < len(lower) and lower[pos] == letter:
                    return False

        return True

    def filter_words(self, word_length, pattern, not_allowed, misplaced_input):
        """
        Returns a list of (word, frequency) tuples matching the given constraints.
        """
        # 1) Pre-compute masks for constraints
        not_allowed_mask = self._get_word_mask(not_allowed)
        misplaced_dict = self.parse_misplaced_letters(misplaced_input)

        # 2) Filter entirely in memory
        results_data = [
            wd
            for wd in self.word_data_list
            if self._filter_word_with_mask(wd, word_length, pattern, not_allowed_mask, misplaced_dict)
        ]

        # Convert back to (word, frequency) tuples
        results = [(d["word"], d["freq"]) for d in results_data]

        # 3) Sort by descending frequency
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def compute_letter_distributions(self, results):
        """
        Given `results` as a list of (word, frequency),
        returns two dicts:
          - overall: letter -> total weighted count across all words
          - positional: pos -> { letter -> weighted count at that position }
        """
        overall = {}
        positional = {}

        if not results:
            return overall, positional

        # assume all words same length
        length = len(results[0][0])
        for pos in range(length):
            positional[pos] = {}

        for word, freq in results:
            lw = word.lower()
            for i, ch in enumerate(lw):
                overall[ch] = overall.get(ch, 0) + freq
                positional[i][ch] = positional[i].get(ch, 0) + freq

        return overall, positional

    def find_words_from_remaining_letters(self, used_letters, not_allowed_letters, overall_distribution, word_length=None, min_frequency=0):
        """
        Finds words that can be formed from the set of remaining (unused) letters.
        """
        available_letters = set("abcdefghijklmnopqrstuvwxyz") - used_letters - not_allowed_letters
        available_mask = self._get_word_mask("".join(available_letters))
        
        valid_words = []
        for word_data in self.word_data_list:
            word = word_data["word"]
            frequency = word_data["freq"]
            word_mask = word_data["mask"]
            
            if word_length is not None and len(word) != word_length:
                continue

            if frequency < min_frequency:
                continue
            
            if (word_mask & available_mask) == word_mask:
                score = sum(overall_distribution.get(letter, 0) for letter in set(word))
                valid_words.append((word, score))
                
        valid_words.sort(key=lambda x: x[1], reverse=True)
        return valid_words

    def _score_coverage(self, word, overall_distribution):
        """Sum of letter frequencies, counting each letter once."""
        return sum(overall_distribution.get(ch, 0)
                   for ch in set(word.lower()))

    def _score_weighted_entropy(self, guess, possible_words):
        """Entropy where each answer is weighted by its frequency."""
        total_mass = sum(freq for _, freq in possible_words)
        if not total_mass:
            return 0.0
            
        pattern_cnt = Counter()

        for answer, freq in possible_words:
            pat = get_feedback_pattern(guess, answer)
            pattern_cnt[pat] += freq

        ent = 0.0
        for mass in pattern_cnt.values():
            p = mass / total_mass
            ent -= p * math.log2(p)
        return ent

    def best_guesses(self, possible_words, overall_distribution, cutoff=250, top_n=15):
        """
        Chooses a scoring strategy and returns the top N best guesses.
        """
        if not possible_words:
            return []

        word_length = len(possible_words[0][0])
        possible_words_only = [w for w, _ in possible_words]

        if cutoff is None or len(possible_words) <= cutoff:
            scorer = lambda w: self._score_weighted_entropy(w, possible_words)
            pool = possible_words_only
        else:
            scorer = lambda w: self._score_coverage(w, overall_distribution)
            pool = [d['word'] for d in self.word_data_list if len(d['word']) == word_length]

        scores = [(w, scorer(w)) for w in pool]
        scores.sort(key=lambda x: x[1], reverse=True)
        
        return scores[:top_n]

# Keep top-level functions that are pure helpers and don't depend on solver state
def get_feedback_pattern(guess, answer):
    """
    Returns a 5-char string such as 'GYBBY' (G=green, Y=yellow, B=gray).
    Handles duplicate letters correctly.
    """
    g = guess.lower()
    a = answer.lower()
    pattern = ['B'] * len(g)
    
    answer_counts = Counter(a)

    # Pass 1: Find green letters
    for i, ch in enumerate(g):
        if ch == a[i]:
            pattern[i] = 'G'
            answer_counts[ch] -= 1

    # Pass 2: Find yellow letters
    for i, ch in enumerate(g):
        if pattern[i] == 'B' and answer_counts.get(ch, 0) > 0:
            pattern[i] = 'Y'
            answer_counts[ch] -= 1
            
    return "".join(pattern)