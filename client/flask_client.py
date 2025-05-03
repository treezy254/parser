# flask_client.py
import os
import sys
import json
import socket
import ssl
from flask import Flask, render_template, request

# Adjust path to include the 'src' directory where config and security modules are
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from config import Config
from security import protect_buffer

app = Flask(__name__)
config = Config()
server_conf = config.get_server_config()
SERVER_HOST = 'localhost'  # Default server host
SERVER_PORT = server_conf['port']
SSL_ENABLED = server_conf['ssl_enabled']
SSL_CERT = server_conf.get('ssl_cert')
SSL_KEY = server_conf.get('ssl_key')
MAX_PAYLOAD_SIZE = server_conf['max_payload_size']
DEFAULT_ALGO = 'trie' # Assuming default algorithm

def send_request(server_address, port, ssl_enabled, certfile, keyfile, action, query, algo):
    """Sends a request to the server and returns the response."""
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

        # Receive response data
        response_data = sock.recv(MAX_PAYLOAD_SIZE)
        sock.close()

        # Handle different response formats based on action
        if action == 'create_log':
            # For create_log, response is a formatted string
            return response_data.decode()
        else:
            # For read_logs and other actions, response is JSON
            try:
                return json.loads(response_data.decode())
            except json.JSONDecodeError:
                return {'error': 'Invalid JSON response from server', 'raw_response': response_data.decode()}
    except Exception as e:
        return {'error': str(e)}

@app.route('/', methods=['GET', 'POST'])
def index():
    results = []
    error = None
    server_address = SERVER_HOST  # Initialize with default
    server_port = SERVER_PORT      # Initialize with default

    if request.method == 'POST':
        search_string = request.form.get('search_string')

        if search_string:
            queries = [q.strip() for q in search_string.split('\n') if q.strip()]
            all_responses = []
            for query in queries:
                response = send_request(server_address, server_port, SSL_ENABLED, SSL_CERT, SSL_KEY,
                                        'create_log', query, DEFAULT_ALGO)

                # Format the response for display
                if isinstance(response, dict) and 'error' in response:
                    all_responses.append(f"Error for query '{query}': {response['error']}")
                else:
                    # Assuming the server returns the formatted debug string
                    all_responses.append(response)

            results = all_responses
        else:
            error = "Please enter one or more search strings."

    return render_template('index.html', results=results, error=error)

@app.route('/read_logs')
def read_logs():
    server_address = SERVER_HOST
    server_port = SERVER_PORT
    response = send_request(server_address, server_port, SSL_ENABLED, SSL_CERT, SSL_KEY, 'read_logs', None, None)

    logs = []
    error = None

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