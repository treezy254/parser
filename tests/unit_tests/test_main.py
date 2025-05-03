import unittest
from unittest.mock import MagicMock, patch, call
import json
import socket
import datetime
from main import client_handler, format_tcp_response


class TestClientHandler(unittest.TestCase):

    def setUp(self):
        self.conn = MagicMock(spec=socket.socket)
        self.addr = ('127.0.0.1', 12345)

        self.config = MagicMock()
        self.config.get_server_config.return_value = {'max_payload_size': 1024}

        self.app_service = MagicMock()

    @patch('main.protect_buffer')
    def test_create_log_success(self, mock_protect):
        request_data = json.dumps({
            'action': 'create_log',
            'query': 'search this',
            'algo': 'naive'
        }).encode()

        mock_protect.return_value = request_data
        self.conn.recv.return_value = request_data

        response_data = {
            'id': 'abc-123',
            'query': 'search this',
            'requesting_ip': '127.0.0.1',
            'execution_time': 0.1,
            'timestamp': '2024-01-01T00:00:00',
            'status': 'STRING_EXISTS'
        }

        self.app_service.create_log.return_value = response_data

        # Call the function under test
        client_handler(self.conn, self.addr, self.app_service, self.config)

        # Verify app_service was called correctly
        self.app_service.create_log.assert_called_once_with(
            requesting_ip='127.0.0.1',
            query_string='search this',
            algo_name='naive'
        )
        
        # Verify formatted response was sent
        expected_response = format_tcp_response(response_data)
        self.conn.sendall.assert_called_once_with(expected_response)
        self.conn.close.assert_called_once()

    @patch('main.protect_buffer')
    def test_create_log_not_found(self, mock_protect):
        request_data = json.dumps({
            'action': 'create_log',
            'query': 'not found string',
            'algo': 'naive'
        }).encode()

        mock_protect.return_value = request_data
        self.conn.recv.return_value = request_data

        response_data = {
            'id': 'abc-456',
            'query': 'not found string',
            'requesting_ip': '127.0.0.1',
            'execution_time': 0.05,
            'timestamp': '2024-01-01T00:00:00',
            'status': 'STRING_NOT_FOUND'
        }

        self.app_service.create_log.return_value = response_data

        client_handler(self.conn, self.addr, self.app_service, self.config)

        expected_response = format_tcp_response(response_data)
        self.conn.sendall.assert_called_once_with(expected_response)

    @patch('main.protect_buffer')
    def test_read_logs_success(self, mock_protect):
        request_data = json.dumps({'action': 'read_logs'}).encode()
        mock_protect.return_value = request_data
        self.conn.recv.return_value = request_data

        logs = [
            {
                'id': 'abc',
                'query': 'test1',
                'requesting_ip': '127.0.0.1',
                'execution_time': 0.1,
                'timestamp': '2024-01-01T00:00:00',
                'status': 'STRING_EXISTS'
            },
            {
                'id': 'def',
                'query': 'test2',
                'requesting_ip': '127.0.0.1',
                'execution_time': 0.2,
                'timestamp': '2024-01-01T00:01:00',
                'status': 'STRING_NOT_FOUND'
            }
        ]
        self.app_service.read_logs.return_value = logs

        client_handler(self.conn, self.addr, self.app_service, self.config)

        # For read_logs, the response should be the JSON-encoded logs
        self.conn.sendall.assert_called_once_with(json.dumps(logs).encode())

    @patch('main.protect_buffer')
    def test_invalid_action(self, mock_protect):
        request_data = json.dumps({'action': 'invalid'}).encode()
        mock_protect.return_value = request_data
        self.conn.recv.return_value = request_data

        client_handler(self.conn, self.addr, self.app_service, self.config)

        # Check that the formatted error response was sent
        call_args = self.conn.sendall.call_args[0][0]
        # The response should start with "ERROR: Invalid action"
        self.assertTrue(call_args.startswith(b"ERROR: Invalid action"))

    def test_json_decode_error(self):
        self.conn.recv.return_value = b'{not valid json'

        client_handler(self.conn, self.addr, self.app_service, self.config)

        # Check that the formatted error response was sent
        call_args = self.conn.sendall.call_args[0][0]
        # The response should start with "ERROR: Invalid JSON format"
        self.assertTrue(b"ERROR: Invalid JSON format" in call_args)

    @patch('main.protect_buffer')
    def test_missing_key_error(self, mock_protect):
        request_data = json.dumps({'action': 'create_log'}).encode()
        mock_protect.return_value = request_data
        self.conn.recv.return_value = request_data

        client_handler(self.conn, self.addr, self.app_service, self.config)

        # Check that the formatted error response was sent
        call_args = self.conn.sendall.call_args[0][0]
        # The response should contain "ERROR: Missing key"
        self.assertTrue(b"ERROR: Missing key" in call_args)

    @patch('main.protect_buffer')
    def test_general_exception(self, mock_protect):
        request_data = json.dumps({'action': 'read_logs'}).encode()
        mock_protect.return_value = request_data
        self.conn.recv.return_value = request_data

        self.app_service.read_logs.side_effect = Exception("Something went wrong")

        client_handler(self.conn, self.addr, self.app_service, self.config)

        # Check that the formatted error response was sent
        call_args = self.conn.sendall.call_args[0][0]
        # The response should contain "ERROR: Something went wrong"
        self.assertTrue(b"ERROR: Something went wrong" in call_args)

    @patch('main.datetime')
    def test_format_tcp_response_string_exists(self, mock_datetime):
        # Mock datetime to return a fixed value
        mock_datetime.datetime.now.return_value = datetime.datetime(2024, 1, 1, 12, 0, 0)
        
        # Test STRING_EXISTS response
        result = {
            'status': 'STRING_EXISTS',
            'query': 'test query',
            'requesting_ip': '127.0.0.1',
            'execution_time': 0.123,
            'timestamp': '2024-01-01T12:00:00',
            'id': 'abc-123'
        }
        
        response = format_tcp_response(result)
        
        expected = (
            "STRING EXISTS\n"
            "DEBUG:\n"
            "  Query: test query\n"
            "  Requesting IP: 127.0.0.1\n"
            "  Execution Time: 0.123s\n"
            "  Timestamp: 2024-01-01T12:00:00\n"
            "  Log ID: abc-123\n"
        ).encode()
        
        self.assertEqual(response, expected)

    def test_format_tcp_response_string_not_found(self):
        # Test STRING_NOT_FOUND response
        result = {
            'status': 'STRING_NOT_FOUND',
            'query': 'missing query',
            'requesting_ip': '192.168.1.1',
            'execution_time': 0.05,
            'timestamp': '2024-01-02T14:30:00',
            'id': 'def-456'
        }
        
        response = format_tcp_response(result)
        
        expected = (
            "STRING NOT_FOUND\n"
            "DEBUG:\n"
            "  Query: missing query\n"
            "  Requesting IP: 192.168.1.1\n"
            "  Execution Time: 0.05s\n"
            "  Timestamp: 2024-01-02T14:30:00\n"
            "  Log ID: def-456\n"
        ).encode()
        
        self.assertEqual(response, expected)

    def test_format_tcp_response_error(self):
        # Test error response
        result = {
            'status': 'error',
            'error': 'Test error message',
            'query': 'error query',
            'requesting_ip': '10.0.0.1',
            'execution_time': 0.01,
            'timestamp': '2024-01-03T09:15:00',
            'id': None
        }
        
        response = format_tcp_response(result)
        
        expected = (
            "ERROR: Test error message\n"
            "DEBUG:\n"
            "  Query: error query\n"
            "  Requesting IP: 10.0.0.1\n"
            "  Execution Time: 0.01s\n"
            "  Timestamp: 2024-01-03T09:15:00\n"
            "  Log ID: None\n"
        ).encode()
        
        self.assertEqual(response, expected)


