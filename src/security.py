import ssl
import socket
import logging
import os

# Set up logging
logger = logging.getLogger(__name__)

def secure_socket(sock: socket.socket, certfile: str, keyfile: str, server_side: bool = True) -> ssl.SSLSocket:
    """
    Secure a socket connection by wrapping it with SSL/TLS encryption.

    :param sock: The socket to secure.
    :param certfile: Path to the certificate file.
    :param keyfile: Path to the private key file.
    :return: An SSL-wrapped socket.
    """
    try:
        # First check if certificate and key files exist
        if not os.path.exists(certfile):
            logger.error(f"Certificate file not found: {certfile}")
            raise FileNotFoundError(f"Certificate file not found: {certfile}")
        
        if not os.path.exists(keyfile):
            logger.error(f"Key file not found: {keyfile}")
            raise FileNotFoundError(f"Key file not found: {keyfile}")
            
        # Create a default SSL context for the server side
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        
        # Add error handling around loading cert chain
        try:
            context.load_cert_chain(certfile=certfile, keyfile=keyfile)
        except ssl.SSLError as e:
            logger.error(f"SSL error when loading certificate chain: {e}")
            if "PEM lib" in str(e):
                logger.error("Invalid PEM format. Check that certificate and key files are properly formatted.")
            raise
            
        # Wrap the socket with the SSL context
        secure_sock = context.wrap_socket(sock, server_side=server_side)
        return secure_sock

    except FileNotFoundError as e:
        logger.error(f"Certificate file not found: {e}")
        raise
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
    :raises TypeError: If the input is not bytes.
    """
    # Check input type first
    if not isinstance(data, bytes):
        raise TypeError("Input data must be bytes")
    
    # Check if max_payload_size is valid
    if max_payload_size <= 0:
        logger.warning(f"Invalid max_payload_size: {max_payload_size}")
        max_payload_size = 1024  # Set a default reasonable size
        
    try:
        if len(data) > max_payload_size:
            raise BufferError(f"Payload too large. Max allowed: {max_payload_size} bytes")
        return data

    except BufferError as e:
        logger.warning(f"Buffer error: {e}")
        raise
    except Exception as e:
        logger.exception("Unexpected error in protect_buffer")
        raise