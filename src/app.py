from typing import List
import uuid
from repositories import LogRepository, StorageRepository
from config import Config
from models import Log  # Assuming the `Log` model is defined in a `domain` module

class AppService:
    def __init__(
        self,
        log_repo: LogRepository,
        storage_repo: StorageRepository,
        config: Config
    ):
        self.log_repo = log_repo
        self.storage_repo = storage_repo
        self.config = config
        self.file_path = self.config.get_file_config()['linuxpath']
        self.reread_on_query = self.config.get_server_config()['reread_on_query']
        self.search_mode = self.config.get_server_config().get('search_mode', 'naive')

    def create_log(self, requesting_ip: str, query_string: str, algo_name: str) -> dict:
        if self.reread_on_query:
            self.storage_repo.load_file(self.file_path)
        elif self.storage_repo.data is None:
            self.storage_repo.load_file(self.file_path)

        self.storage_repo.prepare(mode=algo_name)

        found, exec_time = self.storage_repo.search(query_string)

        log = Log(
            id=str(uuid.uuid4()),
            query=query_string,
            requesting_ip=requesting_ip,
        )
        log.create(found=found, exec_time=exec_time)
        self.log_repo.create_log(log)

        return {
            "id": log.id,
            "query": log.query,
            "requesting_ip": log.requesting_ip,
            "execution_time": log.execution_time,
            "timestamp": log.timestamp.isoformat(),
            "status": log.status
        }

    def read_logs(self) -> List[dict]:
        return self.log_repo.read_logs()
