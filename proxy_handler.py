# Responsibility: Handle requests, parse HTTP, and manage connection to destination
import socket

def parse_request(request_data):
    """
    Parses the raw HTTP request data to extract method, host, and port.
    Returns:
        method (str): GET, POST, CONNECT, etc.
        host (str): Target hostname (e.g., google.com)
        port (int): Target port (e.g., 80 or 443)
    """
    try:
        # 1. Decode bytes to string
        request_text = request_data.decode('utf-8')
        
        # 2. Get the first line (Request Line)
        lines = request_text.split('\n')
        first_line = lines[0].strip()
        
        # 3. Split by space to get parts
        parts = first_line.split(' ')
        if len(parts) < 2:
            return None, None, None
            
        method = parts[0]
        url = parts[1]  
        
        host = ""
        port = 80
        
        # 4. Extract Host and Port based on Method
        if method == 'CONNECT':
            # HTTPS Request format: "CONNECT google.com:443 HTTP/1.1"
            address_parts = url.split(':')
            host = address_parts[0]
            port = 443 if len(address_parts) < 2 else int(address_parts[1])
            
        else:
            # Find the position of "://" to remove http://
            http_pos = url.find("://")
            if http_pos == -1:
                temp_url = url
            else:
                temp_url = url[(http_pos + 3):] 
            
            # Find where the path starts
            path_pos = temp_url.find("/")
            if path_pos == -1:
                base_url = temp_url
            else:
                base_url = temp_url[:path_pos]

            # Check for port in URL
            port_pos = base_url.find(":")
            
            if port_pos == -1:
                host = base_url
                port = 80
            else:
                host = base_url[:port_pos]
                port = int(base_url[port_pos+1:])
                
        return method, host, port
        
    except Exception as e:
        print(f"[!] Error parsing request: {e}")
        return None, None, None

def handle_request(client_socket, client_address):
    try:
        # 1. Receive data from client (Browser)
        request_data = client_socket.recv(4096)
        
        if not request_data:
            client_socket.close()
            return

        # 2. Parse the request to see what the user wants
        method, target_host, target_port = parse_request(request_data)
        
        if target_host:
            print(f"[>] Request Parsed:")
            print(f"    Method: {method}")
            print(f"    Host:   {target_host}")
            print(f"    Port:   {target_port}")
            print("-" * 30)
        else:
            print("[!] Could not parse target host.")
        
    except Exception as e:
        print(f"[!] Error handling client: {e}")
        
    finally:
        client_socket.close()