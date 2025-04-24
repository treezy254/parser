import random
import string
import os
import json

def generate_test_file(filepath, num_lines):
    """
    Generate a test file with num_lines of random strings.
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        for _ in range(num_lines):
            line = ''.join(random.choices(string.ascii_lowercase, k=10))  # Random 10-char string
            f.write(line + '\n')

def generate_queries(filepath, num_queries, mix=True):
    """
    Generate a list of queries, half of which are existing strings from the file, and the rest are random.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f]
    
    existing = random.sample(lines, k=min(num_queries // 2, len(lines)))  # Half from file
    new = [''.join(random.choices(string.ascii_lowercase, k=10)) for _ in range(num_queries - len(existing))]  # Random new queries
    
    queries = existing + new if mix else existing
    return queries

def write_queries_to_json(queries, json_filepath):
    """
    Write queries to a JSON file.
    """
    with open(json_filepath, 'w', encoding='utf-8') as f:
        json.dump(queries, f, indent=4)