class TestMainServer(unittest.TestCase):

    @patch('main.secure_socket')
    @patch('main.socket.socket')
    @patch('main.Config')
    @patch('main.AppService')
    @patch('main.LogRepository')
    @patch('main.StorageRepository')
    def test_main_server_ssl_setup(
        self, mock_storage_repo, mock_log_repo, mock_app_service,
        mock_config, mock_socket_class, mock_secure_socket
    ):
        from main import main  # Re-import to patch __main__

        mock_sock = MagicMock()
        mock_socket_class.return_value = mock_sock

        mock_conf_instance = MagicMock()
        mock_conf_instance.get_server_config.return_value = {
            'port': 9999,
            'ssl_enabled': True,
            'ssl_cert': 'cert.pem',
            'ssl_key': 'key.pem'
        }
        mock_config.return_value = mock_conf_instance
        mock_secure_socket.return_value = mock_sock

        mock_sock.accept.side_effect = KeyboardInterrupt  # stop after first loop

        with self.assertRaises(SystemExit):
            main()

        mock_socket_class.assert_called_once()
        mock_secure_socket.assert_called_once_with(mock_sock, 'cert.pem', 'key.pem')
        mock_sock.bind.assert_called_with(('0.0.0.0', 9999))
        mock_sock.listen.assert_called_once()


if __name__ == "__main__":
    unittest.main()