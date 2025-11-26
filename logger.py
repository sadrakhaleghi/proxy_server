# Responsibility: Save request details to a text file

import datetime

LOG_FILE = "proxy_log.txt"

def log_request(client_ip, method, url, message=""):
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        log_entry = f"[{timestamp}] {client_ip} - {method} {url} - {message}\n"
        
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
            
    except Exception as e:
        print(f"[!] Logging Error: {e}")