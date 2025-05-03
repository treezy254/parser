import ssl
import socket
import logging
import os

# Set up a logger for this module
logger = logging.getLogger(__name__)


def secure_socket(
    sock: socket.socket, certfile: str, keyfile: str, server_side: bool = True
) -> ssl.SSLSocket:
    """
    Wrap a socket with SSL/TLS encryption for secure communication.

    Args:
        sock (socket.socket): The socket object to secure.
        certfile (str): Path to the SSL certificate file (PEM format).
        keyfile (str): Path to the private key file (PEM format).
        server_side (bool, optional): Whether the socket is for a server.

    Returns:
        ssl.SSLSocket: The SSL-wrapped socket.

    Raises:
        FileNotFoundError: If either the certificate or key file is missing.
        ssl.SSLError: If there is an SSL-related error.
        Exception: For any other unexpected error during wrapping.
    """
    try:
        if not os.path.exists(certfile):
            logger.error("Certificate file not found: %s", certfile)
            raise FileNotFoundError(f"Certificate file not found: {certfile}")

        if not os.path.exists(keyfile):
            logger.error("Key file not found: %s", keyfile)
            raise FileNotFoundError(f"Key file not found: {keyfile}")

        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

        try:
            context.load_cert_chain(certfile=certfile, keyfile=keyfile)
        except ssl.SSLError as ssl_error:
            logger.error(
                "SSL error when loading certificate chain: %s",
                ssl_error
            )
            if "PEM lib" in str(ssl_error):
                logger.error(
                    "Invalid PEM format. "
                    "Check certificate and key files."
                )
            raise

        secure_sock = context.wrap_socket(sock, server_side=server_side)
        return secure_sock

    except FileNotFoundError:
        logger.error("Certificate/key file not found")
        raise
    except ssl.SSLError:
        logger.error("SSL error occurred")
        raise
    except Exception:
        logger.exception("Unexpected failure in securing socket")
        raise


def protect_buffer(data: bytes, max_payload_size: int) -> bytes:
    """
    Ensure the data buffer size does not exceed the maximum allowed payload.

    Args:
        data (bytes): The input data buffer to validate.
        max_payload_size (int): The maximum number of bytes allowed.

    Returns:
        bytes: The validated data buffer (unchanged).

    Raises:
        BufferError: If the data exceeds the max allowed size.
        TypeError: If the input data is not of type `bytes`.
    """
    if not isinstance(data, bytes):
        raise TypeError("Input data must be of type 'bytes'")

    if max_payload_size <= 0:
        logger.warning(
            "Invalid max_payload_size: %d. "
            "Defaulting to 1024.",
            max_payload_size
        )
        max_payload_size = 1024

    try:
        if len(data) > max_payload_size:
            raise BufferError(
                f"Payload too large. Max allowed: {max_payload_size} bytes"
            )
        return data

    except BufferError:
        logger.warning("Buffer exceeds max allowed size")
        raise
    except Exception:
        logger.exception("Unexpected error while protecting buffer")
        raise
