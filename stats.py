# Responsibility: Keep track of proxy statistics
TOTAL_REQUESTS = 0
BLOCKED_REQUESTS = 0
CACHE_HITS = 0
BYTES_TRANSFERRED = 0

def increment_total():
    global TOTAL_REQUESTS
    TOTAL_REQUESTS += 1

def increment_blocked():
    global BLOCKED_REQUESTS
    BLOCKED_REQUESTS += 1

def increment_cache():
    global CACHE_HITS
    CACHE_HITS += 1

def add_bytes(count):
    global BYTES_TRANSFERRED
    BYTES_TRANSFERRED += count

def get_stats_html():
    """
    Generate a simple HTML page with current statistics.
    """
    html = f"""
    <html>
    <head>
        <title>Proxy Statistics</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f9; padding: 50px; text-align: center; }}
            .card {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); display: inline-block; margin: 10px; width: 200px; }}
            h1 {{ color: #333; }}
            .number {{ font-size: 40px; color: #007bff; font-weight: bold; }}
            .label {{ color: #666; }}
        </style>
    </head>
    <body>
        <h1>Proxy Server Statistics</h1>
        <hr>
        <div class="card">
            <div class="number">{TOTAL_REQUESTS}</div>
            <div class="label">Total Requests</div>
        </div>
        <div class="card">
            <div class="number" style="color: red;">{BLOCKED_REQUESTS}</div>
            <div class="label">Blocked Sites</div>
        </div>
        <div class="card">
            <div class="number" style="color: green;">{CACHE_HITS}</div>
            <div class="label">Cache Hits</div>
        </div>
        <div class="card">
            <div class="number" style="color: orange;">{round(BYTES_TRANSFERRED / 1024 / 1024, 2)}</div>
            <div class="label">Data (MB)</div>
        </div>
        <br><br>
        <button onclick="location.reload()">Refresh Stats</button>
    </body>
    </html>
    """
    return html.encode('utf-8')