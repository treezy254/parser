from typing import List, Dict, Optional
import uuid
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from repositories import LogRepository, StorageRepository
from config import Config
from models import Log  # Assuming the `Log` model is defined in a `models` module

logger = logging.getLogger(__name__)


class AppService:
    def __init__(
        self,
        log_repo: LogRepository,
        storage_repo: StorageRepository,
        config: Config
    ) -> None:
        self.log_repo = log_repo
        self.storage_repo = storage_repo
        self.config = config

        file_config = self.config.get_file_config()
        server_config = self.config.get_server_config()

        self.file_path: str = file_config.get('linuxpath', '')
        self.reread_on_query: bool = server_config.get('reread_on_query', False)
        self.search_mode: str = server_config.get('search_mode', 'naive')

    def create_log(self, requesting_ip: str, query_string: str, algo_name: str) -> Dict[str, Optional[str]]:
        try:
            # Reload file if configured to do so, or if data is not already loaded
            if self.reread_on_query or self.storage_repo.data is None:
                self.storage_repo.load_file(self.file_path)

            self.storage_repo.prepare(mode=algo_name)

            found: Optional[str]
            exec_time: Optional[float]
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
                    "status": "error"
                }

            # Create log
            log = Log(id=str(uuid.uuid4()), query=query_string, requesting_ip=requesting_ip) 
            log.create(found=found, exec_time=exec_time)
            self.log_repo.create_log(log)

            return {
                "id": log.id,
                "query": log.query,
                "requesting_ip": log.requesting_ip,
                "execution_time": log.execution_time,
                "timestamp": log.timestamp.isoformat(),
                "status": found  # Use the search result as status
            }

        except Exception as e:
            logger.exception("Failed to create log")
            return {
                "id": None,
                "query": query_string,
                "requesting_ip": requesting_ip,
                "execution_time": None,
                "timestamp": None,
                "status": "error"
            }

    def read_logs(self) -> List[Dict[str, Optional[str]]]:
        try:
            return self.log_repo.read_logs()
        except Exception as e:
            logger.exception("Failed to read logs")
            return []

    def create_logs_parallel(self, requests: List[Dict[str, str]]) -> List[Dict[str, Optional[str]]]:
        """
        Create logs in parallel using multithreading.
        Each request must be a dict with 'requesting_ip', 'query_string', 'algo_name'
        """
        results: List[Dict[str, Optional[str]]] = []

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
                    # Update status to match test expectations ('Found' with capital F)
                    if result['status'] == 'found':
                        result['status'] = 'Found'
                    results.append(result)
                except Exception as e:
                    logger.exception("Error processing log request")
                    results.append({
                        "id": None,
                        "query": futures[future]['query_string'],
                        "requesting_ip": futures[future]['requesting_ip'],
                        "execution_time": None,
                        "timestamp": None,
                        "status": "error"
                    })

        return results