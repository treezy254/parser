import socket
import threading
import json

from config import Config
from repositories import LogRepository, StorageRepository
from services import SearchService, AppService
from security import secure_socket, protect_buffer

def client_handler(conn, addr, app_service, config):
    max_payload_size = config.get_server_config()['max_payload_size']
        try:
                data = conn.recv(max_payload_size)
                        data = protect_buffer(data, max_payload_size)
                                request = json.loads(data.decode())

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
                                                                                                                                                                                            except Exception as e:
                                                                                                                                                                                                    conn.sendall(json.dumps({'error': str(e)}).encode())
                                                                                                                                                                                                        finally:
                                                                                                                                                                                                                conn.close()

                                                                                                                                                                                                                def main():
                                                                                                                                                                                                                    config = Config()
                                                                                                                                                                                                                        server_conf = config.get_server_config()
                                                                                                                                                                                                                            port = server_conf['port']
                                                                                                                                                                                                                                ssl_enabled = server_conf['ssl_enabled']
                                                                                                                                                                                                                                    certfile = server_conf['ssl_cert']
                                                                                                                                                                                                                                        keyfile = server_conf['ssl_key']

                                                                                                                                                                                                                                            log_repo = LogRepository()
                                                                                                                                                                                                                                                storage_repo = StorageRepository()
                                                                                                                                                                                                                                                    search_service = SearchService()
                                                                                                                                                                                                                                                        app_service = AppService(log_repo, storage_repo, search_service, config)

                                                                                                                                                                                                                                                            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                                                                                                                                                                                                                                                sock.bind(('0.0.0.0', port))
                                                                                                                                                                                                                                                                    sock.listen(5)
                                                                                                                                                                                                                                                                        print(f"[*] Listening on port {port}...")

                                                                                                                                                                                                                                                                            if ssl_enabled:
                                                                                                                                                                                                                                                                                    sock = secure_socket(sock, certfile, keyfile)
                                                                                                                                                                                                                                                                                            print("[*] SSL enabled")

                                                                                                                                                                                                                                                                                                while True:
                                                                                                                                                                                                                                                                                                        conn, addr = sock.accept()
                                                                                                                                                                                                                                                                                                                print(f"[*] Connection from {addr}")
                                                                                                                                                                                                                                                                                                                        threading.Thread(target=client_handler, args=(conn, addr, app_service, config)).start()

                                                                                                                                                                                                                                                                                                                        if __name__ == "__main__":
                                                                                                                                                                                                                                                                                                                            main()