import threading
import subprocess
import time
import os
import signal
import sys

# Adjust path if you're running from project root
sys.path.append(os.path.abspath("."))

from test_client import TestClient
from config import Config

def load_queries(relative_path):
    # Assumes relative_path like 'data/test_data/data10k_queries30.txt'
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    file_path = os.path.join(base_dir, relative_path)

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, 'r') as f:
        return [line.strip() for line in f.readlines()]


def start_server():
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../src/main.py"))
    return subprocess.Popen(
        ["python", script_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid
    )



def run_e2e_test(dataset='10k', query_count='10', algo='trie', concurrency=10):
    print("[*] Starting E2E Test")

    # Step 1: Start server
    server_process = start_server()
    time.sleep(2)  # Let the server boot up

    try:
        # Step 2: Load queries
        query_file = f"data/test_data/data{dataset}_queries{query_count}.txt"
        queries = load_queries(query_file)
        print(f"[*] Loaded {len(queries)} queries from {query_file}")

        # Step 3: Send queries
        config_path = os.path.join(os.path.dirname(__file__), "../src/config.json")
        config = Config(config_path=os.path.abspath(config_path))
        client = TestClient(config)
        client.run_concurrent_queries(queries, algo_name=algo, concurrency=concurrency)

    finally:
        # Step 4: Cleanup server process
        print("[*] Shutting down server...")
        os.killpg(os.getpgid(server_process.pid), signal.SIGTERM)
        stdout, stderr = server_process.communicate()
        print("[Server stdout]:")
        print(stdout.decode())
        print("[Server stderr]:")
        print(stderr.decode())

    print("[*] E2E Test completed")


if __name__ == "__main__":
    run_e2e_test(dataset='10k', query_count='30', algo='trie', concurrency=10)
