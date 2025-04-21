class AppService:
        def __init__(self, log_repo: LogRepository, storage_repo: StorageRepository, search_service: SearchService, config: Config):
                self.log_repo = log_repo
                        self.storage_repo = storage_repo
                                self.search_service = search_service
                                        self.config = config
                                                self.file_content = None
                                                        self.file_path = self.config.get_file_config()['linuxpath']
                                                                self.reread_on_query = self.config.get_server_config()['reread_on_query']

                                                                    def _load_file(self):
                                                                            if self.reread_on_query or self.file_content is None:
                                                                                        self.file_content = self.storage_repo.load_file(self.file_path)
                                                                                                return self.file_content

                                                                                                    def create_log(self, requesting_ip: str, query_string: str, algo_name: str) -> dict:
                                                                                                            file_content = self._load_file()

                                                                                                                    log = Log(
                                                                                                                                id=str(uuid.uuid4()),
                                                                                                                                            query=query_string,
                                                                                                                                                        requesting_ip=requesting_ip,
                                                                                                                                                                )
                                                                                                                                                                        # command domain model to create itself
                                                                                                                                                                                log.create(file_content=file_content, algo_name=algo_name)
                                                                                                                                                                                        # command repository to persist
                                                                                                                                                                                                self.log_repo.create_log(log)
                                                                                                                                                                                                        # return DTO (data dict)
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