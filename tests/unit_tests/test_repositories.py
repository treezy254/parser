import unittest
import os
import json
import tempfile
from datetime import datetime
from models import Log
from repositories import LogRepository, StorageRepository 

class TestLogRepository(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.repo = LogRepository(filepath=self.temp_file.name)
        self.log = Log(id="1", query="test", requesting_ip="127.0.0.1")

    def tearDown(self):
        try:
            os.unlink(self.temp_file.name)
        except FileNotFoundError:
            pass

    def test_create_and_read_log(self):
        self.repo.create_log(self.log)
        logs = self.repo.read_logs()
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]['id'], "1")

    def test_update_log_success(self):
        self.repo.create_log(self.log)
        success = self.repo.update_log("1", {"query": "updated"})
        logs = self.repo.read_logs()
        self.assertTrue(success)
        self.assertEqual(logs[0]["query"], "updated")

    def test_update_log_failure(self):
        success = self.repo.update_log("nonexistent", {"query": "new"})
        self.assertFalse(success)

    def test_delete_log_success(self):
        self.repo.create_log(self.log)
        success = self.repo.delete_log("1")
        logs = self.repo.read_logs()
        self.assertTrue(success)
        self.assertEqual(logs, [])

    def test_delete_log_failure(self):
        success = self.repo.delete_log("not-there")
        self.assertFalse(success)


class TestStorageRepository(unittest.TestCase):
    def setUp(self):
        self.repo = StorageRepository()
        self.sample_data = ["apple", "banana", "carrot"]
        self.temp_file = tempfile.NamedTemporaryFile(mode='w+', delete=False)
        self.temp_file.write('\n'.join(self.sample_data))
        self.temp_file.close()

    def tearDown(self):
        try:
            os.unlink(self.temp_file.name)
        except FileNotFoundError:
            pass

    def test_load_file_success(self):
        result = self.repo.load_file(self.temp_file.name)
        self.assertTrue(result)
        self.assertEqual(self.repo.data, self.sample_data)

    def test_load_file_fail(self):
        result = self.repo.load_file("no_such_file.txt")
        self.assertFalse(result)

    def test_prepare_naive_mode(self):
        self.repo.load_file(self.temp_file.name)
        self.repo.prepare("naive")
        self.assertEqual(self.repo.search_data, self.sample_data)

    def test_prepare_set_mode(self):
        self.repo.load_file(self.temp_file.name)
        self.repo.prepare("set")
        self.assertEqual(self.repo.search_data, set(self.sample_data))

    def test_prepare_dict_mode(self):
        self.repo.load_file(self.temp_file.name)
        self.repo.prepare("dict")
        self.assertEqual(self.repo.search_data, {word: True for word in self.sample_data})

    def test_prepare_index_map_mode(self):
        self.repo.load_file(self.temp_file.name)
        self.repo.prepare("index_map")
        self.assertEqual(self.repo.search_data, {i: word for i, word in enumerate(self.sample_data)})

    def test_prepare_binary_mode(self):
        self.repo.load_file(self.temp_file.name)
        self.repo.prepare("binary")
        self.assertEqual(self.repo.search_data, sorted(self.sample_data))

    def test_prepare_trie_mode(self):
        self.repo.load_file(self.temp_file.name)
        self.repo.prepare("trie")
        trie = self.repo.search_data
        self.assertIn("a", trie)
        self.assertIn("#", trie["a"]["p"]["p"]["l"]["e"])

    def test_search_naive(self):
        self.repo.load_file(self.temp_file.name)
        self.repo.prepare("naive")
        result, _ = self.repo.search("banana")
        self.assertTrue(result)

    def test_search_not_found(self):
        self.repo.load_file(self.temp_file.name)
        self.repo.prepare("naive")
        result, _ = self.repo.search("not_in_list")
        self.assertFalse(result)

    def test_search_without_prepare_raises(self):
        self.repo.load_file(self.temp_file.name)
        with self.assertRaises(ValueError):
            self.repo.search("banana")

if __name__ == "__main__":
    unittest.main()
