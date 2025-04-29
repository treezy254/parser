import os
import time
import json
import threading
import logging
from typing import List, Optional, Tuple, Dict, Callable
from models import Log

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LogRepository:
    """Handles persistence of Log objects to a JSON file."""
    
    def __init__(self, filepath: str = 'logs.json') -> None:
        self.filepath = filepath
        self._lock = threading.Lock()
        self._ensure_file()

    def _ensure_file(self) -> None:
        """Ensures that the log file exists."""
        if not os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'w') as f:
                    json.dump([], f)
            except Exception as e:
                logger.exception("Failed to create log file: %s", e)

    def create_log(self, log: Log) -> None:
        """Appends a new log entry to the file."""
        with self._lock:
            try:
                logs = self.read_logs()
                logs.append(log.__dict__)
                with open(self.filepath, 'w') as f:
                    json.dump(logs, f, default=str, indent=4)
            except Exception as e:
                logger.exception("Failed to create log: %s", e)

    def read_logs(self) -> List[Dict]:
        """Reads all logs from the file."""
        try:
            with open(self.filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.exception("Failed to read logs: %s", e)
            return []

    def update_log(self, log_id: str, updates: Dict) -> bool:
        """Updates a log entry by ID."""
        with self._lock:
            try:
                logs = self.read_logs()
                for log in logs:
                    if log['id'] == log_id:
                        log.update(updates)
                        with open(self.filepath, 'w') as f:
                            json.dump(logs, f, default=str, indent=4)
                        return True
                return False
            except Exception as e:
                logger.exception("Failed to update log: %s", e)
                return False

    def delete_log(self, log_id: str) -> bool:
        """Deletes a log entry by ID."""
        with self._lock:
            try:
                logs = self.read_logs()
                updated_logs = [log for log in logs if log['id'] != log_id]
                if len(updated_logs) < len(logs):
                    with open(self.filepath, 'w') as f:
                        json.dump(updated_logs, f, default=str, indent=4)
                    return True
                return False
            except Exception as e:
                logger.exception("Failed to delete log: %s", e)
                return False

class StorageRepository:
    """Handles data loading and search operations with multiple search strategies."""
    
    def __init__(self) -> None:
        self.data: Optional[List[str]] = None
        self.search_data: Optional[object] = None
        self.mode: str = 'naive'

    def load_file(self, filepath: str) -> bool:
        """Loads data from a file."""
        if not os.path.exists(filepath):
            logger.warning("File %s does not exist.", filepath)
            return False
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.data = f.read().splitlines()
            logger.info("Loaded %d lines from %s", len(self.data), filepath)
            return True
        except Exception as e:
            logger.exception("Error loading file: %s", e)
            return False

    def prepare(self, mode: str = 'naive') -> None:
        """Prepares the data for a given search mode."""
        if self.data is None:
            raise ValueError("No data loaded. Call load_file() first.")
        
        self.mode = mode
        mode_map: Dict[str, Callable[[], object]] = {
            'set': lambda: set(self.data),
            'dict': lambda: {word: True for word in self.data},
            'index_map': lambda: {i: word for i, word in enumerate(self.data)},
            'binary': lambda: sorted(self.data),
            'trie': lambda: self._build_trie(self.data),
            'naive': lambda: self.data
        }

        prep_func = mode_map.get(mode, mode_map['naive'])
        self.search_data = prep_func()
        logger.info("Search mode '%s' prepared.", mode)

    def _build_trie(self, words: List[str]) -> Dict:
        """Constructs a trie from the list of words."""
        trie: Dict = {}
        for word in words:
            node = trie
            for char in word:
                node = node.setdefault(char, {})
            node['#'] = True
        return trie

    def search(self, target: str) -> Tuple[bool, float]:
        """Performs a search for the target word."""
        if self.search_data is None:
            raise ValueError("Search data not prepared. Call prepare() first.")
        
        search_method = getattr(self, f"{self.mode}_search", self.naive_search)
        start = time.perf_counter()
        result = search_method(target)
        end = time.perf_counter()
        logger.debug("Search for '%s' took %.6f seconds.", target, end - start)
        return result, end - start

    # --- Search implementations ---

    def naive_search(self, target: str) -> bool:
        return target in self.search_data

    def set_search(self, target: str) -> bool:
        return target in self.search_data

    def dict_search(self, target: str) -> bool:
        return target in self.search_data

    def index_map_search(self, target: str) -> bool:
        return target in self.search_data.values()

    def binary_search(self, target: str) -> bool:
        data = self.search_data
        low, high = 0, len(data) - 1
        while low <= high:
            mid = (low + high) // 2
            if data[mid] == target:
                return True
            elif data[mid] < target:
                low = mid + 1
            else:
                high = mid - 1
        return False

    def trie_search(self, target: str) -> bool:
        node = self.search_data
        for char in target:
            if char not in node:
                return False
            node = node[char]
        return '#' in node
