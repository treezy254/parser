from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import threading
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Log:
    """A data class representing a log entry for a query operation."""
    id: str
    query: str
    requesting_ip: str
    execution_time: Optional[float] = None
    timestamp: Optional[datetime] = None
    status: Optional[bool] = None  # True if string exists, False otherwise

    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    def __post_init__(self) -> None:
        """Ensure query does not exceed 1024 bytes when encoded."""
        try:
            query_bytes: bytes = self.query.encode('utf-8')
            if len(query_bytes) > 1024:
                truncated = query_bytes[:1024].rstrip(b'\x00')
                self.query = truncated.decode('utf-8', errors='ignore')
                logger.warning("Query truncated to fit 1024-byte limit.")
        except Exception as e:
            logger.exception("Failed to process query during initialization: %s", e)

    def create(self, found: bool, exec_time: float) -> None:
        """
        Update log with execution status and time.
        
        Args:
            found (bool): Whether the search result was found.
            exec_time (float): Execution time in seconds.
        """
        with self._lock:
            try:
                self.status = found
                self.execution_time = exec_time
                self.timestamp = datetime.utcnow()
                logger.info("Log created: %s", self)
            except Exception as e:
                logger.exception("Failed to update log: %s", e)
