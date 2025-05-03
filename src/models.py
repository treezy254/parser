import threading
from datetime import datetime
from typing import Optional, Dict, Union


class Log:
    """
    A thread-safe log entry for recording query executions.

    This class records details such as query text, requester's IP,
    execution time, timestamp, and query status.
    """

    def __init__(self, id: str, query: str, requesting_ip: str) -> None:
        """
        Initialize a Log object.

        Args:
            id (str): Unique identifier for the log.
            query (str): The query string to log.
            requesting_ip (str): IP address of the requester.
        """
        self.id: str = id
        self.query: str = ""
        self.requesting_ip: str = requesting_ip
        self.execution_time: Optional[float] = None
        self.timestamp: Optional[datetime] = None
        self.status: Optional[bool] = None
        self._lock = threading.Lock()

        self._set_query(query)

    def _set_query(self, query: str) -> None:
        """
        Safely set the query, ensuring it doesn't exceed 1024 bytes
        when UTF-8 encoded. Truncates cleanly at character boundaries
        if needed.

        Args:
            query (str): The query string to sanitize and store.
        """
        try:
            encoded_query = query.encode("utf-8")
            if len(encoded_query) > 1024:
                truncated = encoded_query[:1024]

                # Ensure the truncated bytes do not end mid-character
                while truncated and truncated[-1] & 0xC0 == 0x80:
                    truncated = truncated[:-1]

                self.query = truncated.decode("utf-8", errors="replace")
            else:
                self.query = query
        except (AttributeError, UnicodeEncodeError):
            # Fallback to a shorter safe string
            self.query = str(query)[:256]

    def create(self, found: bool, exec_time: float) -> None:
        """
        Populate log entry with result status and execution details.

        Args:
            found (bool): Whether the query returned any results.
            exec_time (float): Time taken to execute the query in seconds.
        """
        with self._lock:
            self.status = found
            self.execution_time = exec_time
            self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Union[str, float, bool, None]]:
        """
        Serialize the log entry into a dictionary format.

        Returns:
            dict: A dictionary representing the log entry.
        """
        return {
            "id": self.id,
            "query": self.query,
            "requesting_ip": self.requesting_ip,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp.isoformat() \
                if self.timestamp else None,
            "status": self.status
        }
