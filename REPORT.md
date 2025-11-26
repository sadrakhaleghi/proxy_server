# Smart HTTP/HTTPS Proxy Server 🌐

A multi-threaded, feature-rich HTTP/HTTPS proxy server implemented in Python using raw sockets. This project demonstrates core networking concepts including socket programming, threading, HTTP protocol parsing, tunneling, and performance optimization techniques.

**Course:** Computer Networks - Phase 1
**Language:** Python 3

---

## 🚀 Features

### Core Features (Basic Phase)
- **HTTP Proxy:** Parses and forwards standard HTTP requests (GET, POST, HEAD, etc.).
- **HTTPS Tunneling:** Supports the `CONNECT` method to establish secure tunnels for HTTPS traffic.
- **Concurrency:** Uses **Multi-threading** to handle multiple client connections simultaneously without blocking.
- **Logging:** Records detailed request logs (Time, IP, Method, URL, Status) in `proxy_log.txt`.
- **Domain Filtering:** Blocks access to specified blacklisted domains (returns 403 Forbidden).
- **Caching:** Implements in-memory caching for HTTP responses to speed up repeated requests.

### Advanced Features (Bonus Phase - 100 Points)
- **📊 Statistics Dashboard:** A graphical HTML page available at `http://proxy.stats` showing real-time traffic data.
- **⚡ Conditional Caching:** Implements `If-Modified-Since` headers to validate cache freshness with the server (returns 304 Not Modified if valid).
- **🛡️ Rate Limiting:** Protects the server from DoS attacks by limiting requests per IP address (returns 429 Too Many Requests).
- **🔄 HTTP Keep-Alive:** Supports persistent connections to reduce latency and overhead.

---

## 📂 Project Structure

The project is modularized for better maintainability:

| File | Description |
| :--- | :--- |
| `main.py` | Entry point. Initializes the server socket and handles thread spawning. |
| `proxy_handler.py` | Core logic. Parses requests, handles HTTP forwarding, HTTPS tunneling, and Keep-Alive loops. |
| `cache.py` | Manages in-memory storage, retrieval, and Conditional Caching logic (Last-Modified). |
| `filter.py` | Contains the blacklist logic and checks if a domain is blocked. |
| `stats.py` | Tracks statistics (Total requests, Bytes, etc.) and implements Rate Limiting logic. |
| `logger.py` | Handles writing request details to the `proxy_log.txt` file. |

---

## ⚙️ Setup & Usage

### 1. Prerequisites
- Python 3.x installed.
- No external libraries required (uses standard `socket`, `threading`, `select`, `time`, `datetime`).

### 2. Run the Server
Open a terminal in the project directory and run:
```bash
python main.py
```
You should see: `[*] Proxy Server (Main) is running on 127.0.0.1:8080`

---

## 🧪 How to Test

### 1. Test HTTP & Caching
Open a non-HTTPS site (e.g., `http://neverssl.com` or `http://example.com`).
* **First Load:** Logs show `[+] Cached`.
* **Refresh:** Logs show `[*] Cache Hit` or `304 Not Modified`.

### 2. Test HTTPS (Tunneling)
Open a secure site (e.g., `https://google.com` or `https://wikipedia.org`).
* The site should load correctly.
* Logs will show `CONNECT` requests.

### 3. Test Filtering (Blacklist)
Try to access a blocked domain defined in `filter.py` (e.g., `http://divar.ir` or `http://varzesh3.com`).
* **Result:** You will see a custom **403 Forbidden** page.

### 4. Test Statistics Dashboard
In your browser address bar, type:
👉 `http://proxy.stats`
* **Result:** Displays a graphical dashboard with Total Requests, Blocked Sites, Cache Hits, and Data Transferred.

### 5. Test Rate Limiting
Refresh a page rapidly (e.g., hold `F5` or use `curl` in a loop).
* **Result:** After exceeding the limit (configurable in `stats.py`), you will see a **429 Too Many Requests** error.

---

## 🔧 Configuration

You can tweak the server settings by modifying the following files:

* **`filter.py`**: Add or remove domains from the `BLOCKED_DOMAINS` list.
* **`stats.py`**: Change `RATE_LIMIT_COUNT` (default is 200) or `RATE_LIMIT_WINDOW`.
* **`cache.py`**: Change `CACHE_TIMEOUT` (default is 60 seconds).
* **`main.py`**: Change the listening `PORT`.

---

## 📝 Logging

All traffic is logged to `proxy_log.txt` in the following format:

```text
[2024-11-26 14:00:01] 127.0.0.1 - GET example.com - Processing
[2024-11-26 14:00:05] 127.0.0.1 - CONNECT google.com - Processing
[2024-11-26 14:00:10] 127.0.0.1 - GET divar.ir - BLOCKED
```

---

## 👨‍💻 Sadra Khaleghi

Developed for **Computer Networks Course**.