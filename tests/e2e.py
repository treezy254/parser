import threading
import subprocess
import time
import os
import signal
import sys
import shutil
import json

# Adjust path if you're running from project root
sys.path.append(os.path.abspath("."))

def load_queries(relative_path):
    """Load queries from the specified path with better error handling"""
    # Try different paths to find the file
    search_paths = [
        # Direct path
        relative_path,
        # Relative to current directory
        os.path.join(os.getcwd(), relative_path),
        # Relative to script directory
        os.path.join(os.path.dirname(__file__), '..', relative_path),
        # Absolute path constructed from script location
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..', relative_path))
    ]
    
    for path in search_paths:
        if os.path.exists(path):
            print(f"Found query file at: {path}")
            with open(path, 'r') as f:
                return [line.strip() for line in f.readlines()]
    
    # If we get here, we couldn't find the file
    print(f"ERROR: Couldn't find query file. Searched in:")
    for path in search_paths:
        print(f"  - {path}")
    raise FileNotFoundError(f"File not found: {relative_path}")


def ensure_data_file_exists(dataset='10k'):
    """Ensure the test data file exists, create if needed"""
    # Try different paths to find or create the data directory
    base_paths = [
        os.getcwd(),
        os.path.join(os.path.dirname(__file__), '..'),
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    ]
    
    for base_path in base_paths:
        data_dir = os.path.join(base_path, 'data', 'test_data')
        data_file = os.path.join(data_dir, f"data{dataset}.txt")
        
        if os.path.exists(data_file):
            print(f"Found data file at: {data_file}")
            return data_file
            
        # If directory doesn't exist, create it
        if not os.path.exists(data_dir):
            try:
                os.makedirs(data_dir, exist_ok=True)
                print(f"Created directory: {data_dir}")
            except Exception as e:
                print(f"Failed to create directory {data_dir}: {e}")
                continue
                
        # Create a sample data file
        try:
            # Generate a simple test data file with some sample words
            with open(data_file, 'w') as f:
                # Generate sample data
                sample_words = [
                    "apple", "banana", "cherry", "date", "elderberry", 
                    "fig", "grape", "honeydew", "kiwi", "lemon",
                    "mango", "nectarine", "orange", "pear", "quince",
                    "raspberry", "strawberry", "tangerine", "watermelon"
                ]
                
                # Add more words for larger datasets
                if dataset == '10k':
                    # For 10k dataset, we'll repeat the words with numbers
                    for i in range(1, 527):  # ~10k words
                        for word in sample_words:
                            f.write(f"{word}{i}\n")
                else:
                    # For smaller datasets, just write the words
                    for word in sample_words:
                        f.write(f"{word}\n")
                        
            print(f"Created sample data file: {data_file}")
            return data_file
        except Exception as e:
            print(f"Failed to create data file {data_file}: {e}")
    
    raise FileNotFoundError(f"Could not find or create data file for dataset {dataset}")


def ensure_query_file_exists(dataset='10k', query_count='10'):
    """Ensure the test query file exists, create if needed"""
    # Try different paths to find or create the data directory
    base_paths = [
        os.getcwd(),
        os.path.join(os.path.dirname(__file__), '..'),
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    ]
    
    for base_path in base_paths:
        data_dir = os.path.join(base_path, 'data', 'test_data')
        query_file = os.path.join(data_dir, f"data{dataset}_queries{query_count}.txt")
        
        if os.path.exists(query_file):
            print(f"Found query file at: {query_file}")
            return query_file
            
        # If directory doesn't exist, create it
        if not os.path.exists(data_dir):
            try:
                os.makedirs(data_dir, exist_ok=True)
                print(f"Created directory: {data_dir}")
            except Exception as e:
                print(f"Failed to create directory {data_dir}: {e}")
                continue
                
        # Create a sample query file
        try:
            # Generate queries based on the data file
            with open(query_file, 'w') as f:
                # Create some sample queries
                sample_queries = [
                    "apple", "banana", "cherry", "date", "elderberry",
                    "nonexistent1", "nonexistent2", "nonexistent3"
                ]
                
                # Add numbers for larger datasets
                if dataset == '10k':
                    queries = [f"{word}{i}" for i in range(1, int(query_count)//2 + 1) 
                             for word in ["apple", "banana", "nonexistent"]]
                    # Limit to requested count
                    queries = queries[:int(query_count)]
                else:
                    queries = sample_queries[:int(query_count)]
                    
                for query in queries:
                    f.write(f"{query}\n")
                        
            print(f"Created sample query file: {query_file}")
            return query_file
        except Exception as e:
            print(f"Failed to create query file {query_file}: {e}")
    
    raise FileNotFoundError(f"Could not find or create query file for dataset {dataset} with {query_count} queries")


def update_config_file(data_file_path):
    """Update the config file with the correct data file path"""
    config_paths = [
        os.path.join(os.getcwd(), 'src', 'config.json'),
        os.path.join(os.path.dirname(__file__), '..', 'src', 'config.json'),
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'config.json'))
    ]
    
    for config_path in config_paths:
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                # Update the file path
                if 'file' in config:
                    config['file']['linuxpath'] = data_file_path
                else:
                    config['file'] = {'linuxpath': data_file_path}
                
                # Write back the updated config
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=4)
                
                print(f"Updated config file at: {config_path}")
                return config_path
            except Exception as e:
                print(f"Failed to update config file {config_path}: {e}")
    
    raise FileNotFoundError("Could not find or update config file")


def start_server():
    """Start the server with better path handling"""
    script_paths = [
        os.path.join(os.getcwd(), 'src', 'main.py'),
        os.path.join(os.path.dirname(__file__), '..', 'src', 'main.py'),
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'main.py'))
    ]
    
    for script_path in script_paths:
        if os.path.exists(script_path):
            print(f"Starting server using script at: {script_path}")
            server_process = subprocess.Popen(
                ["python", script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
            return server_process
    
    raise FileNotFoundError("Could not find main.py server script")


def run_e2e_test(dataset='10k', query_count='10', algo='trie', concurrency=10):
    print("[*] Starting E2E Test")
    
    # Step 0: Set up the test environment
    try:
        # Ensure data file exists
        data_file = ensure_data_file_exists(dataset)
        
        # Ensure query file exists
        query_file = ensure_query_file_exists(dataset, query_count)
        
        # Update config file
        config_path = update_config_file(data_file)
        
        # Now import the necessary modules
        from test_client import TestClient
        from config import Config
        
        # Step 1: Start server
        server_process = start_server()
        print("[*] Server started, waiting for it to initialize...")
        time.sleep(2)  # Let the server boot up
        
        try:
            # Step 2: Load queries
            query_relative_path = f"data/test_data/data{dataset}_queries{query_count}.txt"
            queries = load_queries(query_file)
            print(f"[*] Loaded {len(queries)} queries from {query_file}")
            
            # Step 3: Send queries
            config = Config(config_path=config_path)
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
            
    except Exception as e:
        print(f"[!] E2E Test failed: {e}")
        raise
        
    print("[*] E2E Test completed")


if __name__ == "__main__":
    run_e2e_test(dataset='10k', query_count='30', algo='trie', concurrency=10)