import socket
import select
import logger

def parse_request(request_data):
    try:
        request_text = request_data.decode('utf-8')
        lines = request_text.split('\n')
        first_line = lines[0].strip()
        parts = first_line.split(' ')
        if len(parts) < 2: return None, None, None
        method = parts[0]
        url = parts[1]
        host = ""
        port = 80
        if method == 'CONNECT':
            address_parts = url.split(':')
            host = address_parts[0]
            port = 443 if len(address_parts) < 2 else int(address_parts[1])
        else:
            http_pos = url.find("://")
            temp_url = url if http_pos == -1 else url[(http_pos + 3):]
            path_pos = temp_url.find("/")
            base_url = temp_url if path_pos == -1 else temp_url[:path_pos]
            port_pos = base_url.find(":")
            if port_pos == -1: host, port = base_url, 80
            else: host, port = base_url[:port_pos], int(base_url[port_pos+1:])
        return method, host, port
    except: return None, None, None

def handle_https_tunnel(client_socket, target_host, target_port):
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect((target_host, target_port))
        client_socket.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        sockets = [client_socket, server_socket]
        while True:
            readable, _, _ = select.select(sockets, [], [], 10)
            if not readable: break
            for sock in readable:
                other_sock = server_socket if sock is client_socket else client_socket
                try:
                    data = sock.recv(4096)
                    if not data: return
                    other_sock.sendall(data)
                except: return
    except: pass
    finally:
        server_socket.close()
        client_socket.close()

def handle_http_request(client_socket, request_data, target_host, target_port):
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect((target_host, target_port))
        server_socket.sendall(request_data)
        while True:
            data = server_socket.recv(4096)
            if len(data) > 0: client_socket.sendall(data)
            else: break
        server_socket.close()
        client_socket.close()
    except: client_socket.close()

def handle_request(client_socket, client_address):
    """
    UPDATED: Now logs requests to file using logger module
    """
    try:
        request_data = client_socket.recv(4096)
        if not request_data:
            client_socket.close()
            return

        method, target_host, target_port = parse_request(request_data)
        
        if not target_host:
            client_socket.close()
            return

        # --- LOGGING ADDED HERE ---
        print(f"[>] {method} {target_host}:{target_port}")
        client_ip = client_address[0]
        logger.log_request(client_ip, method, target_host, "Processing")

        if method == 'CONNECT':
            handle_https_tunnel(client_socket, target_host, target_port)
        else:
            handle_http_request(client_socket, request_data, target_host, target_port)

    except Exception as e:
        print(f"[!] General Handler Error: {e}")
        client_socket.close()