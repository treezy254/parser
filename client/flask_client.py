# flask_client.py
from config import Config  # type: ignore
from security import protect_buffer  # type: ignore
import os
import sys
import json
import socket
import ssl
import time
from typing import Optional, List, Dict, Any, Union

from flask import Flask, render_template, request, redirect, url_for  # type: ignore

src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.append(src_path)

app = Flask(__name__)

CONFIG_PATH: str = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'src', 'config.json')
)


def load_config() -> Dict[str, Any]:
    """Load and return the configuration dictionary from the config file."""
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_config(config_data: Dict[str, Any]) -> None:
    """Save the updated configuration dictionary to the config file."""
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2)


def get_current_data_file() -> str:
    """Get the current data file name from the configuration."""
    config_data = load_config()
    file_path: str = config_data.get('file', {}).get('linuxpath', '')
    return os.path.basename(file_path) if file_path else 'data10k.txt'


def update_config_file(data_file: str) -> Dict[str, Any]:
    """
    Update the configuration with a new data file path and save the changes.

    Args:
        data_file: The new data file name to use.

    Returns:
        The updated configuration dictionary.
    """
    config_data = load_config()
    base_path = "tests/data/test_data/"
    full_path = f"{base_path}{data_file}"
    config_data['file']['linuxpath'] = full_path
    if 'file_config' in config_data:
        config_data['file_config']['linuxpath'] = full_path
    save_config(config_data)
    return config_data


config: Config = Config()
server_conf = config.get_server_config()

SERVER_HOST: str = 'localhost'
SERVER_PORT: int = server_conf['port']
SSL_ENABLED: bool = server_conf['ssl_enabled']
SSL_CERT: Optional[str] = server_conf.get('ssl_cert')
SSL_KEY: Optional[str] = server_conf.get('ssl_key')
MAX_PAYLOAD_SIZE: int = server_conf['max_payload_size']
DEFAULT_ALGO: str = 'trie'


def send_request(
    server_address: str,
    port: int,
    ssl_enabled: bool,
    certfile: Optional[str],
    keyfile: Optional[str],
    action: str,
    query: Optional[str],
    algo: Optional[str]
) -> Union[Dict[str, Any], str]:
    """
    Send a request to the backend server and return the response.

    Args:
        server_address: Server hostname or IP.
        port: Port number to connect to.
        ssl_enabled: Whether to use SSL.
        certfile: Path to SSL certificate.
        keyfile: Path to SSL key.
        action: Action to perform ('create_log', 'read_logs', etc.).
        query: The query string to process.
        algo: Algorithm to use.

    Returns:
        Server response as a dict (JSON) or string.
    """
    try:
        sock = socket.create_connection((server_address, port))

        if ssl_enabled:
            context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            if certfile and keyfile:
                context.load_cert_chain(certfile=certfile, keyfile=keyfile)
            sock = context.wrap_socket(sock, server_hostname=server_address)

        request_data = {
            "action": action,
            "query": query,
            "algo": algo
        }

        payload = json.dumps(request_data).encode()
        protected_payload = protect_buffer(payload, MAX_PAYLOAD_SIZE)
        sock.sendall(protected_payload)

        response_data = sock.recv(MAX_PAYLOAD_SIZE)
        sock.close()

        if action == 'create_log':
            return response_data.decode()

        try:
            return json.loads(response_data.decode())
        except json.JSONDecodeError:
            return {
                'error': 'Invalid JSON response from server',
                'raw_response': response_data.decode()
            }

    except Exception as e:
        return {'error': str(e)}


def extract_execution_time_ms(log_response: str) -> Optional[float]:
    """
    Extract and convert execution time (in seconds) from log response to ms.

    Args:
        log_response: The server response string.

    Returns:
        Execution time in milliseconds, if found; otherwise None.
    """
    try:
        if "Execution Time:" in log_response:
            parts = log_response.split("Execution Time:")
            if len(parts) > 1:
                time_part = parts[1].strip().split("s")[0]
                return float(time_part) * 1000
    except Exception:
        pass
    return None


@app.route('/', methods=['GET', 'POST'])
def index() -> str:
    """
    Flask route for the index page.

    Handles query submission and performance metrics display.

    Returns:
        Rendered HTML page.
    """
    results: List[Union[str, Dict[str, Any]]] = []
    error: Optional[str] = None
    server_address: str = SERVER_HOST
    server_port: int = SERVER_PORT
    performance_metrics: Optional[Dict[str, Union[int, float, str]]] = None
    current_file: str = get_current_data_file()

    if request.method == 'POST':
        search_string = request.form.get('search_string')
        data_file = request.form.get('data_file')

        if data_file and data_file != current_file:
            update_config_file(data_file)
            current_file = data_file
            # Reload config after changing the data file
            new_config = Config()
            new_server_conf = new_config.get_server_config()
            # We're not using new_server_conf, but we need to keep this
            # assignment to maintain functionality

            if not search_string:
                return redirect(url_for('index'))

        if search_string:
            queries = [q.strip() for q in search_string.split('\n') if q.strip()]
            all_responses: List[Union[str, Dict[str, Any]]] = []
            execution_times: List[float] = []

            start_time = time.time()

            for query in queries:
                response = send_request(
                    server_address,
                    server_port,
                    SSL_ENABLED,
                    SSL_CERT,
                    SSL_KEY,
                    'create_log',
                    query,
                    DEFAULT_ALGO
                )

                if isinstance(response, dict) and 'error' in response:
                    all_responses.append(
                        f"Error for query '{query}': {response['error']}"
                    )
                else:
                    exec_time = (
                        extract_execution_time_ms(response)
                        if isinstance(response, str) else None
                    )
                    if exec_time is not None:
                        execution_times.append(exec_time)
                    all_responses.append(response)

            end_time = time.time()
            total_time = end_time - start_time
            queries_per_second = len(queries) / total_time if total_time > 0 else 0
            avg_execution_time = (
                sum(execution_times) / len(execution_times)
                if execution_times else None
            )

            performance_metrics = {
                'total_queries': len(queries),
                'total_time_seconds': round(total_time, 3),
                'queries_per_second': round(queries_per_second, 2),
                'avg_execution_time_ms': (
                    round(avg_execution_time, 3)
                    if avg_execution_time is not None else "N/A"
                ),
                'data_file': current_file
            }

            results = all_responses
        else:
            error = "Please enter one or more search strings."

    return render_template(
        'index.html',
        results=results,
        error=error,
        performance_metrics=performance_metrics,
        current_file=current_file
    )


@app.route('/read_logs')
def read_logs() -> str:
    """
    Flask route to read logs from the server.

    Returns:
        Rendered HTML page with logs or an error.
    """
    server_address = SERVER_HOST
    server_port = SERVER_PORT
    response = send_request(
        server_address,
        server_port,
        SSL_ENABLED,
        SSL_CERT,
        SSL_KEY,
        'read_logs',
        None,
        None
    )

    logs: List[Any] = []
    error: Optional[str] = None

    if isinstance(response, dict):
        if 'error' in response:
            error = response['error']
        elif isinstance(response, list):
            logs = response
    elif isinstance(response, list):
        logs = response
    else:
        error = "Unexpected response format from server"

    return render_template('read_logs.html', logs=logs, error=error)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
