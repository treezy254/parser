import unittest
from unittest import mock
from unittest.mock import patch, MagicMock
import ssl
import socket
import types

from security import secure_socket, protect_buffer

class TestSecureSocket(unittest.TestCase):

    @patch('ssl.create_default_context')
    @patch('os.path.exists')
    def test_secure_socket_success(self, mock_exists, mock_ssl_context):
        # Arrange mocks
        mock_exists.return_value = True
        mock_context = MagicMock()
        mock_ssl_context.return_value = mock_context
        mock_socket = MagicMock(spec=socket.socket)
        mock_wrapped_socket = MagicMock(spec=ssl.SSLSocket)
        mock_context.wrap_socket.return_value = mock_wrapped_socket

        # Act
        result = secure_socket(mock_socket, 'cert.pem', 'key.pem')

        # Assert
        self.assertEqual(result, mock_wrapped_socket)
        mock_exists.assert_any_call('cert.pem')
        mock_exists.assert_any_call('key.pem')
        mock_context.load_cert_chain.assert_called_once_with(certfile='cert.pem', keyfile='key.pem')
        mock_context.wrap_socket.assert_called_once_with(mock_socket, server_side=True)

    @patch('os.path.exists')
    def test_secure_socket_missing_cert(self, mock_exists):
        mock_exists.side_effect = [False, True]
        mock_socket = MagicMock(spec=socket.socket)
        with self.assertRaises(FileNotFoundError):
            secure_socket(mock_socket, 'missing_cert.pem', 'key.pem')

    @patch('os.path.exists')
    def test_secure_socket_missing_key(self, mock_exists):
        mock_exists.side_effect = [True, False]
        mock_socket = MagicMock(spec=socket.socket)
        with self.assertRaises(FileNotFoundError):
            secure_socket(mock_socket, 'cert.pem', 'missing_key.pem')

    @patch('ssl.create_default_context')
    @patch('os.path.exists')
    def test_secure_socket_ssl_error(self, mock_exists, mock_ssl_context):
        mock_exists.return_value = True
        mock_context = MagicMock()
        mock_ssl_context.return_value = mock_context
        mock_context.load_cert_chain.side_effect = ssl.SSLError("PEM lib error")
        mock_socket = MagicMock(spec=socket.socket)

        with self.assertRaises(ssl.SSLError):
            secure_socket(mock_socket, 'cert.pem', 'key.pem')

    @patch('ssl.create_default_context')
    @patch('os.path.exists')
    def test_secure_socket_wrap_socket_failure(self, mock_exists, mock_ssl_context):
        mock_exists.return_value = True
        mock_context = MagicMock()
        mock_ssl_context.return_value = mock_context
        mock_context.wrap_socket.side_effect = Exception("Unexpected error")
        mock_socket = MagicMock(spec=socket.socket)

        with self.assertRaises(Exception):
            secure_socket(mock_socket, 'cert.pem', 'key.pem')


class TestProtectBuffer(unittest.TestCase):

    def test_protect_buffer_success(self):
        data = b'hello'
        result = protect_buffer(data, 10)
        self.assertEqual(result, data)

    def test_protect_buffer_exceeds_size(self):
        data = b'hello world'
        max_size = 5
        with self.assertRaises(BufferError):
            protect_buffer(data, max_size)

    def test_protect_buffer_invalid_type(self):
        data = "not bytes"
        with self.assertRaises(TypeError):
            protect_buffer(data, 1024)

    def test_protect_buffer_negative_max_size(self):
        data = b'small data'
        result = protect_buffer(data, -1)
        self.assertEqual(result, data)  # Should pass since default size is 1024

    def test_protect_buffer_zero_max_size(self):
        data = b'small data'
        result = protect_buffer(data, 0)
        self.assertEqual(result, data)  # Should pass because default max size is set to 1024 internally

    def test_protect_buffer_exact_size(self):
        data = b'abcde'
        result = protect_buffer(data, 5)
        self.assertEqual(result, data)

if __name__ == '__main__':
    unittest.main()
