import ssl
import socket
import logging
import os
from typing import Optional

# Set up a logger for this module
logger = logging.getLogger(__name__)


def secure_socket(
    sock: socket.socket, certfile: str, keyfile: str, server_side: bool = True
) -> ssl.SSLSocket:
    """
    Wrap a socket with SSL/TLS encryption for secure communication.

    This function ensures that the given socket is encrypted using the provided 
    certificate and key files, creating a secure communication channel.

    Args:
        sock (socket.socket): The socket object to secure.
        certfile (str): Path to the SSL certificate file (PEM format).
        keyfile (str): Path to the private key file (PEM format).
        server_side (bool, optional): Whether the socket is for a server. Defaults to True.

    Returns:
        ssl.SSLSocket: The SSL-wrapped socket.

    Raises:
        FileNotFoundError: If either the certificate or key file is missing.
        ssl.SSLError: If there is an SSL-related error.
        Exception: For any other unexpected error during wrapping.
    """
    try:
        # Ensure certificate and key files exist
        if not os.path.exists(certfile):
            logger.error(f"Certificate file not found: {certfile}")
            raise FileNotFoundError(f"Certificate file not found: {certfile}")
        
        if not os.path.exists(keyfile):
            logger.error(f"Key file not found: {keyfile}")
            raise FileNotFoundError(f"Key file not found: {keyfile}")
        
        # Create SSL context (assumes server by default)
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        
        # Load the certificate and private key into the context
        try:
            context.load_cert_chain(certfile=certfile, keyfile=keyfile)
        except ssl.SSLError as e:
            logger.error(f"SSL error when loading certificate chain: {e}")
            if "PEM lib" in str(e):
                logger.error("Invalid PEM format. Check certificate and key files.")
            raise
        
        # Securely wrap the socket
        secure_sock = context.wrap_socket(sock, server_side=server_side)
        return secure_sock

    except FileNotFoundError as e:
        logger.error(f"Certificate/key file not found: {e}")
        raise
    except ssl.SSLError as e:
        logger.error(f"SSL error occurred: {e}")
        raise
    except Exception as e:
        logger.exception("Unexpected failure in securing socket")
        raise


def protect_buffer(data: bytes, max_payload_size: int) -> bytes:
    """
    Ensure the data buffer size does not exceed the maximum allowed payload.

    This function checks the size of the provided data buffer and raises an error 
    if it exceeds the specified maximum payload size.

    Args:
        data (bytes): The input data buffer to validate.
        max_payload_size (int): The maximum number of bytes allowed.

    Returns:
        bytes: The validated data buffer (unchanged).

    Raises:
        BufferError: If the data exceeds the max allowed size.
        TypeError: If the input data is not of type `bytes`.
    """
    # Validate input type
    if not isinstance(data, bytes):
        raise TypeError("Input data must be of type 'bytes'")

    # Validate payload size threshold
    if max_payload_size <= 0:
        logger.warning(f"Invalid max_payload_size: {max_payload_size}. Defaulting to 1024.")
        max_payload_size = 1024  # Default value if invalid input is provided

    try:
        if len(data) > max_payload_size:
            raise BufferError(f"Payload too large. Max allowed: {max_payload_size} bytes")
        return data

    except BufferError as e:
        logger.warning(f"Buffer error: {e}")
        raise
    except Exception as e:
        logger.exception("Unexpected error while protecting buffer")
        raise
