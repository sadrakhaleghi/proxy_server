# Responsibility: Handle requests, parse HTTP, and manage connection to destination
import socket
import select 

def parse_request(request_data):
    """
    Parses the raw HTTP request data to extract method, host, and port.
    """
    try:
        request_text = request_data.decode('utf-8')
        lines = request_text.split('\n')
        first_line = lines[0].strip()
        parts = first_line.split(' ')
        
        if len(parts) < 2:
            return None, None, None
            
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
            if http_pos == -1:
                temp_url = url
            else:
                temp_url = url[(http_pos + 3):]
            
            path_pos = temp_url.find("/")
            if path_pos == -1:
                base_url = temp_url
            else:
                base_url = temp_url[:path_pos]

            port_pos = base_url.find(":")
            if port_pos == -1:
                host = base_url
                port = 80
            else:
                host = base_url[:port_pos]
                port = int(base_url[port_pos+1:])
                
        return method, host, port
    except Exception:
        return None, None, None

def handle_https_tunnel(client_socket, target_host, target_port):
    """
    Handles HTTPS requests (CONNECT method).
    Creates a direct tunnel between client and target server.
    """
    try:
        # 1. Connect to the Destination Server
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect((target_host, target_port))

        # 2. Tell the Client (Browser) that connection is established
        success_msg = b"HTTP/1.1 200 Connection Established\r\n\r\n"
        client_socket.sendall(success_msg)

        # 3. Start Tunneling (Transfer data back and forth)
        sockets = [client_socket, server_socket]
        
        while True:
            readable, _, _ = select.select(sockets, [], [], 10)
            
            if not readable:
                break 

            for sock in readable:
                other_sock = server_socket if sock is client_socket else client_socket
                
                try:
                    data = sock.recv(4096)
                    if not data:
                        return 
                    other_sock.sendall(data)
                except:
                    return 

    except Exception as e:
        print(f"[!] HTTPS Tunnel Error: {e}")
    finally:
        server_socket.close()
        client_socket.close()

def handle_http_request(client_socket, request_data, target_host, target_port):
    """
    Handles standard HTTP requests (GET, POST, etc.)
    """
    try:
        # 1. Connect to the Destination Server
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect((target_host, target_port))
        
        # 2. Forward the Client's Request to the Server
        server_socket.sendall(request_data)
        
        # 3. Receive the Server's Response and Forward to Client
        while True:
            data = server_socket.recv(4096)
            if len(data) > 0:
                client_socket.sendall(data)
            else:
                break
                
        server_socket.close()
        client_socket.close()
        
    except Exception as e:
        print(f"[!] HTTP Error: {e}")
        client_socket.close()

def handle_request(client_socket, client_address):
    """
    Main handler: Decides whether to Tunnel (HTTPS) or Forward (HTTP)
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

        print(f"[>] {method} {target_host}:{target_port}")

        if method == 'CONNECT':
            handle_https_tunnel(client_socket, target_host, target_port)
        else:
            handle_http_request(client_socket, request_data, target_host, target_port)

    except Exception as e:
        print(f"[!] General Handler Error: {e}")
        client_socket.close()