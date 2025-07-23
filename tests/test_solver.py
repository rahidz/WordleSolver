import unittest
import sys
import os

# Add the parent directory to the path so we can import the solver
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from solver import WordleSolver, get_feedback_pattern

class TestWordleSolver(unittest.TestCase):
    
    def setUp(self):
        """Set up a solver instance before each test."""
        # Use a dummy frequency file for testing
        with open("test_freq.txt", "w") as f:
            f.write("apple,100\n")
            f.write("baker,90\n")
            f.write("crane,110\n")
            f.write("drape,80\n")
            f.write("earth,120\n")
            f.write("react,130\n")
            f.write("eerie,70\n")
        
        self.solver = WordleSolver("test_freq.txt")

    def tearDown(self):
        """Clean up the dummy frequency file after each test."""
        os.remove("test_freq.txt")

    def test_score_coverage_with_duplicates(self):
        """Test that _score_coverage correctly handles duplicate letters."""
        # 'e' is the most frequent letter in our test set
        distribution = {'e': 50, 'r': 20, 'a': 15, 't': 10, 'c': 5}
        
        # "eerie" has three 'e's, "react" has one
        score_eerie = self.solver._score_coverage("eerie", distribution)
        score_react = self.solver._score_coverage("react", distribution)
        
        # Expected scores:
        # eerie: 50 (e) + 50 (e) + 20 (r) + 50 (e) = 170
        # react: 20 (r) + 50 (e) + 15 (a) + 5 (c) + 10 (t) = 100
        self.assertEqual(score_eerie, 170)
        self.assertEqual(score_react, 100)
        self.assertGreater(score_eerie, score_react)

    def test_example(self):
        """A placeholder test to ensure the setup is working."""
        self.assertIsNotNone(self.solver)

    def test_get_feedback_pattern(self):
        """Test the feedback pattern generation."""
        self.assertEqual(get_feedback_pattern("crane", "earth"), "BYYBY")
        self.assertEqual(get_feedback_pattern("apple", "apply"), "GGGGB")
        self.assertEqual(get_feedback_pattern("tests", "toast"), "GBYYB")
        self.assertEqual(get_feedback_pattern("hello", "world"), "BBBGY")
        self.assertEqual(get_feedback_pattern("aabbc", "babac"), "YGGYG")
        self.assertEqual(get_feedback_pattern("aaaaa", "bbbbb"), "BBBBB")
        self.assertEqual(get_feedback_pattern("abcde", "abcde"), "GGGGG")
        self.assertEqual(get_feedback_pattern("edcba", "abcde"), "YYGYY")

    def test_parse_misplaced_letters(self):
        """Test the parsing of the misplaced letters string."""
        self.assertEqual(self.solver.parse_misplaced_letters(""), {})
        self.assertEqual(self.solver.parse_misplaced_letters("a:1"), {'a': {0}})
        self.assertEqual(self.solver.parse_misplaced_letters("a:1,3"), {'a': {0, 2}})
        self.assertEqual(self.solver.parse_misplaced_letters("a:1;b:2"), {'a': {0}, 'b': {1}})
        self.assertEqual(self.solver.parse_misplaced_letters(" a : 1 , 3 ; b:2 "), {'a': {0, 2}, 'b': {1}})
        self.assertEqual(self.solver.parse_misplaced_letters("a:1,foo,3"), {'a': {0, 2}})
        self.assertEqual(self.solver.parse_misplaced_letters("a:1;a:3"), {'a': {0, 2}})

    def test_filter_words(self):
        """Test the main word filtering logic."""
        # Pattern filtering
        results = self.solver.filter_words(5, "c____", "", "")
        self.assertEqual([r[0] for r in results], ["crane"])

        # Not allowed filtering
        results = self.solver.filter_words(5, "_____", "c", "")
        self.assertEqual([r[0] for r in results], ["earth", "apple", "baker", "drape", "eerie"])

        # Misplaced filtering
        results = self.solver.filter_words(5, "_____", "", "a:2")
        self.assertEqual([r[0] for r in results], ["react", "crane", "apple", "drape"])
        
        # Combined filtering
        results = self.solver.filter_words(5, "_r___", "d", "a:1")
        self.assertEqual([r[0] for r in results], ["crane"])


if __name__ == '__main__':
    unittest.main()