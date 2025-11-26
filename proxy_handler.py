import socket
import select
import logger
import filter
import cache
import stats

KEEP_ALIVE_TIMEOUT = 10

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
    return False

def send_too_many_requests_response(client_socket):
    response = (b"HTTP/1.1 429 Too Many Requests\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n"
                b"<html><body><h1>429 Too Many Requests</h1></body></html>")
    client_socket.sendall(response)
    return False

def send_stats_page(client_socket):
    response_body = stats.get_stats_html()
    response_headers = (
        f"HTTP/1.1 200 OK\r\nContent-Length: {len(response_body)}\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n"
    ).encode('utf-8')
    client_socket.sendall(response_headers + response_body)
    return False

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
                    if not data: return False
                    stats.add_bytes(len(data))
                    other_sock.sendall(data)
                except: return False
    except: pass
    finally:
        server_socket.close()
    return False

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
    server_socket = None
    try:
        # 1. Cache Check
        cached_data, last_modified = cache.get_cache(full_url)
        if cached_data and not last_modified:
            print(f"[*] Cache Hit (Fresh)! {full_url}")
            stats.increment_cache()
            client_socket.sendall(cached_data)
            return True

        # 2. Connect to Server
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect((target_host, target_port))

        # Conditional Get
        if last_modified:
            print(f"[?] Conditional Request for {full_url} (Since: {last_modified})")
            if request_data.endswith(b"\r\n\r\n"):
                insert_header = f"If-Modified-Since: {last_modified}\r\n\r\n"
                request_data = request_data[:-4] + insert_header.encode('utf-8')

        # Forward Request
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
                    print(f"[*] 304 Not Modified!")
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
            
    except Exception as e:
        print(f"[!] HTTP Error: {e}")
        return False
    finally:
        if server_socket: server_socket.close()
    
    return True

def handle_request(client_socket, client_address):
    client_socket.settimeout(KEEP_ALIVE_TIMEOUT) 
    try:
        while True:
            try:
                request_data = client_socket.recv(4096)
                if not request_data:
                    break
            except socket.timeout:
                break

            method, target_host, target_port, full_url = parse_request(request_data)
            
            if not target_host:
                break
            
            client_ip = client_address[0]

            if stats.is_rate_limited(client_ip):
                print(f"[!] RATE LIMIT: {client_ip}")
                logger.log_request(client_ip, method, target_host, "RATE_LIMITED")
                send_too_many_requests_response(client_socket)
                break 
            
            stats.increment_total()

            if "proxy.stats" in target_host:
                send_stats_page(client_socket)
                break

            if filter.is_blocked(target_host):
                print(f"[!] BLOCKED: {target_host}")
                stats.increment_blocked()
                logger.log_request(client_ip, method, target_host, "BLOCKED")
                send_forbidden_response(client_socket)
                break

            print(f"[>] {method} {target_host}:{target_port}")
            logger.log_request(client_ip, method, target_host, "Processing")

            should_continue = False
            if method == 'CONNECT':
                should_continue = handle_https_tunnel(client_socket, target_host, target_port)
            else:
                should_continue = handle_http_request(client_socket, request_data, target_host, target_port, full_url)
            
            if not should_continue:
                break

    except Exception as e:
        pass
    finally:
        client_socket.close()