import ssl

def secure_socket(sock, certfile, keyfile):
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile=certfile, keyfile=keyfile)
    secure_sock = context.wrap_socket(sock, server_side=True)
    return secure_sock

def protect_buffer(data: bytes, max_payload_size: int) -> bytes:
    if len(data) > max_payload_size:
        raise BufferError(
            f"Payload too large. Max allowed: {max_payload_size} bytes")
        return data
