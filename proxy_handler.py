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

def send_forbidden_response(client_socket):
    response = (b"HTTP/1.1 403 Forbidden\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n"
                b"<html><body><h1>403 Forbidden</h1></body></html>")
    client_socket.sendall(response)
    client_socket.close()

def send_too_many_requests_response(client_socket):
    response = (b"HTTP/1.1 429 Too Many Requests\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n"
                b"<html><body><h1>429 Too Many Requests</h1></body></html>")
    client_socket.sendall(response)
    client_socket.close()

def send_stats_page(client_socket):
    response_body = stats.get_stats_html()
    response_headers = (
        f"HTTP/1.1 200 OK\r\nContent-Length: {len(response_body)}\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n"
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

def extract_header(response_bytes, header_name):
    try:
        headers_end = response_bytes.find(b"\r\n\r\n")
        if headers_end == -1: return None
        headers_part = response_bytes[:headers_end].decode('utf-8', errors='ignore')
        for line in headers_part.split('\r\n'):
            if line.lower().startswith(header_name.lower() + ":"):
                return line.split(":", 1)[1].strip()
    except: pass
    return None

def handle_http_request(client_socket, request_data, target_host, target_port, full_url):
    try:
        cached_data, last_modified = cache.get_cache(full_url)
        
        if cached_data and not last_modified:
            print(f"[*] Cache Hit (Fresh)! {full_url}")
            stats.increment_cache()
            client_socket.sendall(cached_data)
            client_socket.close()
            return

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect((target_host, target_port))

        if last_modified:
            print(f"[?] Conditional Request for {full_url} (Since: {last_modified})")
            if request_data.endswith(b"\r\n\r\n"):
                insert_header = f"If-Modified-Since: {last_modified}\r\n\r\n"
                request_data = request_data[:-4] + insert_header.encode('utf-8')

        server_socket.sendall(request_data)
        
        full_response = b""
        first_chunk = True
        is_304 = False
        
        while True:
            data = server_socket.recv(4096)
            if not data: break
            
            if first_chunk:
                first_chunk = False
                if b"304 Not Modified" in data:
                    print(f"[*] 304 Not Modified! Serving from Old Cache.")
                    is_304 = True
                    cache.save_cache(full_url, cached_data, last_modified) 
                    client_socket.sendall(cached_data)
                    stats.increment_cache()
                    break 
            
            client_socket.sendall(data)
            full_response += data
            stats.add_bytes(len(data))
        
        if not is_304:
            new_last_modified = extract_header(full_response, "Last-Modified")
            cache.save_cache(full_url, full_response, new_last_modified)
            
        server_socket.close()
        client_socket.close()
        
    except Exception as e:
        print(f"[!] HTTP Error: {e}")
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

        # Rate Limit Check
        if stats.is_rate_limited(client_ip):
            print(f"[!] RATE LIMIT: {client_ip}")
            logger.log_request(client_ip, method, target_host, "RATE_LIMITED")
            send_too_many_requests_response(client_socket)
            return
        
        stats.increment_total()

        if "proxy.stats" in target_host:
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