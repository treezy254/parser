import time
from typing import Any, List, Optional


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
        return query in text

    def hash_set_search(self, text: str, query: str) -> bool:
        return query in set(text.split())

    def binary_search(self, sorted_text: List[str], query: str) -> bool:
        left, right = 0, len(sorted_text) - 1
        while left <= right:
            mid = (left + right) // 2
            if sorted_text[mid] == query:
                return True
            elif sorted_text[mid] < query:
                left = mid + 1
            else:
                right = mid - 1
        return False

    def trie_search(self, text: str, query: str) -> bool:
        # Placeholder: could implement full trie structure
        return query in text

    def boyer_moore_search(self, text: str, pattern: str) -> bool:
        return text.find(pattern) != -1

    def rabin_karp_search(self, text: str, pattern: str) -> bool:
        d = 256
        q = 101
        m = len(pattern)
        n = len(text)
        p = 0
        t = 0
        h = 1

        for i in range(m - 1):
            h = (h * d) % q

        for i in range(m):
            p = (d * p + ord(pattern[i])) % q
            t = (d * t + ord(text[i])) % q

        for i in range(n - m + 1):
            if p == t:
                if text[i:i + m] == pattern:
                    return True
            if i < n - m:
                t = (d * (t - ord(text[i]) * h) + ord(text[i + m])) % q
                if t < 0:
                    t += q
        return False

    def aho_corasick_search(self, text: str, pattern: str) -> bool:
        # Simplified version
        return pattern in text

    # --- Dispatcher ---

    def execute_algorithm(self, algo_name: str, text: str, query: str) -> bool:
        algo_name = algo_name.lower()
        if algo_name == "linear search":
            return self.linear_search(text, query)
        elif algo_name == "hash set search":
            return self.hash_set_search(text, query)
        elif algo_name == "binary search":
            sorted_text = sorted(text.split())
            return self.binary_search(sorted_text, query)
        elif algo_name == "trie search":
            return self.trie_search(text, query)
        elif algo_name in ["bayer moore", "boyer moore"]:
            return self.boyer_moore_search(text, query)
        elif algo_name == "rabin karp":
            return self.rabin_karp_search(text, query)
        elif algo_name == "aho corasick":
            return self.aho_corasick_search(text, query)
        else:
            raise ValueError("Unknown algorithm")

    def search_in_file(self, filepath: str, algo_name: str, query: str) -> (bool, float): # type: ignore
        text = self.load_file(filepath)
        if text is None:
            return False, 0.0
        start_time = time.time()
        found = self.execute_algorithm(algo_name, text, query)
        end_time = time.time()
        return found, end_time - start_time
