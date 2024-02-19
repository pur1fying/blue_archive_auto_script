import socket


def wsa_try_start(host, port):
    try:
        port = int(port)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        return f"{host}:{port}:"
    except socket.error as e:
        return None
    finally:
        s.close()
