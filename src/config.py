class Config:
    def __init__(self):
        self._file_config = {
            "linuxpath": "data/words.txt"
        }
        self._server_config = {
            "reread_on_query": True,
            "search_mode": "trie"
        }

    def get_file_config(self) -> dict:
        return self._file_config

    def get_server_config(self) -> dict:
        return self._server_config
