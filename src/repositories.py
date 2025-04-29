import os
import time
from typing import Optional, Tuple

class StorageRepository:
    def __init__(self, filepath: str, mode: str = 'naive'):
        self.filepath = filepath
        self.mode = mode
        self.data = self.load_file()
        if self.data is None:
            raise ValueError(f"Failed to load file: {filepath}")
        self.prepare_data()
        
    def load_file(self) -> Optional[list]:
        if not os.path.exists(self.filepath):
            print(f"File {self.filepath} does not exist.")
            return None
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                return content.splitlines()  # assuming file contains one word per line
        except Exception as e:
            print(f"Error loading file: {e}")
            return None

    def prepare_data(self):
        mode_prep = {
            'set': lambda: set(self.data),
            'dict': lambda: {word: True for word in self.data},
            'index_map': lambda: {i: word for i, word in enumerate(self.data)},
            'binary': lambda: sorted(self.data),
            'trie': lambda: self.build_trie(self.data),
            'naive': lambda: self.data
        }
        self.search_data = mode_prep.get(self.mode, mode_prep['naive'])()

    def build_trie(self, words):
        trie = {}
        for word in words:
            node = trie
            for char in word:
                node = node.setdefault(char, {})
            node['#'] = True
        return trie

    def search(self, target) -> Tuple[bool, float]:
        """Search for the target and return (result, elapsed_time_in_seconds)."""
        search_method = getattr(self, f"{self.mode}_search", self.naive_search)
        start_time = time.perf_counter()
        result = search_method(target)
        end_time = time.perf_counter()
        elapsed_time = end_time - start_time
        return result, elapsed_time

    def naive_search(self, target):
        return target in self.search_data

    def set_search(self, target):
        return target in self.search_data

    def dict_search(self, target):
        return target in self.search_data

    def index_map_search(self, target):
        return target in self.search_data.values()

    def binary_search(self, target):
        data, low, high = self.search_data, 0, len(self.search_data) - 1
        while low <= high:
            mid = (low + high) // 2
            if data[mid] == target:
                return True
            low, high = (mid + 1, high) if data[mid] < target else (low, mid - 1)
        return False

    def trie_search(self, target):
        node = self.search_data
        for char in target:
            if char not in node:
                return False
            node = node[char]
        return '#' in node
