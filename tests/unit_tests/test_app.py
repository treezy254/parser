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
        self.mock_storage_repo.search.return_value = (True, 0.123)  # Search found something

        # Prepare a Log mock that will be returned after create_log
        mock_log = MagicMock()
        mock_log.id = "test-uuid"
        mock_log.query = "test query"
        mock_log.requesting_ip = "127.0.0.1"
        mock_log.execution_time = 0.123
        mock_log.timestamp = datetime.now()

        # Patch uuid.uuid4 to return a predictable ID
        with patch("uuid.uuid4", return_value="test-uuid"), \
             patch("models.Log", return_value=mock_log) as mock_log_class:

            # Make create method properly set timestamp and other properties
            def mock_create(found, exec_time):
                mock_log.found = found
                mock_log.execution_time = exec_time
                mock_log.timestamp = datetime.now()
            
            mock_log.create = mock_create

            result = self.service.create_log("127.0.0.1", "test query", "naive")

            # Assert the result is as expected
            self.assertEqual(result["id"], "test-uuid")
            self.assertEqual(result["query"], "test query")
            self.assertEqual(result["requesting_ip"], "127.0.0.1")
            self.assertEqual(result["status"], "STRING_EXISTS")
            self.assertIsNotNone(result["timestamp"])

    def test_create_log_load_file_failure(self):
        self.mock_storage_repo.data = None
        self.mock_storage_repo.load_file.return_value = False

        result = self.service.create_log("127.0.0.1", "query", "naive")

        self.assertEqual(result["status"], "error")
        self.assertIn("could not be loaded", result["error"])

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

        # First call returns success, second call throws exception
        self.mock_storage_repo.search.side_effect = [(True, 0.123), Exception("fail")]

        # Mock log objects
        mock_log1 = MagicMock()
        mock_log1.id = "uuid-1"
        mock_log1.query = "q1"
        mock_log1.requesting_ip = "ip1"
        mock_log1.execution_time = 0.123
        mock_log1.timestamp = datetime.now()
        
        mock_log2 = MagicMock()
        mock_log2.id = "uuid-2"
        mock_log2.query = "q2"
        mock_log2.requesting_ip = "ip2"

        # Patch uuid.uuid4 and Log constructor
        with patch("uuid.uuid4", side_effect=["uuid-1", "uuid-2"]), \
             patch("models.Log", side_effect=[mock_log1, mock_log2]) as mock_log_class:
            
            # Define a create method that properly sets attributes
            def mock_create1(found, exec_time):
                mock_log1.found = found
                mock_log1.execution_time = exec_time
                mock_log1.timestamp = datetime.now()
            
            mock_log1.create = mock_create1
            
            def mock_create2(found, exec_time):
                mock_log2.found = found
                mock_log2.execution_time = exec_time
                mock_log2.timestamp = datetime.now()
            
            mock_log2.create = mock_create2

            requests = [
                {"requesting_ip": "ip1", "query_string": "q1", "algo_name": "naive"},
                {"requesting_ip": "ip2", "query_string": "q2", "algo_name": "naive"}
            ]

            # Force execute the first successful search, then fail the second
            def side_effect_create_log(*args, **kwargs):
                if args[1] == "q1":  # First request succeeds
                    return {
                        "id": "uuid-1",
                        "query": "q1",
                        "requesting_ip": "ip1",
                        "execution_time": 0.123,
                        "timestamp": mock_log1.timestamp.isoformat(),
                        "status": "success"
                    }
                else:  # Second request fails
                    raise Exception("fail")
            
            # Mock the create_log method for deterministic results
            with patch.object(self.service, 'create_log', side_effect=side_effect_create_log):
                result = self.service.create_logs_parallel(requests)
                
                # We should have 2 results - one success and one error
                self.assertEqual(len(result), 2)
                
                # Check that we have at least one success and one error
                success_results = [r for r in result if r.get("status") == "success"]
                error_results = [r for r in result if r.get("status") == "error"]
                
                self.assertEqual(len(success_results), 1)
                self.assertEqual(len(error_results), 1)

    def test_validate_file_path_relative_converted(self):
        # Patch os.getcwd and os.path.isabs
        with patch("os.getcwd", return_value="/home/user/project"), \
             patch("os.path.isabs", return_value=False), \
             patch("os.path.abspath", return_value="/home/user/project/data.txt"):
            self.service._validate_file_path()
            self.assertTrue(self.service.file_path.endswith("data.txt"))

if __name__ == '__main__':
    unittest.main()
