import ssl
import logging

# Set up logging
logger = logging.getLogger(__name__)

def secure_socket(sock: ssl.SSLSocket, certfile: str, keyfile: str) -> ssl.SSLSocket:
    """
    Secure a socket connection by wrapping it with SSL/TLS encryption.

    :param sock: The socket to secure.
    :param certfile: Path to the certificate file.
    :param keyfile: Path to the private key file.
    :return: An SSL-wrapped socket.
    """
    try:
        # Create a default SSL context for the server side
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(certfile=certfile, keyfile=keyfile)

        # Wrap the socket with the SSL context
        secure_sock = context.wrap_socket(sock, server_side=True)
        return secure_sock

    except ssl.SSLError as e:
        logger.error(f"SSL error occurred: {e}")
        raise
    except Exception as e:
        logger.exception("Failed to secure socket")
        raise


def protect_buffer(data: bytes, max_payload_size: int) -> bytes:
    """
    Protect the buffer by ensuring the data does not exceed the max allowed payload size.

    :param data: The data to check.
    :param max_payload_size: The maximum allowable size for the payload.
    :return: The data if it does not exceed the max payload size.
    :raises BufferError: If the data exceeds the max allowed size.
    """
    try:
        if len(data) > max_payload_size:
            raise BufferError(
                f"Payload too large. Max allowed: {max_payload_size} bytes"
            )
        return data

    except BufferError as e:
        logger.warning(f"Buffer error: {e}")
        raise
    except Exception as e:
        logger.exception("Unexpected error in protect_buffer")
        raise
