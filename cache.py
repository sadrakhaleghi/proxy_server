import time

CACHE_STORE = {}
CACHE_TIMEOUT = 5

def get_cache(url):
    if url in CACHE_STORE:
        data, timestamp, last_modified = CACHE_STORE[url]
        
        if time.time() - timestamp < CACHE_TIMEOUT:
            return data, None
        
        return data, last_modified
        
    return None, None

def save_cache(url, data, last_modified=None):
    if data:
        CACHE_STORE[url] = (data, time.time(), last_modified)
        print(f"[+] Cached: {url} (Last-Mod: {last_modified})")