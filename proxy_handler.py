import socket
import select
import logger
import filter
import cache
import stats

def parse_request(request_data):
    try:
        request_text = request_data.decode('utf-8')
        lines = request_text.split('\n')
        first_line = lines[0].strip()
        parts = first_line.split(' ')
        if len(parts) < 2: return None, None, None, None
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
        return method, host, port, url
    except: return None, None, None, None

def send_stats_page(client_socket):
    """
    Sends the statistics HTML page to the client.
    """
    response_body = stats.get_stats_html()
    response_headers = (
        "HTTP/1.1 200 OK\r\n"
        f"Content-Length: {len(response_body)}\r\n"
        "Content-Type: text/html\r\n"
        "Connection: close\r\n\r\n"
    ).encode('utf-8')
    client_socket.sendall(response_headers + response_body)
    client_socket.close()

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
                    
                    stats.add_bytes(len(data))

                    other_sock.sendall(data)
                except: return
    except: pass
    finally:
        server_socket.close()
        client_socket.close()

def handle_http_request(client_socket, request_data, target_host, target_port, full_url):
    try:
        # 1. CHECK CACHE
        cached_response = cache.get_cache(full_url)
        if cached_response:
            print(f"[*] Cache Hit! {full_url}")
            stats.increment_cache()
            client_socket.sendall(cached_response)
            client_socket.close()
            return

        # 2. DOWNLOAD
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect((target_host, target_port))
        server_socket.sendall(request_data)
        
        full_response = b""
        
        while True:
            data = server_socket.recv(4096)
            if len(data) > 0:
                stats.add_bytes(len(data))
                client_socket.sendall(data)
                full_response += data
            else:
                break
        
        cache.save_cache(full_url, full_response)
        server_socket.close()
        client_socket.close()
        
    except Exception as e:
        print(f"[!] HTTP Error: {e}")
        client_socket.close()

def send_forbidden_response(client_socket):
    response = (
        "HTTP/1.1 403 Forbidden\r\n"
        "Content-Type: text/html\r\n"
        "Connection: close\r\n\r\n"
        "<html><body><h1>403 Forbidden</h1><p>Access to this site is blocked.</p></body></html>"
    ).encode('utf-8')
    client_socket.sendall(response)
    client_socket.close()

def send_too_many_requests_response(client_socket):
    response = (
        "HTTP/1.1 429 Too Many Requests\r\n"
        "Content-Type: text/html\r\n"
        "Connection: close\r\n\r\n"
        "<html><body><h1>429 Too Many Requests</h1><p>You are sending requests too fast. Please slow down.</p></body></html>"
    ).encode('utf-8')
    client_socket.sendall(response)
    client_socket.close()

def handle_request(client_socket, client_address):
    try:
        request_data = client_socket.recv(4096)
        if not request_data:
            client_socket.close()
            return

        method, target_host, target_port, full_url = parse_request(request_data)
        
        if not target_host:
            client_socket.close()
            return
        
        client_ip = client_address[0]

        if stats.is_rate_limited(client_ip):
            print(f"[!] RATE LIMIT EXCEEDED: {client_ip}")
            logger.log_request(client_ip, method, target_host, "RATE_LIMITED")
            send_too_many_requests_response(client_socket)
            return
        
        stats.increment_total()

        if "proxy.stats" in target_host:
            print("[*] Serving Statistics Page")
            send_stats_page(client_socket)
            return
        
        if filter.is_blocked(target_host):
            print(f"[!] BLOCKED: {target_host}")
            stats.increment_blocked()
            logger.log_request(client_ip, method, target_host, "BLOCKED")
            send_forbidden_response(client_socket)
            return

        print(f"[>] {method} {target_host}:{target_port}")
        logger.log_request(client_ip, method, target_host, "Processing")

        if method == 'CONNECT':
            handle_https_tunnel(client_socket, target_host, target_port)
        else:
            handle_http_request(client_socket, request_data, target_host, target_port, full_url)

    except Exception as e:
        print(f"[!] Handler Error: {e}")
        client_socket.close()