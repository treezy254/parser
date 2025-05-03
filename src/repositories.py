import os
import time
import json
import threading
import logging
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Callable, cast, Any, Set, Union
from models import Log  # Assumes Log is a dataclass or class with an 'id' attribute

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LogRepository:
    """
    Handles persistence of Log objects to a JSON file.

    Supports basic CRUD operations on logs stored as JSON entries in a file.
    Thread-safe using a lock for write operations.
    """

    def __init__(self, filepath: Optional[Path] = None) -> None:
        """
        Initializes the LogRepository with a given or default file path.

        Args:
            filepath (Optional[Path]): Custom path for the JSON file. If None, uses default path.
        """
        if filepath is None:
            ROOT_DIR = Path(__file__).resolve().parents[1]
            filepath = ROOT_DIR / 'data' / 'logs' / 'logs.json'
        self.filepath: Path = filepath
        self._lock = threading.Lock()
        self._ensure_file()

    def _ensure_file(self) -> None:
        """Ensures the log file exists. Creates it if not found."""
        if not os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'w') as f:
                    json.dump([], f)
            except Exception as e:
                logger.exception("Failed to create log file: %s", e)

    def create_log(self, log: Log) -> None:
        """
        Appends a new log entry to the file.

        Args:
            log (Log): The log instance to persist.
        """
        with self._lock:
            try:
                logs = self.read_logs()
                logs.append(log.__dict__)  # Assumes Log is JSON-serializable
                with open(self.filepath, 'w') as f:
                    json.dump(logs, f, default=str, indent=4)
            except Exception as e:
                logger.exception("Failed to create log: %s", e)

    def read_logs(self) -> List[Dict]:
        """
        Reads all log entries from the file.

        Returns:
            List[Dict]: List of logs as dictionaries.
        """
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
        """
        Updates a log entry by ID.

        Args:
            log_id (str): ID of the log to update.
            updates (Dict): Dictionary of fields to update.

        Returns:
            bool: True if log was updated, False otherwise.
        """
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
        """
        Deletes a log entry by ID.

        Args:
            log_id (str): ID of the log to delete.

        Returns:
            bool: True if deletion was successful, False otherwise.
        """
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


# Define search data types
SearchDataType = Union[
    List[str],  # For naive and binary search
    Set[str],   # For set search
    Dict[str, bool],  # For dict search
    Dict[int, str],   # For index map search
    Dict[str, Any]    # For trie search
]


class StorageRepository:
    """
    Handles data loading and searching with multiple search modes.

    Supports naive, set, dictionary, index map, binary search, and trie search.
    """

    def __init__(self) -> None:
        self.data: Optional[List[str]] = None
        self.search_data: Optional[SearchDataType] = None
        self.mode: str = 'naive'
        self.last_loaded_file: Optional[str] = None

    def load_file(self, filepath: str) -> bool:
        """
        Loads data (line-by-line) from a file.

        Args:
            filepath (str): Path to the file.

        Returns:
            bool: True if successfully loaded, else False.
        """
        logger.info(f"Current working directory: {os.getcwd()}")

        search_paths = [
            filepath,
            os.path.abspath(filepath),
            os.path.join(os.getcwd(), filepath),
            os.path.join(os.path.dirname(os.getcwd()), filepath),
            os.path.join(os.path.dirname(os.getcwd()), os.path.basename(filepath)),
        ]

        for path in search_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        self.data = f.read().splitlines()
                    logger.info(f"Loaded {len(self.data)} lines from {path}")
                    self.last_loaded_file = path
                    return True
                except Exception as e:
                    logger.exception(f"Error loading found file {path}: {e}")
        logger.warning(f"File not found. Tried: {search_paths}")
        return False

    def prepare(self, mode: str = 'naive') -> None:
        if self.data is None:
            msg = "No data loaded. Call load_file() first."
            if self.last_loaded_file:
                msg += f" Last attempt was: {self.last_loaded_file}"
            raise ValueError(msg)

        # Safely cast self.data to List[str] since we've checked it's not None
        data: List[str] = self.data

        self.mode = mode if mode in ['set', 'dict', 'index_map', 'binary', 'trie', 'naive'] else 'naive'

        mode_map: Dict[str, Callable[[], SearchDataType]] = {
            'set': lambda: set(data),
            'dict': lambda: {word: True for word in data},
            'index_map': lambda: {i: word for i, word in enumerate(data)},
            'binary': lambda: sorted(data),
            'trie': lambda: self._build_trie(data),
            'naive': lambda: data,
        }

        try:
            self.search_data = mode_map.get(self.mode, mode_map['naive'])()
            logger.info(f"Prepared search mode '{self.mode}' with {len(data)} items.")
        except Exception as e:
            logger.exception(f"Error preparing search mode '{self.mode}': {e}")
            self.mode = 'naive'
            self.search_data = data
            logger.info("Falling back to 'naive' mode.")

    def _build_trie(self, words: List[str]) -> Dict[str, Any]:
        """
        Builds a trie data structure from a list of words.

        Args:
            words (List[str]): Words to include in trie.

        Returns:
            Dict[str, Any]: Trie structure.
        """
        trie: Dict[str, Any] = {}
        for word in words:
            if not word:
                continue
            node = trie
            for char in word:
                node = node.setdefault(char, {})
            node['#'] = True  # End of word marker
        return trie

    def search(self, target: str) -> Tuple[bool, float]:
        """
        Searches for a word using the currently prepared mode.

        Args:
            target (str): Word to search.

        Returns:
            Tuple[bool, float]: (Found or not, time taken in seconds)

        Raises:
            ValueError: If search data has not been prepared.
        """
        if self.search_data is None:
            raise ValueError("Search data not prepared. Call prepare() first.")

        if not target:
            logger.warning("Empty search target provided.")
            return False, 0.0

        search_method = getattr(self, f"{self.mode}_search", self.naive_search)
        start = time.perf_counter()
        result = search_method(target)
        end = time.perf_counter()
        execution_time = end - start

        logger.info(f"Search '{target}' with mode '{self.mode}' took {execution_time:.6f}s. Found: {result}")
        return result, execution_time

    # --- Search implementations below ---

    def naive_search(self, target: str) -> bool:
        """Naive linear search."""
        assert self.search_data is not None
        data = cast(List[str], self.search_data)
        return target in data

    def set_search(self, target: str) -> bool:
        """Search using a set."""
        assert self.search_data is not None
        data = cast(Set[str], self.search_data)
        return target in data

    def dict_search(self, target: str) -> bool:
        """Search using a dictionary."""
        assert self.search_data is not None
        data = cast(Dict[str, bool], self.search_data)
        return target in data

    def index_map_search(self, target: str) -> bool:
        """Search values in an index map."""
        assert self.search_data is not None
        data = cast(Dict[int, str], self.search_data)
        return target in data.values()

    def binary_search(self, target: str) -> bool:
        """Binary search (requires sorted list)."""
        assert self.search_data is not None
        data = cast(List[str], self.search_data)
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
        """Search using a trie."""
        assert self.search_data is not None
        node = cast(Dict[str, Any], self.search_data)
        for char in target:
            if char not in node:
                return False
            node = node[char]
        return '#' in node