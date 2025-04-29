import unittest
from unittest.mock import MagicMock, patch, call
import json
import socket
from main import client_handler  


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
            'status': 'success'
        }

        self.app_service.create_log.return_value = response_data

        client_handler(self.conn, self.addr, self.app_service, self.config)

        self.app_service.create_log.assert_called_once_with(
            requesting_ip='127.0.0.1',
            query_string='search this',
            algo_name='naive'
        )
        self.conn.sendall.assert_called_once_with(json.dumps(response_data).encode())
        self.conn.close.assert_called_once()

    @patch('main.protect_buffer')
    def test_read_logs_success(self, mock_protect):
        request_data = json.dumps({'action': 'read_logs'}).encode()
        mock_protect.return_value = request_data
        self.conn.recv.return_value = request_data

        logs = [{'id': 'abc', 'query': 'test'}]
        self.app_service.read_logs.return_value = logs

        client_handler(self.conn, self.addr, self.app_service, self.config)

        self.conn.sendall.assert_called_once_with(json.dumps(logs).encode())

    @patch('main.protect_buffer')
    def test_invalid_action(self, mock_protect):
        request_data = json.dumps({'action': 'invalid'}).encode()
        mock_protect.return_value = request_data
        self.conn.recv.return_value = request_data

        client_handler(self.conn, self.addr, self.app_service, self.config)

        self.conn.sendall.assert_called_once_with(json.dumps({'error': 'Invalid action'}).encode())

    def test_json_decode_error(self):
        self.conn.recv.return_value = b'{not valid json'

        client_handler(self.conn, self.addr, self.app_service, self.config)

        self.conn.sendall.assert_called_once_with(json.dumps({'error': 'Invalid JSON format'}).encode())

    @patch('main.protect_buffer')
    def test_missing_key_error(self, mock_protect):
        request_data = json.dumps({'action': 'create_log'}).encode()
        mock_protect.return_value = request_data
        self.conn.recv.return_value = request_data

        client_handler(self.conn, self.addr, self.app_service, self.config)

        self.conn.sendall.assert_called_once()
        sent_data = json.loads(self.conn.sendall.call_args[0][0].decode())
        self.assertTrue('Missing key' in sent_data['error'])

    @patch('main.protect_buffer')
    def test_general_exception(self, mock_protect):
        request_data = json.dumps({'action': 'read_logs'}).encode()
        mock_protect.return_value = request_data
        self.conn.recv.return_value = request_data

        self.app_service.read_logs.side_effect = Exception("Something went wrong")

        client_handler(self.conn, self.addr, self.app_service, self.config)

        sent_data = json.loads(self.conn.sendall.call_args[0][0].decode())
        self.assertEqual(sent_data['error'], 'Something went wrong')


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
