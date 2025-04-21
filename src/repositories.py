import json
import os
from typing import List, Optional
from models import Log

class LogRepository:
    def __init__(self, filepath: str = 'logs.json'):
            self.filepath = filepath
                    if not os.path.exists(self.filepath):
                                with open(self.filepath, 'w') as f:
                                                json.dump([], f)

                                                    def create_log(self, log: Log) -> None:
                                                            logs = self.read_logs()
                                                                    logs.append(log.__dict__)
                                                                            with open(self.filepath, 'w') as f:
                                                                                        json.dump(logs, f, default=str, indent=4)

                                                                                            def read_logs(self) -> List[dict]:
                                                                                                    with open(self.filepath, 'r') as f:
                                                                                                                return json.load(f)

                                                                                                                    def update_log(self, log_id: str, updates: dict) -> bool:
                                                                                                                            logs = self.read_logs()
                                                                                                                                    updated = False
                                                                                                                                            for log in logs:
                                                                                                                                                        if log['id'] == log_id:
                                                                                                                                                                        log.update(updates)
                                                                                                                                                                                        updated = True
                                                                                                                                                                                                        break
                                                                                                                                                                                                                if updated:
                                                                                                                                                                                                                            with open(self.filepath, 'w') as f:
                                                                                                                                                                                                                                            json.dump(logs, f, default=str, indent=4)
                                                                                                                                                                                                                                                    return updated

                                                                                                                                                                                                                                                        def delete_log(self, log_id: str) -> bool:
                                                                                                                                                                                                                                                                logs = self.read_logs()
                                                                                                                                                                                                                                                                        initial_length = len(logs)
                                                                                                                                                                                                                                                                                logs = [log for log in logs if log['id'] != log_id]
                                                                                                                                                                                                                                                                                        if len(logs) < initial_length:
                                                                                                                                                                                                                                                                                                    with open(self.filepath, 'w') as f:
                                                                                                                                                                                                                                                                                                                    json.dump(logs, f, default=str, indent=4)
                                                                                                                                                                                                                                                                                                                                return True
                                                                                                                                                                                                                                                                                                                                        return False


                                                                                                                                                                                                                                                                                                                                        class StorageRepository:
                                                                                                                                                                                                                                                                                                                                            def load_file(self, filepath: str) -> Optional[str]:
                                                                                                                                                                                                                                                                                                                                                    if not os.path.exists(filepath):
                                                                                                                                                                                                                                                                                                                                                                print(f"File {filepath} does not exist.")
                                                                                                                                                                                                                                                                                                                                                                            return None
                                                                                                                                                                                                                                                                                                                                                                                    try:
                                                                                                                                                                                                                                                                                                                                                                                                with open(filepath, 'r', encoding='utf-8') as f:
                                                                                                                                                                                                                                                                                                                                                                                                                return f.read()
                                                                                                                                                                                                                                                                                                                                                                                                                        except Exception as e:
                                                                                                                                                                                                                                                                                                                                                                                                                                    print(f"Error loading file: {e}")
                                                                                                                                                                                                                                                                                                                                                                                                                                                return None