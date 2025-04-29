import socket
import threading
import json
import sys
from typing import Optional

from config import Config
from repositories import LogRepository, StorageRepository
from security import secure_socket, protect_buffer
from app import AppService


def client_handler(
    conn: socket.socket, addr: tuple[str, int], app_service: AppService, config: Config
) -> None:
    """
    Handles incoming client connections and processes requests such as
    creating and reading logs.

    Args:
        conn: The client socket connection.
        addr: The address of the client.
        app_service: The application service instance.
        config: The configuration object.
    """
    max_payload_size = config.get_server_config()['max_payload_size']

    try:
        # Receive data from client and ensure it doesn't exceed max payload size
        data = conn.recv(max_payload_size)
        data = protect_buffer(data, max_payload_size)
        
        # Decode and parse the JSON data from client
        request = json.loads(data.decode())

        # Process actions based on the request
        action = request.get('action')
        if action == 'create_log':
            result = app_service.create_log(
                requesting_ip=addr[0],
                query_string=request['query'],
                algo_name=request['algo']
            )
            conn.sendall(json.dumps(result).encode())
        elif action == 'read_logs':
            result = app_service.read_logs()
            conn.sendall(json.dumps(result).encode())
        else:
            conn.sendall(json.dumps({'error': 'Invalid action'}).encode())
    except json.JSONDecodeError:
        conn.sendall(json.dumps({'error': 'Invalid JSON format'}).encode())
    except KeyError as e:
        conn.sendall(json.dumps({'error': f'Missing key: {str(e)}'}).encode())
    except Exception as e:
        conn.sendall(json.dumps({'error': str(e)}).encode())
    finally:
        # Ensure the connection is closed properly
        conn.close()


def main() -> None:
    """
    Main function to start the server, initialize services, and handle connections.
    """
    try:
        config = Config()
        server_conf = config.get_server_config()
        port = server_conf['port']
        ssl_enabled = server_conf['ssl_enabled']
        certfile = server_conf['ssl_cert']
        keyfile = server_conf['ssl_key']

        # Repositories and service initialization
        log_repo = LogRepository()
        storage_repo = StorageRepository()
        app_service = AppService(log_repo, storage_repo, config)

        # Setup socket for server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('0.0.0.0', port))
        sock.listen(5)
        print(f"[*] Listening on port {port}...")

        # Apply SSL if enabled
        if ssl_enabled:
            sock = secure_socket(sock, certfile, keyfile)
            print("[*] SSL enabled")

        # Server loop: Accept connections and start a new thread for each client
        while True:
            conn, addr = sock.accept()
            print(f"[*] Connection from {addr}")
            threading.Thread(
                target=client_handler,
                args=(conn, addr, app_service, config),
                daemon=True
            ).start()

    except KeyboardInterrupt:
        print("\n[*] Server shutting down.")
        sys.exit(0)
    except Exception as e:
        print(f"[!] Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
