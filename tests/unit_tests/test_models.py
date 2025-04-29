import unittest
from datetime import datetime
from log_module import Log  # Replace with actual module name if different
import threading

class TestLog(unittest.TestCase):

    def test_normal_initialization(self):
        log = Log(id="1", query="SELECT * FROM table", requesting_ip="127.0.0.1")
        self.assertEqual(log.query, "SELECT * FROM table")
        self.assertIsNone(log.execution_time)
        self.assertIsNone(log.timestamp)
        self.assertIsNone(log.status)

    def test_query_exactly_1024_bytes(self):
        query = "a" * 1024
        log = Log(id="2", query=query, requesting_ip="127.0.0.1")
        self.assertEqual(len(log.query.encode("utf-8")), 1024)

    def test_query_exceeds_1024_bytes(self):
        query = "a" * 1100
        log = Log(id="3", query=query, requesting_ip="127.0.0.1")
        self.assertLessEqual(len(log.query.encode("utf-8")), 1024)

    def test_query_with_multibyte_characters(self):
        query = "😊" * 300  # Each emoji ~4 bytes
        log = Log(id="4", query=query, requesting_ip="127.0.0.1")
        self.assertLessEqual(len(log.query.encode("utf-8")), 1024)

    def test_create_method_updates_fields(self):
        log = Log(id="5", query="test", requesting_ip="192.168.0.1")
        log.create(found=True, exec_time=1.23)
        self.assertTrue(log.status)
        self.assertEqual(log.execution_time, 1.23)
        self.assertIsInstance(log.timestamp, datetime)

    def test_thread_safety_in_create(self):
        log = Log(id="6", query="test", requesting_ip="10.0.0.1")

        def update_log():
            log.create(found=False, exec_time=0.5)

        threads = [threading.Thread(target=update_log) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertIn(log.status, [True, False])
        self.assertIsInstance(log.execution_time, float)
        self.assertIsInstance(log.timestamp, datetime)

    def test_query_encoding_error_handling(self):
        class BadStr:
            def encode(self, *_):
                raise UnicodeEncodeError("utf-8", "x", 0, 1, "reason")

        log = Log(id="7", query=BadStr(), requesting_ip="127.0.0.1")
        # If exception is raised, test will fail
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()
