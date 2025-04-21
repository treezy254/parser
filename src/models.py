from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from services import SearchService  # we will make SearchService a class now


@dataclass
class Log:
    id: str
    query: str
    requesting_ip: str
    execution_time: Optional[float] = None
    timestamp: Optional[datetime] = None
    status: Optional[bool] = None  # True if string exists, False otherwise

    def __post_init__(self):
        # Invariant: query should not exceed 1024 bytes
        query_bytes = self.query.encode('utf-8')
        if len(query_bytes) > 1024:
            self.query = query_bytes[:1024].rstrip(
                b'\x00').decode('utf-8', errors='ignore')

    def create(self, filepath: str, algo_name: str):
        service = SearchService()
        found, exec_time = service.search_in_file(
            filepath, algo_name, self.query)
        self.execution_time = exec_time
        self.timestamp = datetime.utcnow()
        self.status = found
