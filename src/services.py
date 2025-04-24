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


class StringSearcher:
    def __init__(self, data):
        self.data = data
        self.data_set = set(data)
        self.data_dict = {word: True for word in data}  # for dict-based search
        self.index_map = {i: word for i, word in enumerate(data)}  # index map
        self.trie = self.build_trie(data)  # for trie-based search

    # Naive search
    def search_naive(self, target):
        for word in self.data:
            if word == target:
                return True
        return False

    # Set-based search
    def search_with_set(self, target):
        return target in self.data_set

    # Dict-based search
    def search_with_dict(self, target):
        return target in self.data_dict

    # Index map-based search
    def search_with_index_map(self, target):
        return target in self.index_map.values()

    # Binary Search (requires sorted data)
    def search_with_binary(self, target):
        sorted_data = sorted(self.data)  # sorting the data
        low, high = 0, len(sorted_data) - 1
        while low <= high:
            mid = (low + high) // 2
            if sorted_data[mid] == target:
                return True
            elif sorted_data[mid] < target:
                low = mid + 1
            else:
                high = mid - 1
        return False

    # Trie Search (For prefix-based search)
    def build_trie(self, words):
        trie = {}
        for word in words:
            node = trie
            for char in word:
                if char not in node:
                    node[char] = {}
                node = node[char]
            node['#'] = word  # end of the word marker
        return trie

    def search_with_trie(self, target):
        node = self.trie
        for char in target:
            if char not in node:
                return False
            node = node[char]
        return '# ' in node  # Check if it's an actual word and not just a prefix

# Example usage:
data = ["apple", "banana", "grape", "orange", "mango"]
searcher = StringSearcher(data)

target = "banana"
print("Naive:", searcher.search_naive(target))
print("Set:", searcher.search_with_set(target))
print("Dict:", searcher.search_with_dict(target))
print("Index Map:", searcher.search_with_index_map(target))
print("Binary:", searcher.search_with_binary(target))
print("Trie:", searcher.search_with_trie(target))
