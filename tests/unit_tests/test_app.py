import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
from app import AppService 
from models import Log

class TestAppService(unittest.TestCase):
    def setUp(self):
        # Mock dependencies
        self.mock_log_repo = MagicMock()
        self.mock_storage_repo = MagicMock()
        self.mock_config = MagicMock()

        self.mock_config.get_file_config.return_value = {'linuxpath': 'data.txt'}
        self.mock_config.get_server_config.return_value = {
            'reread_on_query': False,
            'search_mode': 'naive'
        }

        # Patch os.path.exists to simulate file existence
        patcher = patch('os.path.exists', return_value=True)
        self.addCleanup(patcher.stop)
        self.mock_exists = patcher.start()

        self.service = AppService(
            log_repo=self.mock_log_repo,
            storage_repo=self.mock_storage_repo,
            config=self.mock_config
        )

    def test_create_log_success(self):
        # Setup mocks
        self.mock_storage_repo.data = "some_data"
        self.mock_storage_repo.load_file.return_value = True
        self.mock_storage_repo.prepare.return_value = None
        self.mock_storage_repo.search.return_value = ("result", 0.123)

        # Patch uuid and timestamp
        with patch("uuid.uuid4", return_value="test-uuid"), \
             patch("models.Log.create") as mock_log_create:

            result = self.service.create_log("127.0.0.1", "test query", "naive")

            self.assertEqual(result["id"], "test-uuid")
            self.assertEqual(result["query"], "test query")
            self.assertEqual(result["requesting_ip"], "127.0.0.1")
            self.assertEqual(result["status"], "success")

    def test_create_log_load_file_failure(self):
        self.mock_storage_repo.data = None
        self.mock_storage_repo.load_file.return_value = False

        result = self.service.create_log("127.0.0.1", "query", "naive")

        self.assertEqual(result["status"], "error")
        self.assertIn("couldn't be loaded", result["error"])

    def test_create_log_no_data_loaded(self):
        self.mock_storage_repo.data = None
        self.mock_storage_repo.load_file.return_value = True  # even if file loaded, still None

        result = self.service.create_log("127.0.0.1", "query", "naive")

        self.assertEqual(result["status"], "error")
        self.assertIn("No data loaded", result["error"])

    def test_create_log_prepare_raises_value_error(self):
        self.mock_storage_repo.data = "some_data"
        self.mock_storage_repo.load_file.return_value = True
        self.mock_storage_repo.prepare.side_effect = ValueError("invalid algo")

        result = self.service.create_log("127.0.0.1", "query", "naive")

        self.assertEqual(result["status"], "error")
        self.assertIn("Failed to prepare storage", result["error"])

    def test_create_log_search_raises_exception(self):
        self.mock_storage_repo.data = "some_data"
        self.mock_storage_repo.load_file.return_value = True
        self.mock_storage_repo.prepare.return_value = None
        self.mock_storage_repo.search.side_effect = Exception("search failed")

        result = self.service.create_log("127.0.0.1", "query", "naive")

        self.assertEqual(result["status"], "error")
        self.assertIn("Search operation failed", result["error"])

    def test_read_logs_success(self):
        self.mock_log_repo.read_logs.return_value = [{"id": "1", "query": "x"}]
        result = self.service.read_logs()
        self.assertEqual(result, [{"id": "1", "query": "x"}])

    def test_read_logs_failure(self):
        self.mock_log_repo.read_logs.side_effect = Exception("read error")
        result = self.service.read_logs()
        self.assertEqual(result, [])

    def test_create_logs_parallel_mixed_results(self):
        self.mock_storage_repo.data = "some_data"
        self.mock_storage_repo.load_file.return_value = True
        self.mock_storage_repo.prepare.return_value = None
        self.mock_storage_repo.search.side_effect = [("result", 0.123), Exception("fail")]

        with patch("uuid.uuid4", side_effect=["uuid-1", "uuid-2"]), \
             patch("models.Log.create"):
            requests = [
                {"requesting_ip": "ip1", "query_string": "q1", "algo_name": "naive"},
                {"requesting_ip": "ip2", "query_string": "q2", "algo_name": "naive"}
            ]

            result = self.service.create_logs_parallel(requests)
            self.assertEqual(len(result), 2)
            self.assertTrue(any(r["status"] == "success" for r in result))
            self.assertTrue(any(r["status"] == "error" for r in result))

    def test_validate_file_path_relative_converted(self):
        # Patch os.getcwd and os.path.isabs
        with patch("os.getcwd", return_value="/home/user/project"), \
             patch("os.path.isabs", return_value=False), \
             patch("os.path.abspath", return_value="/home/user/project/data.txt"):
            self.service._validate_file_path()
            self.assertTrue(self.service.file_path.endswith("data.txt"))

if __name__ == '__main__':
    unittest.main()
