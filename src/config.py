import json
import os
from typing import Dict, Optional

class Config:
    def __init__(self, config_path: Optional[str] = None) -> None:
        """
        Initializes the Config class by loading configuration from a JSON file.

        Args:
            config_path (str, optional): Path to the configuration file. Defaults to None,
                                          which loads 'config.json' from the current directory.

        Raises:
            FileNotFoundError: If the specified configuration file doesn't exist.
            json.JSONDecodeError: If the configuration file is not a valid JSON.
            KeyError: If expected keys are not found in the loaded configuration.
        """
        if config_path is None:
            # Default config file path
            config_path = os.path.join(os.path.dirname(__file__), "config.json")

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file '{config_path}' not found.")

        try:
            with open(config_path, "r") as f:
                config_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Error parsing config file: {e}")

        # Assign configuration values
        self._file_config = config_data.get("file_config", {})
        self._server_config = config_data.get("server_config", {})

        # Validate required keys in server_config and file_config
        if not self._file_config or not self._server_config:
            raise KeyError("Missing required sections in the config file: 'file_config' or 'server_config'")

    def get_file_config(self) -> Dict[str, str]:
        """
        Returns the file configuration settings.

        Returns:
            dict: The 'file_config' section from the loaded configuration.
        """
        return self._file_config

    def get_server_config(self) -> Dict[str, str]:
        """
        Returns the server configuration settings.

        Returns:
            dict: The 'server_config' section from the loaded configuration.
        """
        return self._server_config
