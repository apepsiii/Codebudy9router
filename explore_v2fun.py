"""
V2Fun.ai API Explorer
Explore available API endpoints
"""

import requests
import json
from datetime import datetime

# Token from successful registration
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6IlNzWnZoMGpvaG5zdG9uNzUwM0BnZXpvbi5uZXQiLCJjbGllbnRUeXBlIjoid2ViIiwidXNlcmlkIjoiMjA5MjU3NjgwOTEwMjA4NjE0NiIsImV4cCI6MTc4ODA0NjU2NH0.c9CszVX-sQoep0XmNCjH73wCiv98NDv2vscJRCqq8no"

BASE_URL = "https://api.prod.v2fun.ai"
HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://v2fun.ai",
    "Referer": "https://v2fun.ai/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Authorization": f"Bearer {TOKEN}"
}

def test_endpoint(method, path, data=None, params=None):
    """Test an API endpoint"""
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET":
            resp = requests.get(url, headers=HEADERS, params=params, timeout=5)
        elif method == "POST":
            resp = requests.post(url, headers=HEADERS, json=data, timeout=5)
        elif method == "PUT":
            resp = requests.put(url, headers=HEADERS, json=data, timeout=5)
        elif method == "DELETE":
            resp = requests.delete(url, headers=HEADERS, timeout=5)
        
        print(f"\n{'='*60}")
        print(f"[{method}] {path}")
        print(f"Status: {resp.status_code}")
        
        if resp.status_code == 200:
            try:
                result = resp.json()
                print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}")
            except:
                print(f"Response: {resp.text[:500]}")
        else:
            print(f"Error: {resp.text[:200]}")
            
        return resp
    except Exception as e:
        print(f"\n[{method}] {path} - Error: {e}")
        return None

print("="*60)
print("V2Fun.ai API Explorer")
print("="*60)
print(f"Token: {TOKEN[:50]}...")
print(f"Base URL: {BASE_URL}")
print()

# Common API patterns to test
endpoints = [
    # User Management Service (UMS)
    ("GET", "/ums/user/info"),
    ("GET", "/ums/user/profile"),
    ("GET", "/ums/user/me"),
    ("GET", "/ums/user/current"),
    ("GET", "/ums/user/detail"),
    ("GET", "/ums/user/settings"),
    ("GET", "/ums/account/info"),
    
    # Chat/Conversation
    ("GET", "/chat/conversations"),
    ("GET", "/chat/history"),
    ("GET", "/chat/list"),
    ("GET", "/conversation/list"),
    ("GET", "/message/list"),
    
    # Models
    ("GET", "/model/list"),
    ("GET", "/models"),
    ("GET", "/api/models"),
    
    # Usage/Credits
    ("GET", "/usage"),
    ("GET", "/usage/quota"),
    ("GET", "/usage/stats"),
    ("GET", "/credits"),
    ("GET", "/balance"),
    
    # Settings
    ("GET", "/settings"),
    ("GET", "/config"),
    ("GET", "/preferences"),
]

print("Testing common endpoints...")
print()

for method, path in endpoints:
    test_endpoint(method, path)

print("\n" + "="*60)
print("Exploration complete!")
print("="*60)
