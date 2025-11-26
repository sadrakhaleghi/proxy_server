# File: filter.py
# Responsibility: Check if a domain is blocked
BLOCKED_DOMAINS = [
    "varzesh3.com",
    "digikala.com",
    "aparat.com",
    "divar.ir",
    "test.com"
]

def is_blocked(host):
    if not host:
        return False
    
    host = host.lower()
    
    if host.startswith("www."):
        host = host[4:]
    
    if host in BLOCKED_DOMAINS:
        return True
    
    for blocked in BLOCKED_DOMAINS:
        if host.endswith("." + blocked):
            return True
        
    return False