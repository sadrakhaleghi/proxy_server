def handle_request(client_socket, client_address):
    print(f"[+] Client {client_address} handled by thread.")
    client_socket.close()