"""
Server module for handling incoming socket connections securely and processing
client requests to interact with logs.

It initializes configuration, sets up the main socket server with optional SSL,
and spawns a new thread to handle each client request using the
AppService layer.
"""

from app import AppService
from security import secure_socket, protect_buffer
from repositories import LogRepository, StorageRepository
from config import Config
import os
import socket
import threading
import json
import sys
from typing import Optional, Dict, Any
import datetime

sys.path.append(os.path.abspath("."))


def format_tcp_response(result: Dict[str, Any]) -> bytes:
    """
    Format the response according to requirements:
    - First line: STRING EXISTS or STRING NOT FOUND with a newline
    - Additional lines: Debug information with log details

    Args:
        result (Dict[str, Any]): The result dictionary from AppService

    Returns:
        bytes: Formatted response encoded as bytes
    """
    status = result.get("status", "error")

    # Determine the main response string
    if status == "STRING_EXISTS":
        response_lines = ["STRING EXISTS\n"]
    elif status == "STRING_NOT_FOUND":
        response_lines = ["STRING NOT_FOUND\n"]
    else:
        # For error cases
        response_lines = [f"ERROR: {result.get('error', 'Unknown error')}\n"]

    # Add debug information
    response_lines.append("DEBUG:\n")
    response_lines.append(f"  Query: {result.get('query', 'N/A')}\n")
    response_lines.append(
        f"  Requesting IP: {result.get('requesting_ip', 'N/A')}\n")
    response_lines.append(
        f"  Execution Time: {result.get('execution_time', 'N/A')}s\n")
    response_lines.append(f"  Timestamp: {result.get('timestamp', 'N/A')}\n")
    response_lines.append(f"  Log ID: {result.get('id', 'N/A')}\n")

    # Join all lines and encode
    return "".join(response_lines).encode()


def client_handler(conn: socket.socket,
                   addr: tuple[str,
                               int],
                   app_service: AppService,
                   config: Config) -> None:
    """
    Handles a client connection by reading its request and sending an
    appropriate response.

    Supports actions like:
    - 'create_log': stores a query log.
    - 'read_logs': returns all existing logs.

    Args:
        conn (socket.socket): Active socket connection to the client.
        addr (tuple[str, int]): IP address and port of the connected client.
        app_service (AppService): Core application logic for log handling.
        config (Config): Configuration object for retrieving server settings.
    """
    server_config = config.get_server_config()
    # Explicitly cast to int to satisfy mypy
    max_payload_size: int = int(server_config["max_payload_size"])

    try:
        # Receive raw bytes from client
        data = conn.recv(max_payload_size)

        # Protect buffer from overflow or unsafe input
        data = protect_buffer(data, max_payload_size)

        # Decode bytes to JSON object
        request = json.loads(data.decode())

        # Determine requested action
        action: Optional[str] = request.get("action")

        if action == "create_log":
            # Handle log creation
            result = app_service.create_log(
                requesting_ip=addr[0],
                query_string=request["query"],
                algo_name=request["algo"],
            )
            # Format response according to requirements
            response = format_tcp_response(result)

            # Print the same response to terminal
            print("\n" + response.decode(), end="")

            # Send response to client
            conn.sendall(response)

        elif action == "read_logs":
            # Handle log retrieval
            logs = app_service.read_logs()

            # For read_logs, we'll print a more readable format to terminal
            print("\n[*] Sending log data to client:")
            for log in logs:
                print("DEBUG:")
                print(f"  Query: {log.get('query', 'N/A')}")
                print(f"  Requesting IP: {log.get('requesting_ip', 'N/A')}")
                print(f"  Execution Time: {log.get('execution_time', 'N/A')}s")
                print(f"  Timestamp: {log.get('timestamp', 'N/A')}")
                print(f"  Log ID: {log.get('id', 'N/A')}")
                print(f"  Status: {log.get('status', 'N/A')}")
                print("")

            # For read_logs, we'll send a JSON response since we're returning
            # multiple logs
            conn.sendall(json.dumps(logs).encode())

        else:
            # Invalid action provided by client
            error_result = {
                "status": "error",
                "error": "Invalid action",
                "query": request.get("query", "N/A"),
                "requesting_ip": addr[0],
                "timestamp": datetime.datetime.now().isoformat(),
                "execution_time": 0,
                "id": None,
            }
            response = format_tcp_response(error_result)
            print("\n" + response.decode(), end="")
            conn.sendall(response)

    except json.JSONDecodeError:
        error_result = {
            "status": "error",
            "error": "Invalid JSON format",
            "requesting_ip": addr[0],
            "timestamp": datetime.datetime.now().isoformat(),
            "execution_time": 0,
            "id": None,
        }
        response = format_tcp_response(error_result)
        print("\n" + response.decode(), end="")
        conn.sendall(response)

    except KeyError as e:
        error_result = {
            "status": "error",
            "error": f"Missing key: {str(e)}",
            "requesting_ip": addr[0],
            "timestamp": datetime.datetime.now().isoformat(),
            "execution_time": 0,
            "id": None,
        }
        response = format_tcp_response(error_result)
        print("\n" + response.decode(), end="")
        conn.sendall(response)

    except Exception as e:
        # Catch-all for unexpected errors
        error_result = {
            "status": "error",
            "error": str(e),
            "requesting_ip": addr[0],
            "timestamp": datetime.datetime.now().isoformat(),
            "execution_time": 0,
            "id": None,
        }
        response = format_tcp_response(error_result)
        print("\n" + response.decode(), end="")
        conn.sendall(response)

    finally:
        # Ensure the socket is closed to free up resources
        conn.close()


def main() -> None:
    """
    Entry point of the server application.

    Initializes configuration, sets up repositories and services,
    starts the socket server (optionally with SSL), and begins accepting
    connections.
    Each client is handled in a separate daemon thread.
    """
    try:
        # Configure console output formatting
        print("\n" + "=" * 50)
        print(" String Search Server - TCP Response Format")
        print("=" * 50 + "\n")

        config = Config()
        server_conf = config.get_server_config()

        # Explicitly cast values to expected types
        port: int = int(server_conf["port"])
        ssl_enabled: bool = bool(server_conf["ssl_enabled"])
        certfile: Optional[str] = server_conf.get("ssl_cert")
        keyfile: Optional[str] = server_conf.get("ssl_key")

        # Initialize repositories and application service
        log_repo = LogRepository()
        storage_repo = StorageRepository()
        app_service = AppService(log_repo, storage_repo, config)

        # Setup server socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("0.0.0.0", port))
        sock.listen(5)
        print(f"[*] Server started. Listening on port {port}...")

        # Wrap socket with SSL if configured
        if ssl_enabled:
            # Fix: Ensure certfile and keyfile are not None before passing to
            # secure_socket
            if certfile is None or keyfile is None:
                raise ValueError(
                    "SSL is enabled but certificate or key file is missing"
                )
            sock = secure_socket(sock, certfile, keyfile)
            print("[*] SSL enabled")

        print("\n[*] Ready to accept connections.")
        print("-" * 50)

        # Continuously accept and handle new connections
        while True:
            conn, addr = sock.accept()
            print(f"\n[*] New connection from {addr[0]}:{addr[1]}")

            # Spawn a new thread to handle the client
            thread = threading.Thread(
                target=client_handler,
                args=(conn, addr, app_service, config),
                daemon=True,
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
