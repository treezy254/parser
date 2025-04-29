import os
import time
import json
import threading
import logging
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Callable
from models import Log

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LogRepository:
    """Handles persistence of Log objects to a JSON file."""
    
    def __init__(self, filepath: Path = None) -> None:
        if filepath is None:
            # Resolve path relative to project root (assuming src/ is 1 level below root)
            ROOT_DIR = Path(__file__).resolve().parents[1]
            filepath = ROOT_DIR / 'data' / 'logs' / 'logs.json'
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
        try:
            with open(self.filepath, 'r') as f:
                content = f.read().strip()
                if not content:
                    logger.warning("Log file is empty. Returning empty list.")
                    return []
                return json.loads(content)
        except json.JSONDecodeError as e:
            logger.exception("Invalid JSON format: %s", e)
            return []
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
        self.last_loaded_file: Optional[str] = None

    def load_file(self, filepath: str) -> bool:
        """
        Loads data from a file.
        
        Args:
            filepath (str): Path to the file to load
            
        Returns:
            bool: True if file was loaded successfully, False otherwise
        """
        # Print current directory for debugging
        logger.info(f"Current working directory: {os.getcwd()}")
        
        # Try various path combinations if the direct path doesn't work
        search_paths = [
            filepath,  # Direct path as provided
            os.path.abspath(filepath),  # Absolute path
            os.path.join(os.getcwd(), filepath),  # Relative to current directory
        ]
        
        # Add parent directory paths
        parent_dir = os.path.dirname(os.getcwd())
        search_paths.append(os.path.join(parent_dir, filepath))
        search_paths.append(os.path.join(parent_dir, os.path.basename(filepath)))
        
        for path in search_paths:
            if os.path.exists(path):
                logger.info(f"Found file at: {path}")
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        self.data = f.read().splitlines()
                    logger.info(f"Loaded {len(self.data)} lines from {path}")
                    self.last_loaded_file = path
                    return True
                except Exception as e:
                    logger.exception(f"Error loading found file {path}: {e}")
                    continue
        
        # If we reach here, we couldn't find or load the file
        logger.warning(f"File not found in any of the search paths. Tried: {search_paths}")
        return False

    def prepare(self, mode: str = 'naive') -> None:
        """
        Prepares the data for a given search mode.
        
        Args:
            mode (str): The search algorithm mode to use
            
        Raises:
            ValueError: If no data has been loaded
        """
        if self.data is None:
            error_msg = "No data loaded. Call load_file() first."
            if self.last_loaded_file:
                error_msg += f" Last attempt was with file: {self.last_loaded_file}"
            raise ValueError(error_msg)
        
        self.mode = mode
        valid_modes = ['set', 'dict', 'index_map', 'binary', 'trie', 'naive']
        
        if mode not in valid_modes:
            logger.warning(f"Unknown search mode '{mode}', defaulting to 'naive'")
            self.mode = 'naive'
        
        mode_map: Dict[str, Callable[[], object]] = {
            'set': lambda: set(self.data),
            'dict': lambda: {word: True for word in self.data},
            'index_map': lambda: {i: word for i, word in enumerate(self.data)},
            'binary': lambda: sorted(self.data),
            'trie': lambda: self._build_trie(self.data),
            'naive': lambda: self.data
        }

        try:
            prep_func = mode_map.get(self.mode, mode_map['naive'])
            self.search_data = prep_func()
            logger.info(f"Search mode '{self.mode}' prepared with {len(self.data)} items.")
        except Exception as e:
            logger.exception(f"Error preparing search data for mode '{self.mode}': {e}")
            # Fall back to naive mode in case of error
            self.mode = 'naive'
            self.search_data = self.data
            logger.info(f"Falling back to 'naive' search mode after error.")

    def _build_trie(self, words: List[str]) -> Dict:
        """Constructs a trie from the list of words."""
        logger.debug(f"Building trie from {len(words)} words")
        trie: Dict = {}
        for word in words:
            if not word:  # Skip empty words
                continue
            node = trie
            for char in word:
                node = node.setdefault(char, {})
            node['#'] = True
        logger.debug("Trie construction completed")
        return trie

    def search(self, target: str) -> Tuple[bool, float]:
        """
        Performs a search for the target word.
        
        Args:
            target (str): The string to search for
            
        Returns:
            Tuple[bool, float]: (found, execution_time)
            
        Raises:
            ValueError: If search data has not been prepared
        """
        if self.search_data is None:
            raise ValueError("Search data not prepared. Call prepare() first.")
        
        if not target:
            logger.warning("Empty search target provided, returning False")
            return False, 0.0
        
        search_method = getattr(self, f"{self.mode}_search", self.naive_search)
        start = time.perf_counter()
        result = search_method(target)
        end = time.perf_counter()
        execution_time = end - start
        logger.info(f"Search for '{target}' using {self.mode} mode took {execution_time:.6f} seconds. Result: {result}")
        return result, execution_time

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