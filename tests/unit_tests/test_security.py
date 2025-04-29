import unittest
from unittest import mock
from io import BytesIO
import ssl
import socket
import tempfile
import os

from your_module import secure_socket, protect_buffer  # Replace with actual module name


class TestSecureSocket(unittest.TestCase):
    def setUp(self):
        # Generate dummy cert and key for testing
        self.certfile = tempfile.NamedTemporaryFile(delete=False, suffix=".pem")
        self.keyfile = tempfile.NamedTemporaryFile(delete=False, suffix=".key")

        self.certfile.write(b"""-----BEGIN CERTIFICATE-----
MIIBjTCCATegAwIBAgIUHps5T3d06IjZa6rJqMSqAKdWGiMwCgYIKoZIzj0EAwIw
EjEQMA4GA1UEAwwHZXhhbXBsZTAeFw0yNTA0MjgxODAxMTFaFw0yNjA0MjgxODAx
MTFaMBIxEDAOBgNVBAMMB2V4YW1wbGUwWTATBgcqhkjOPQIBBggqhkjOPQMBBwNC
AAQIHVu7ef7RukYcH3HMyBfhs+pN7dx6wNplMZ+crZlaUcfGExkFBNyXkMZpvHUI
JtIYBhZcIOYZvSgeu0AXOIgNo1MwUTAdBgNVHQ4EFgQU7NvhzazN+ul6IKEDRuEK
ZQPXp7kwHwYDVR0jBBgwFoAU7NvhzazN+ul6IKEDRuEKZQPXp7kwDwYDVR0TAQH/
BAUwAwEB/zAKBggqhkjOPQQDAgNHADBEAiAztUPVbTgfYvxfQBLJ1H3wE9kgbf97
++/ZfEMO6mPU1gIgMz1cS3S0pyP+u6u9xLDlaS1oISXEbczMw3bTqBG/7dw=
-----END CERTIFICATE-----""")
        self.certfile.close()

        self.keyfile.write(b"""-----BEGIN EC PRIVATE KEY-----
MHcCAQEEIAkZZL64JJDDbLMTlGcODxwWaDz0ttRgzKczq3Y0qucDoAoGCCqGSM49
AwEHoUQDQgAECB1bu3n+0bpGHB9xzMH37x+pN7dx6wNplMZ+crZlaUcfGExkFBNy
XkMZpvHUIJtIYBhZcIOYZvSgeu0AXOIgNw==
-----END EC PRIVATE KEY-----""")
        self.keyfile.close()

    def tearDown(self):
        os.unlink(self.certfile.name)
        os.unlink(self.keyfile.name)

    def test_secure_socket_success(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Wrap socket (won't actually start listening or connecting)
        wrapped_socket = secure_socket(server_socket, self.certfile.name, self.keyfile.name)
        self.assertIsInstance(wrapped_socket, ssl.SSLSocket)
        wrapped_socket.close()

    def test_secure_socket_invalid_cert(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as bad_cert:
            bad_cert.write("INVALID CERT")
        with self.assertRaises(ssl.SSLError):
            secure_socket(socket.socket(), bad_cert.name, self.keyfile.name)
        os.unlink(bad_cert.name)

    def test_secure_socket_missing_certfile(self):
        with self.assertRaises(FileNotFoundError):
            secure_socket(socket.socket(), "missing_cert.pem", self.keyfile.name)

    def test_secure_socket_wrap_error(self):
        # Patch wrap_socket to raise an error
        with mock.patch("ssl.SSLContext.wrap_socket", side_effect=ssl.SSLError("wrap failed")):
            with self.assertRaises(ssl.SSLError):
                secure_socket(socket.socket(), self.certfile.name, self.keyfile.name)


class TestProtectBuffer(unittest.TestCase):
    def test_valid_data_under_limit(self):
        data = b"hello"
        result = protect_buffer(data, max_payload_size=10)
        self.assertEqual(result, data)

    def test_data_exactly_at_limit(self):
        data = b"123456"
        result = protect_buffer(data, max_payload_size=6)
        self.assertEqual(result, data)

    def test_data_exceeds_limit_raises(self):
        data = b"abcdef"
        with self.assertRaises(BufferError):
            protect_buffer(data, max_payload_size=5)

    def test_empty_data(self):
        result = protect_buffer(b"", max_payload_size=1)
        self.assertEqual(result, b"")

    def test_large_data_under_limit(self):
        large_data = b"x" * 100_000
        result = protect_buffer(large_data, max_payload_size=100_000)
        self.assertEqual(result, large_data)

    def test_non_bytes_input_raises_typeerror(self):
        with self.assertRaises(TypeError):
            protect_buffer("not_bytes", max_payload_size=100)  # type: ignore

    def test_negative_payload_size_raises(self):
        with self.assertRaises(BufferError):
            protect_buffer(b"data", max_payload_size=-1)


if __name__ == "__main__":
    unittest.main()
