import uuid
from datetime import datetime
import threading

class Log:
    def __init__(self, id: str, query: str, requesting_ip: str):
        """
        Initialize a Log object.
        
        :param id: Unique identifier for the log
        :param query: The query string to log
        :param requesting_ip: IP address of the requester
        """
        self.id = id
        # Ensure query doesn't exceed 1024 bytes when encoded
        self._set_query(query)
        self.requesting_ip = requesting_ip
        self.execution_time = None
        self.timestamp = None
        self.status = None
        self._lock = threading.Lock()
        
    def _set_query(self, query):
        """Safely set the query ensuring it doesn't exceed 1024 bytes when UTF-8 encoded"""
        try:
            encoded_query = query.encode("utf-8")
            if len(encoded_query) > 1024:
                # Truncate the query to fit within 1024 bytes
                # This approach handles multi-byte characters properly
                truncated = encoded_query[:1024]
                # Make sure we don't break in the middle of a multi-byte character
                while truncated[-1] & 0xC0 == 0x80:  # Check if it's a continuation byte
                    truncated = truncated[:-1]
                self.query = truncated.decode("utf-8", errors="replace")
            else:
                self.query = query
        except (AttributeError, UnicodeEncodeError) as e:
            # Handle encoding errors by using a safe default
            self.query = str(query)[:256]  # Fallback with length limit
            
    def create(self, found: bool, exec_time: float):
        """
        Update the log with execution results.
        
        :param found: Whether the query returned results
        :param exec_time: Execution time in seconds
        """
        with self._lock:
            self.status = found
            self.execution_time = exec_time
            self.timestamp = datetime.now()
        
    def to_dict(self):
        """Convert the log to a dictionary."""
        return {
            "id": self.id,
            "query": self.query,
            "requesting_ip": self.requesting_ip,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "status": self.status
        }