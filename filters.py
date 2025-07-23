import os

import math
from collections import Counter


# --- Bitmasking Helpers ---
def get_char_mask(char):
    """Returns a 26-bit integer mask for a single character."""
    # Assumes char is 'a'-'z'
    return 1 << (ord(char) - ord('a'))

def get_word_mask(word):
    """Computes a bitmask representing the set of unique letters in a word."""
    mask = 0
    for char in word.lower():
        mask |= 1 << (ord(char) - ord('a'))
    return mask
def parse_misplaced_letters(s):
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


def filter_word_with_mask(word_data, word_length, pattern, not_allowed_mask, misplaced_dict):
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
        if not (word_mask & get_char_mask(letter)):
            return False
        # Check if it's in a bad spot (slower)
        for pos in bad_positions:
            if 0 <= pos < len(lower) and lower[pos] == letter:
                return False

    return True


def compute_letter_distributions(results):
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


# ——————————————————————————————————————————————————————
# Pre-load dictionary into memory on first use
_WORD_DATA = None

def _load_word_list(filename="frequency.txt"):
    """
    Loads word data from the given file once, caches it, and returns the list.
    Each entry will be a dictionary containing the word, its frequency,
    and pre-computed bitmasks for efficient filtering.
    """
    global _WORD_DATA
    if _WORD_DATA is None:
        _WORD_DATA = []
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
                
                # Pre-compute and store bitmasks
                _WORD_DATA.append({
                    "word": word,
                    "freq": frequency,
                    "mask": get_word_mask(word),
                })
    return _WORD_DATA


def filter_words(file_path, word_length, pattern, not_allowed, misplaced_input):
    """
    Returns a list of (word, frequency) tuples matching the given constraints.
    The word list is loaded from disk only once and then cached in memory.
    
    Args:
      file_path      : Filename (e.g. 'frequency.txt') in this module’s folder.
      word_length    : Desired word length (int) or None.
      pattern        : String of length N with '_' for unknowns and letters for known spots.
      not_allowed    : String of letters that must NOT appear.
      misplaced_input: String like 'a:1,3; e:2' for letters in the word but not those positions.
    
    Returns:
      List of (word, frequency), sorted by frequency descending.
    """
    # 1) Load or retrieve the cached word data with masks
    word_data_list = _load_word_list(file_path)

    # 2) Pre-compute masks for constraints
    not_allowed_mask = get_word_mask(not_allowed)
    misplaced_dict = parse_misplaced_letters(misplaced_input)

    # 3) Filter entirely in memory
    results_data = [
        wd
        for wd in word_data_list
        if filter_word_with_mask(wd, word_length, pattern, not_allowed_mask, misplaced_dict)
    ]

    # Convert back to (word, frequency) tuples for compatibility
    results = [(d["word"], d["freq"]) for d in results_data]

    # 4) Sort by descending frequency
    results.sort(key=lambda x: x[1], reverse=True)
    return results
def find_words_from_remaining_letters(word_list, used_letters, not_allowed_letters, overall_distribution, word_length=None, min_frequency=0):
    """
    Finds words that can be formed from the set of remaining (unused) letters.

    Args:
      word_list: The full list of word data dictionaries.
      used_letters: A set of letters that have been used (green or yellow).
      not_allowed_letters: A set of letters known to not be in the word.
      overall_distribution: A dict mapping letters to their frequency count.
      word_length: The length of words to find.
      min_frequency: The minimum frequency a word must have to be included.

    Returns:
      A list of (word, score) tuples for words that can be formed.
    """
    # Letters to build words from are ones not used (green/yellow) and not disallowed (gray)
    available_letters = set("abcdefghijklmnopqrstuvwxyz") - used_letters - not_allowed_letters
    available_mask = get_word_mask("".join(available_letters))
    
    valid_words = []
    for word_data in word_list:
        word = word_data["word"]
        frequency = word_data["freq"]
        word_mask = word_data["mask"]
        
        # The word must have the correct length
        if word_length is not None and len(word) != word_length:
            continue

        # Check against minimum frequency
        if frequency < min_frequency:
            continue
        
        # All letters in the word must be from the available set (subset check)
        if (word_mask & available_mask) == word_mask:
            # Calculate the score based on the sum of letter counts for unique letters
            score = sum(overall_distribution.get(letter, 0) for letter in set(word))
            valid_words.append((word, score))
            
    valid_words.sort(key=lambda x: x[1], reverse=True)
    return valid_words


# ------------------------------------------------------------------
# Best Guess Scorer
# ------------------------------------------------------------------

def score_coverage(word, overall_distribution):
    """Sum of letter frequencies, counting each letter once."""
    return sum(overall_distribution.get(ch, 0)
               for ch in set(word.lower()))

def get_feedback_pattern(guess, answer):
    """
    Returns a 5-char string such as 'GYBBY'
    (G=green, Y=yellow, B=gray).
    Handles duplicate letters correctly.
    """
    g = guess.lower()
    a = answer.lower()
    pattern = ['B'] * len(g)
    
    # Use a counter to handle duplicate letters in the answer
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

def score_entropy(guess, possible_words):
    """
    Expected information gain (bits) of `guess`
    given the current `possible_words` list.

    Complexity: O(len(possible_words)^2) naively,
    so call only when the pool is reasonably small.
    """
    pattern_counts = Counter()

    for answer in possible_words:
        pattern = get_feedback_pattern(guess, answer)
        pattern_counts[pattern] += 1

    total = len(possible_words)
    if not total:
        return 0.0

    ent = 0.0
    for c in pattern_counts.values():
        p = c / total
        ent -= p * math.log2(p)
    return ent

def score_weighted_entropy(guess, possible_words):
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

def best_guesses(
    possible_words, word_list, overall_distribution, cutoff=250, top_n=15, probe_limit=2000
):
    """
    Chooses a scoring strategy and returns the top N best guesses.
    """
    if not possible_words:
        return []  # No possible answers means no guesses to suggest.

    word_length = len(possible_words[0][0])
    possible_words_only = [w for w, _ in possible_words]

    # Decide on the scoring function and the pool of candidates to test.
    if cutoff is None or len(possible_words) <= cutoff:
        # For smaller possibility lists, use the more accurate weighted entropy score.
        scorer = lambda w: score_weighted_entropy(w, possible_words)
        
        # The best guess is one of the possible words. Probes are not used.
        pool = possible_words_only

    else:
        # For larger lists, coverage scoring is a faster heuristic.
        scorer = lambda w: score_coverage(w, overall_distribution)
        
        # At this stage, any word of the correct length is a candidate.
        pool = [d['word'] for d in word_list if len(d['word']) == word_length]

    # Score all words in the chosen pool. This can be slow for the coverage
    # case, but it's run in a background thread in the GUI.
    scores = [(w, scorer(w)) for w in pool]
    scores.sort(key=lambda x: x[1], reverse=True)
    
    return scores[:top_n]
