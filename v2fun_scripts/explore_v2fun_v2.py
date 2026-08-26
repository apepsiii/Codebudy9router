"""
V2Fun.ai API Explorer v2
Test with token as query parameter
"""

import requests
import json

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6IlNzWnZoMGpvaG5zdG9uNzUwM0BnZXpvbi5uZXQiLCJjbGllbnRUeXBlIjoid2ViIiwidXNlcmlkIjoiMjA5MjU3NjgwOTEwMjA4NjE0NiIsImV4cCI6MTc4ODA0NjU2NH0.c9CszVX-sQoep0XmNCjH73wCiv98NDv2vscJRCqq8no"

BASE_URL = "https://api.prod.v2fun.ai"
HEADERS = {
    "Accept": "application/json",
    "Origin": "https://v2fun.ai",
    "Referer": "https://v2fun.ai/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

def test_endpoint(method, path, use_token_param=True):
    """Test an API endpoint"""
    url = f"{BASE_URL}{path}"
    
    # Add token as query parameter
    if use_token_param:
        params = {"token": TOKEN}
    else:
        params = {}
    
    try:
        if method == "GET":
            resp = requests.get(url, headers=HEADERS, params=params, timeout=5)
        elif method == "POST":
            resp = requests.post(url, headers=HEADERS, params=params, timeout=5)
        
        print(f"\n{'='*60}")
        print(f"[{method}] {path}")
        print(f"Status: {resp.status_code}")
        
        if resp.status_code < 400:
            try:
                result = resp.json()
                print(f"Response: {json.dumps(result, indent=2)[:800]}")
                return result
            except:
                text = resp.text[:500]
                print(f"Response (text): {text}")
                return text
        else:
            print(f"Error: {resp.text[:300]}")
            
        return None
    except Exception as e:
        print(f"\n[{method}] {path} - Error: {e}")
        return None

print("="*60)
print("V2Fun.ai API Explorer v2 - Token as Query Parameter")
print("="*60)
print()

# Test UMS endpoints with token param
ums_endpoints = [
    "/ums/user/info",
    "/ums/user/profile", 
    "/ums/user/current",
    "/ums/account/info",
    "/ums/external/user",
    "/ums/external/profile",
]

print("Testing UMS endpoints...")
for path in ums_endpoints:
    test_endpoint("GET", path)

# Test potential chat/conversation endpoints
chat_endpoints = [
    "/api/chat/list",
    "/api/conversation/list",
    "/api/chat/conversations",
]

print("\nTesting Chat endpoints...")
for path in chat_endpoints:
    test_endpoint("GET", path)

print("\n" + "="*60)
print("Done!")
print("="*60)
