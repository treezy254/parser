import time
from typing import Any, List, Optional, Dict, Set


class SearchService:

    def load_file(self, filepath: str) -> Optional[str]:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error loading file: {e}")
            return None

    # --- Algorithms Implementation ---

    def linear_search(self, text: str, query: str) -> bool:
        """Simple linear search using Python's built-in 'in' operator."""
        return query in text

    def hash_set_search(self, text: str, query: str) -> bool:
        """Search using a hash set of words for efficient lookups."""
        # Pre-split words and create set only once if this is used repeatedly
        words_set = set(text.split())
        return query in words_set

    def binary_search(self, text: str, query: str) -> bool:
        """Binary search on sorted words."""
        sorted_words = sorted(text.split())
        left, right = 0, len(sorted_words) - 1
        
        while left <= right:
            mid = left + (right - left) // 2  # Avoid potential overflow
            if sorted_words[mid] == query:
                return True
            elif sorted_words[mid] < query:
                left = mid + 1
            else:
                right = mid - 1
        return False

    def build_trie(self, words: List[str]) -> Dict:
        """Build a trie data structure for fast string searches."""
        root = {}
        for word in words:
            current = root
            for char in word:
                if char not in current:
                    current[char] = {}
                current = current[char]
            current['#'] = True  # Mark end of word
        return root

    def search_trie(self, trie: Dict, query: str) -> bool:
        """Search for a word in the trie."""
        current = trie
        for char in query:
            if char not in current:
                return False
            current = current[char]
        return '#' in current

    def trie_search(self, text: str, query: str) -> bool:
        """Search using a trie data structure."""
        words = text.split()
        trie = self.build_trie(words)
        return self.search_trie(trie, query)

    def build_bad_char_table(self, pattern: str) -> Dict[str, int]:
        """Build bad character table for Boyer-Moore algorithm."""
        m = len(pattern)
        # Initialize with the pattern length for characters not in pattern
        bad_char = {c: m for c in set(pattern)}
        
        # For each character in pattern, store the last occurrence position
        for i in range(m-1):
            bad_char[pattern[i]] = m - 1 - i
            
        return bad_char

    def boyer_moore_search(self, text: str, pattern: str) -> bool:
        """Boyer-Moore string search algorithm."""
        n, m = len(text), len(pattern)
        
        if m == 0:
            return True
        if n < m:
            return False

        # Preprocess pattern
        bad_char = self.build_bad_char_table(pattern)
        
        # Search
        i = m - 1  # Start from the end of pattern
        while i < n:
            j = m - 1
            k = i
            
            # Compare characters from right to left
            while j >= 0 and text[k] == pattern[j]:
                j -= 1
                k -= 1
            
            if j == -1:  # Pattern found
                return True
                
            # Shift based on bad character rule
            char_shift = bad_char.get(text[i], m)
            i += char_shift
                
        return False

    def rabin_karp_search(self, text: str, pattern: str) -> bool:
        """Rabin-Karp string search using rolling hash."""
        if not pattern:
            return True
            
        n, m = len(text), len(pattern)
        if m > n:
            return False
            
        # Use a smaller prime for better performance
        q = 101  # Prime number
        d = 256  # Number of characters in input alphabet
        
        # Calculate hash values for pattern and first window of text
        pattern_hash = 0
        text_hash = 0
        h = pow(d, m-1) % q
        
        for i in range(m):
            pattern_hash = (d * pattern_hash + ord(pattern[i])) % q
            text_hash = (d * text_hash + ord(text[i])) % q
        
        # Slide the pattern over text one by one
        for i in range(n - m + 1):
            # Check if hash values match
            if pattern_hash == text_hash:
                # Verify character by character
                match = True
                for j in range(m):
                    if text[i+j] != pattern[j]:
                        match = False
                        break
                if match:
                    return True
            
            # Calculate hash for next window
            if i < n - m:
                text_hash = (d * (text_hash - ord(text[i]) * h) + ord(text[i+m])) % q
                # Make sure we have a positive hash value
                if text_hash < 0:
                    text_hash += q
                    
        return False

    class AhoCorasickNode:
        def __init__(self):
            self.goto = {}  # Character transitions
            self.out = set()  # Set of matched patterns
            self.fail = None  # Failure function

    def build_aho_corasick(self, patterns: List[str]):
        """Build Aho-Corasick automaton."""
        root = self.AhoCorasickNode()
        
        # Build trie
        for i, pattern in enumerate(patterns):
            node = root
            for char in pattern:
                if char not in node.goto:
                    node.goto[char] = self.AhoCorasickNode()
                node = node.goto[char]
            node.out.add(i)
        
        # Build failure function using BFS
        queue = []
        for char, child in root.goto.items():
            queue.append(child)
            child.fail = root
            
        while queue:
            node = queue.pop(0)
            for char, child in node.goto.items():
                queue.append(child)
                failure = node.fail
                
                while failure and char not in failure.goto:
                    failure = failure.fail
                    
                child.fail = failure.goto[char] if failure and char in failure.goto else root
                child.out.update(child.fail.out)
                
        return root

    def aho_corasick_search(self, text: str, pattern: str) -> bool:
        """Aho-Corasick algorithm for multiple pattern search."""
        if not pattern:
            return True
            
        # For single pattern search, build automaton with just the pattern
        automaton = self.build_aho_corasick([pattern])
        node = automaton
        
        for char in text:
            while node and char not in node.goto:
                node = node.fail
                
            if not node:
                node = automaton
                continue
                
            node = node.goto[char]
            
            if node.out:  # Found a match
                return True
                
        return False

    # --- Dispatcher ---

    def execute_algorithm(self, algo_name: str, text: str, query: str) -> bool:
        algo_name = algo_name.lower()
        if algo_name == "linear search":
            return self.linear_search(text, query)
        elif algo_name == "hash set search":
            return self.hash_set_search(text, query)
        elif algo_name == "binary search":
            return self.binary_search(text, query)
        elif algo_name == "trie search":
            return self.trie_search(text, query)
        elif algo_name in ["bayer moore", "boyer moore"]:
            return self.boyer_moore_search(text, query)
        elif algo_name == "rabin karp":
            return self.rabin_karp_search(text, query)
        elif algo_name == "aho corasick":
            return self.aho_corasick_search(text, query)
        else:
            raise ValueError(f"Unknown algorithm: {algo_name}")

    def search_in_file(self, filepath: str, algo_name: str, query: str) -> tuple[bool, float]:
        text = self.load_file(filepath)
        if text is None:
            return False, 0.0
        start_time = time.time()
        found = self.execute_algorithm(algo_name, text, query)
        end_time = time.time()
        return found, (end_time - start_time) * 1000  # Return time in milliseconds

