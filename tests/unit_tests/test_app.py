import unittest
from unittest.mock import MagicMock, patch
from app_service import AppService  # Replace with actual import
from datetime import datetime
import uuid

class TestAppService(unittest.TestCase):

    def setUp(self):
        # Mock repositories and config
        self.mock_log_repo = MagicMock()
        self.mock_storage_repo = MagicMock()
        self.mock_config = MagicMock()

        self.mock_config.get_file_config.return_value = {'linuxpath': '/tmp/data.txt'}
        self.mock_config.get_server_config.return_value = {
            'reread_on_query': False,
            'search_mode': 'naive'
        }

        self.service = AppService(
            log_repo=self.mock_log_repo,
            storage_repo=self.mock_storage_repo,
            config=self.mock_config
        )

        self.mock_log = MagicMock()
        self.mock_log.id = str(uuid.uuid4())
        self.mock_log.query = 'test-query'
        self.mock_log.requesting_ip = '127.0.0.1'
        self.mock_log.execution_time = 0.123
        self.mock_log.timestamp = datetime.utcnow()
        self.mock_log.status = 'success'

    @patch('models.Log', autospec=True)
    def test_create_log_success(self, MockLog):
        # Arrange
        self.mock_storage_repo.data = "data"
        self.mock_storage_repo.search.return_value = ("found", 0.123)
        mock_log_instance = MockLog.return_value
        mock_log_instance.id = self.mock_log.id
        mock_log_instance.query = self.mock_log.query
        mock_log_instance.requesting_ip = self.mock_log.requesting_ip
        mock_log_instance.execution_time = self.mock_log.execution_time
        mock_log_instance.timestamp = self.mock_log.timestamp
        mock_log_instance.status = self.mock_log.status

        # Act
        result = self.service.create_log("127.0.0.1", "test-query", "naive")

        # Assert
        self.mock_storage_repo.prepare.assert_called_once_with(mode="naive")
        self.mock_log_repo.create_log.assert_called_once()
        self.assertEqual(result["status"], "success")

    @patch('models.Log', autospec=True)
    def test_create_log_with_reread_on_query(self, MockLog):
        # Arrange
        self.service.reread_on_query = True
        self.mock_storage_repo.data = None  # Simulates empty cache
        self.mock_storage_repo.search.return_value = ("found", 0.123)

        # Act
        self.service.create_log("127.0.0.1", "test-query", "naive")

        # Assert
        self.mock_storage_repo.load_file.assert_called_once_with('/tmp/data.txt')

    @patch('models.Log', autospec=True)
    def test_create_log_storage_error(self, MockLog):
        # Arrange
        self.mock_storage_repo.search.side_effect = Exception("Storage failure")

        # Act
        result = self.service.create_log("127.0.0.1", "test-query", "naive")

        # Assert
        self.assertEqual(result["status"], "error")
        self.assertIsNone(result["id"])
        self.assertEqual(result["query"], "test-query")

    def test_read_logs_success(self):
        # Arrange
        self.mock_log_repo.read_logs.return_value = [{"id": "1"}]

        # Act
        result = self.service.read_logs()

        # Assert
        self.assertEqual(result, [{"id": "1"}])

    def test_read_logs_error(self):
        # Arrange
        self.mock_log_repo.read_logs.side_effect = Exception("DB read error")

        # Act
        result = self.service.read_logs()

        # Assert
        self.assertEqual(result, [])

    @patch('models.Log', autospec=True)
    def test_create_logs_parallel_success(self, MockLog):
        # Arrange
        self.mock_storage_repo.data = "data"
        self.mock_storage_repo.search.return_value = ("found", 0.123)
        MockLog.return_value.id = self.mock_log.id
        MockLog.return_value.query = self.mock_log.query
        MockLog.return_value.requesting_ip = self.mock_log.requesting_ip
        MockLog.return_value.execution_time = self.mock_log.execution_time
        MockLog.return_value.timestamp = self.mock_log.timestamp
        MockLog.return_value.status = self.mock_log.status

        requests = [
            {"requesting_ip": "1.1.1.1", "query_string": "foo", "algo_name": "naive"},
            {"requesting_ip": "2.2.2.2", "query_string": "bar", "algo_name": "naive"}
        ]

        # Act
        results = self.service.create_logs_parallel(requests)

        # Assert
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r['status'] == 'success' for r in results))

    @patch('models.Log', autospec=True)
    def test_create_logs_parallel_partial_failure(self, MockLog):
        # Arrange
        self.mock_storage_repo.data = "data"

        def side_effect(query):
            if query == "fail":
                raise Exception("fail")
            return "found", 0.123

        self.mock_storage_repo.search.side_effect = lambda query: side_effect(query)
        MockLog.return_value.id = self.mock_log.id
        MockLog.return_value.query = self.mock_log.query
        MockLog.return_value.requesting_ip = self.mock_log.requesting_ip
        MockLog.return_value.execution_time = self.mock_log.execution_time
        MockLog.return_value.timestamp = self.mock_log.timestamp
        MockLog.return_value.status = self.mock_log.status

        requests = [
            {"requesting_ip": "1.1.1.1", "query_string": "fail", "algo_name": "naive"},
            {"requesting_ip": "2.2.2.2", "query_string": "ok", "algo_name": "naive"},
        ]

        # Act
        results = self.service.create_logs_parallel(requests)

        # Assert
        self.assertEqual(len(results), 2)
        statuses = [r["status"] for r in results]
        self.assertIn("error", statuses)
        self.assertIn("success", statuses)


if __name__ == "__main__":
    unittest.main()
