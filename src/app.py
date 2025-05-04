from typing import List, Dict, Optional, Union
import uuid
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from repositories import LogRepository, StorageRepository
from config import Config
from models import Log

logger = logging.getLogger(__name__)


class AppService:
    """
    Application service layer responsible for handling search queries,
    managing logs, and interacting with storage and logging repositories.
    """

    def __init__(
        self,
        log_repo: LogRepository,
        storage_repo: StorageRepository,
        config: Config
    ) -> None:
        """
        Initialize the AppService with required dependencies.

        :param log_repo: Repository for persisting and retrieving logs
        :param storage_repo: Repository for data storage and search logic
        :param config: Application configuration instance
        """
        self.log_repo = log_repo
        self.storage_repo = storage_repo
        self.config = config

        file_config = self.config.get_file_config()
        server_config = self.config.get_server_config()

        self.file_path: str = file_config.get('linuxpath', '')
        # Fix 1: Explicitly convert to boolean
        self.reread_on_query: bool = bool(
            server_config.get('reread_on_query', False)
        )
        self.search_mode: str = server_config.get('search_mode', 'naive')

        # Validate file path at initialization
        self._validate_file_path()

    def _validate_file_path(self) -> None:
        """
        Ensure the configured file path is absolute and exists.
        Logs warnings if issues are detected.
        """
        if not self.file_path:
            logger.warning(
                "No file path configured. Search operations will fail."
            )
            return

        # Convert relative path to absolute
        if not os.path.isabs(self.file_path):
            # Use the project root directory
            project_root = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..")
            )
            absolute_path = os.path.join(project_root, self.file_path)
            logger.info(
                (
                    f"Converting relative path '{self.file_path}' "
                    f"to absolute path '{absolute_path}'"
                )
            )
            self.file_path = absolute_path

        # Check if file exists
        if not os.path.exists(self.file_path):
            logger.warning(f"Data file not found at path: {self.file_path}")

            # Attempt to find the file in the parent directory
            parent_dir = os.path.dirname(os.getcwd())
            alternative_path = os.path.join(parent_dir, self.file_path)
            if os.path.exists(alternative_path):
                logger.info(
                    f"Found data file in parent directory: {alternative_path}"
                )
                self.file_path = alternative_path

    def create_log(
        self,
        requesting_ip: str,
        query_string: str,
        algo_name: str
    ) -> Dict[str, Optional[Union[str, float]]]:
        """
        Process a query, perform search, and log the results.

        :param requesting_ip: IP address of the requester
        :param query_string: The search query string
        :param algo_name: Algorithm name used for searching
        :return: A dictionary containing log information and status
        """
        try:
            # Initialize log with None to ensure it's defined in all code paths
            log = None

            # Reload data file if needed
            if self.reread_on_query or self.storage_repo.data is None:
                file_loaded = self.storage_repo.load_file(self.file_path)
                if not file_loaded:
                    error_msg = f"Data file could not be loaded: {self.file_path}. " \
                                f"Ensure the file exists and has ≤ {MAX_ROWS} rows."
                    logger.error(error_msg)
                    return {
                        "id": None,
                        "query": query_string,
                        "requesting_ip": requesting_ip,
                        "execution_time": None,
                        "timestamp": None,
                        "status": "error",
                        "error": error_msg
                    }

            if self.storage_repo.data is None:
                logger.error("No data loaded in storage repository")
                return {
                    "id": None,
                    "query": query_string,
                    "requesting_ip": requesting_ip,
                    "execution_time": None,
                    "timestamp": None,
                    "status": "error",
                    "error": "No data loaded in storage repository"
                }

            try:
                self.storage_repo.prepare(mode=algo_name)
            except ValueError as e:
                logger.error(f"Failed to prepare storage: {e}")
                return {
                    "id": None,
                    "query": query_string,
                    "requesting_ip": requesting_ip,
                    "execution_time": None,
                    "timestamp": None,
                    "status": "error",
                    "error": f"Failed to prepare storage: {str(e)}"
                }

            try:
                found, exec_time = self.storage_repo.search(query_string)
            except Exception as e:
                logger.exception("Search failed: %s", e)
                return {
                    "id": None,
                    "query": query_string,
                    "requesting_ip": requesting_ip,
                    "execution_time": None,
                    "timestamp": None,
                    "status": "error",
                    "error": f"Search operation failed: {str(e)}"
                }

            # Create and persist log
            log_id = str(uuid.uuid4())
            log = Log(
                id=log_id,
                query=query_string,
                requesting_ip=requesting_ip
            )
            log.create(found=found, exec_time=exec_time)
            self.log_repo.create_log(log)

            # Safely access timestamp
            timestamp_str = (
                log.timestamp.isoformat()
                if hasattr(log, 'timestamp') and log.timestamp is not None
                else None
            )

            # Fix 2: Update return type to include float for execution_time
            return {
                "id": log.id,
                "query": log.query,
                "requesting_ip": log.requesting_ip,
                "execution_time": log.execution_time,  # This is likely a float
                "timestamp": timestamp_str,
                "status": "STRING_EXISTS" if found else "STRING_NOT_FOUND"
            }

        except Exception as e:
            logger.exception("Failed to create log")
            return {
                "id": None,
                "query": query_string,
                "requesting_ip": requesting_ip,
                "execution_time": None,
                "timestamp": None,
                "status": "error",
                "error": str(e)
            }

    def read_logs(self) -> List[Dict[str, Optional[Union[str, float]]]]:
        """
        Retrieve all logs from the log repository.

        :return: List of log entries as dictionaries
        """
        try:
            return self.log_repo.read_logs()
        except Exception as e:
            logger.exception(f"Failed to read logs: {e}")
            return []

    def create_logs_parallel(
        self,
        requests: List[Dict[str, str]]
    ) -> List[Dict[str, Optional[Union[str, float]]]]:
        """
        Create logs in parallel using a thread pool for performance.

        :param requests: List of request dicts, each containing:
                         'requesting_ip', 'query_string', and 'algo_name'
        :return: List of log results with success/error statuses
        """
        results: List[Dict[str, Optional[Union[str, float]]]] = []

        with ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(
                    self.create_log,
                    req['requesting_ip'],
                    req['query_string'],
                    req['algo_name']
                ): req for req in requests
            }

            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.exception("Error processing log request")
                    req = futures[future]
                    results.append({
                        "id": None,
                        "query": req['query_string'],
                        "requesting_ip": req['requesting_ip'],
                        "execution_time": None,
                        "timestamp": None,
                        "status": "error",
                        "error": str(e)
                    })

        return results
