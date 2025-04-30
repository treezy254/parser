"""
Server module for handling incoming socket connections securely and processing
client requests to interact with logs.

It initializes configuration, sets up the main socket server with optional SSL,
and spawns a new thread to handle each client request using the AppService layer.
"""

import os
import socket
import threading
import json
import sys
from typing import Optional

sys.path.append(os.path.abspath("."))

from config import Config
from repositories import LogRepository, StorageRepository
from security import secure_socket, protect_buffer
from app import AppService


def client_handler(
    conn: socket.socket,
    addr: tuple[str, int],
    app_service: AppService,
    config: Config
) -> None:
    """
    Handles a client connection by reading its request and sending an appropriate response.

    Supports actions like:
    - 'create_log': stores a query log.
    - 'read_logs': returns all existing logs.

    Args:
        conn (socket.socket): Active socket connection to the client.
        addr (tuple[str, int]): IP address and port of the connected client.
        app_service (AppService): Core application logic for log handling.
        config (Config): Configuration object for retrieving server settings.
    """
    max_payload_size: int = config.get_server_config()['max_payload_size']

    try:
        # Receive raw bytes from client
        data = conn.recv(max_payload_size)

        # Protect buffer from overflow or unsafe input
        data = protect_buffer(data, max_payload_size)

        # Decode bytes to JSON object
        request = json.loads(data.decode())

        # Determine requested action
        action: Optional[str] = request.get('action')

        if action == 'create_log':
            # Handle log creation
            result = app_service.create_log(
                requesting_ip=addr[0],
                query_string=request['query'],
                algo_name=request['algo']
            )
            conn.sendall(json.dumps(result).encode())

        elif action == 'read_logs':
            # Handle log retrieval
            result = app_service.read_logs()
            conn.sendall(json.dumps(result).encode())

        else:
            # Invalid action provided by client
            conn.sendall(json.dumps({'error': 'Invalid action'}).encode())

    except json.JSONDecodeError:
        conn.sendall(json.dumps({'error': 'Invalid JSON format'}).encode())

    except KeyError as e:
        conn.sendall(json.dumps({'error': f'Missing key: {str(e)}'}).encode())

    except Exception as e:
        # Catch-all for unexpected errors
        conn.sendall(json.dumps({'error': str(e)}).encode())

    finally:
        # Ensure the socket is closed to free up resources
        conn.close()


def main() -> None:
    """
    Entry point of the server application.

    Initializes configuration, sets up repositories and services, 
    starts the socket server (optionally with SSL), and begins accepting connections.
    Each client is handled in a separate daemon thread.
    """
    try:
        config = Config()
        server_conf = config.get_server_config()

        port: int = server_conf['port']
        ssl_enabled: bool = server_conf['ssl_enabled']
        certfile: Optional[str] = server_conf.get('ssl_cert')
        keyfile: Optional[str] = server_conf.get('ssl_key')

        # Initialize repositories and application service
        log_repo = LogRepository()
        storage_repo = StorageRepository()
        app_service = AppService(log_repo, storage_repo, config)

        # Setup server socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('0.0.0.0', port))
        sock.listen(5)
        print(f"[*] Listening on port {port}...")

        # Wrap socket with SSL if configured
        if ssl_enabled:
            sock = secure_socket(sock, certfile, keyfile)
            print("[*] SSL enabled")

        # Continuously accept and handle new connections
        while True:
            conn, addr = sock.accept()
            print(f"[*] Connection from {addr}")

            # Spawn a new thread to handle the client
            thread = threading.Thread(
                target=client_handler,
                args=(conn, addr, app_service, config),
                daemon=True
            )
            thread.start()

    except KeyboardInterrupt:
        # Graceful shutdown on user interrupt
        print("\n[*] Server shutting down.")
        sys.exit(0)

    except Exception as e:
        # Log unexpected errors and exit
        print(f"[!] Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
