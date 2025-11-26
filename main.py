# Responsibility: Server setup, listening on port, and managing threading
import socket
import threading
import proxy_handler

HOST = '127.0.0.1'
PORT = 8080

def start_server():
    # 1. Create the socket
    # AF_INET = IPv4, SOCK_STREAM = TCP
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        # 2. Bind
        server_socket.bind((HOST, PORT))
        
        # 3. Listen
        server_socket.listen(10)
        print(f"[*] Proxy Server (Main) is running on {HOST}:{PORT}")

        while True:
            # 4. Accept connection
            client_socket, client_addr = server_socket.accept()
            
            # 5. Hand over to thread
            client_thread = threading.Thread(
                target=proxy_handler.handle_request,
                args=(client_socket, client_addr)
            )
            
            client_thread.start()

    except Exception as e:
        print(f"[!] Server Error: {e}")
    finally:
        server_socket.close()

if __name__ == '__main__':
    start_server()