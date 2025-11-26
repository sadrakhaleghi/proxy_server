import time

CACHE_STORE = {}
CACHE_TIMEOUT = 60

def get_cache(url):
    if url in CACHE_STORE:
        data, timestamp = CACHE_STORE[url]
        
        if time.time() - timestamp < CACHE_TIMEOUT:
            return data
        else:
            del CACHE_STORE[url]
            
    return None

def save_cache(url, data):
    if data:
        CACHE_STORE[url] = (data, time.time())
        print(f"[+] Cached: {url}")