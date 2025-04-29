import socket
import ssl
import threading
import json
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from security import secure_socket, protect_buffer
from config import Config

class TestClient:
    def __init__(self, config):
        self.config = config
        self.server_conf = config.get_server_config()
        self.host = 'localhost'
        self.port = self.server_conf['port']
        self.ssl_enabled = self.server_conf['ssl_enabled']
        self.cert = self.server_conf['ssl_cert']
        self.key = self.server_conf['ssl_key']
        self.max_payload_size = self.server_conf['max_payload_size']

    def send_request(self, action, query, algo):
        try:
            sock = socket.create_connection((self.host, self.port))
            if self.ssl_enabled:
                context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
                context.load_cert_chain(certfile=self.cert, keyfile=self.key)
                sock = context.wrap_socket(sock, server_hostname=self.host)

            request = {
                "action": action,
                "query": query,
                "algo": algo
            }
            data = json.dumps(request).encode()
            data = protect_buffer(data, self.max_payload_size)

            sock.sendall(data)
            response = sock.recv(self.max_payload_size)
            print(f"[Response] {response.decode()}")
            sock.close()
        except Exception as e:
            print(f"[Error] {e}")

    def run_concurrent_queries(self, queries, algo_name, concurrency=10):
        threads = []
        for query in queries:
            t = threading.Thread(target=self.send_request, args=('create_log', query, algo_name))
            threads.append(t)
            t.start()
            if len(threads) >= concurrency:
                for t in threads:
                    t.join()
                threads = []
