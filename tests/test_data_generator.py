import os
import random
import string
import threading
import logging

# Setup
row_counts = [10_000, 250_000, 1_000_000]
query_sizes = [1, 10, 30, 50, 100]

# Logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# Output Directory
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, '..'))
output_dir = os.path.join(root_dir, 'data', 'test_data')
os.makedirs(output_dir, exist_ok=True)

def generate_random_string(length=8):
    return ''.join(random.choices(string.ascii_lowercase, k=length))

def generate_unique_strings(n, length=8):
    seen = set()
    while len(seen) < n:
        seen.add(generate_random_string(length))
    return list(seen)

def generate_dataset(filename, num_rows):
    logging.info(f"🔨 Generating dataset {filename}...")
    filepath = os.path.join(output_dir, filename)
    values = generate_unique_strings(num_rows)
    with open(filepath, 'w') as f:
        f.writelines(f"{v}\n" for v in values)
    logging.info(f"✅ Created dataset: {filename}")
    return values

def generate_query_file(dataset_filename, value_pool):
    for q in query_sizes:
        in_count = min(q // 2, len(value_pool))
        in_data = random.sample(value_pool, in_count)
        out_data = generate_unique_strings(q - in_count)
        all_queries = in_data + out_data
        random.shuffle(all_queries)

        query_file = dataset_filename.replace('.txt', f'_queries{q}.txt')
        with open(os.path.join(output_dir, query_file), 'w') as f:
            f.writelines(f"{item}\n" for item in all_queries)
        logging.info(f"   ↪ Query file: {query_file} ({q} queries)")

def worker(count):
    filename = f"data{count//1000}k.txt"
    values = generate_dataset(filename, count)
    generate_query_file(filename, values)

# Start threads
threads = []
for count in row_counts:
    t = threading.Thread(target=worker, args=(count,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

logging.info("🎉 All done under 10 seconds (hopefully)!")
