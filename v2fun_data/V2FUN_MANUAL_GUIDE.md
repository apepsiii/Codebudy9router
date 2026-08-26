# V2Fun.ai API Exploration Guide

> Manual guide untuk discover API endpoints dari v2fun.ai

**Date:** 2026-08-26  
**Token Valid Until:** 2026-08-30 06:36:04

---

## 🎯 Your Token Info

```json
{
  "username": "SsZvh0johnston7503@gezon.net",
  "clientType": "web",
  "userid": "2092576809102086146",
  "exp": 1788046564
}
```

**Full Token:**
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6IlNzWnZoMGpvaG5zdG9uNzUwM0BnZXpvbi5uZXQiLCJjbGllbnRUeXBlIjoid2ViIiwidXNlcmlkIjoiMjA5MjU3NjgwOTEwMjA4NjE0NiIsImV4cCI6MTc4ODA0NjU2NH0.c9CszVX-sQoep0XmNCjH73wCiv98NDv2vscJRCqq8no
```

---

## 📋 Manual Exploration Steps

### Step 1: Open Browser DevTools

1. Open Chrome/Edge browser
2. Press `F12` to open DevTools
3. Go to **Network** tab
4. Check "Preserve log"
5. Filter by "Fetch/XHR" only

### Step 2: Navigate v2fun.ai

Visit: https://v2fun.ai/

Look for these API calls in Network tab:

#### On Page Load
- User info API
- Config/settings API
- Model list API

#### When Using Chat
- Start conversation API
- Send message API
- Get response API
- Model selection API

#### Profile/Settings
- User quota/usage API
- Settings API
- Profile API

---

## 🔍 What to Record

For each API call, document:

### 1. Request Info
```
Method: GET/POST/PUT/DELETE
URL: https://api.prod.v2fun.ai/...
Query Params: token=xxx&other=yyy
Headers:
  - Authorization: Bearer xxx
  - Content-Type: application/json
Body (if POST):
  {...}
```

### 2. Response Info
```
Status: 200
Body:
  {...}
```

---

## 📝 Documentation Template

Copy this and fill in for each endpoint you find:

```markdown
### Endpoint Name

**Purpose:** What this API does

**Request:**
- Method: GET/POST
- URL: https://api.prod.v2fun.ai/path/here
- Auth: token query param / Bearer header
- Body (if POST):
```json
{
  "key": "value"
}
```

**Response:**
```json
{
  "success": true,
  "data": {...}
}
```

**Example curl:**
```bash
curl -X GET "https://api.prod.v2fun.ai/path?token=YOUR_TOKEN" \
  -H "Origin: https://v2fun.ai"
```
```

---

## 🎯 Priority Endpoints to Find

### High Priority
1. ✅ **SSE Endpoint** (Already found)
   ```
   GET /ums/external/sse?token=xxx
   ```

2. **Chat/Conversation**
   - Create conversation
   - Send message
   - Get messages
   - List conversations

3. **Models**
   - List available models
   - Get model info

4. **User Info**
   - Get user profile
   - Get usage/quota
   - Get credits/balance

### Medium Priority
5. **Settings**
   - Get settings
   - Update settings

6. **History**
   - Get chat history
   - Export conversations

---

## 🛠️ Testing Found APIs

Once you find an endpoint, test it with:

```bash
# Example
curl -X GET "https://api.prod.v2fun.ai/YOUR_ENDPOINT?token=eyJhbGc..." \
  -H "Accept: application/json" \
  -H "Origin: https://v2fun.ai"
```

Or use Python:

```python
import requests

TOKEN = "eyJhbGc..."
BASE = "https://api.prod.v2fun.ai"

resp = requests.get(
    f"{BASE}/YOUR_ENDPOINT",
    params={"token": TOKEN},
    headers={"Origin": "https://v2fun.ai"}
)

print(resp.status_code)
print(resp.json())
```

---

## 📊 Share Your Findings

After exploring, share in this format:

```
=== V2Fun.ai API Findings ===

1. User Info
   GET /api/user/profile?token=xxx
   Response: {...}

2. Chat Create
   POST /api/chat/create?token=xxx
   Body: {"model": "xxx", "message": "xxx"}
   Response: {...}

3. Model List
   GET /api/models?token=xxx
   Response: [{...}]

... etc
```

---

## 🚀 Next Steps After Discovery

Once you have the API endpoints documented:

1. **Create API client** - Python class to interact with v2fun.ai API
2. **Test automation** - Register new accounts, get tokens
3. **Usage automation** - Create conversations, send messages
4. **Token management** - Store tokens, check expiry
5. **Export functionality** - Save conversations, export data

---

## 💡 Quick Start (What We Know)

```python
import requests

TOKEN = "eyJhbGc..."
BASE_URL = "https://api.prod.v2fun.ai"

# Known working endpoint
def test_sse():
    import sseclient  # pip install sseclient-py
    url = f"{BASE_URL}/ums/external/sse?token={TOKEN}"
    resp = requests.get(url, stream=True, headers={
        "Accept": "text/event-stream",
        "Origin": "https://v2fun.ai"
    })
    client = sseclient.SSEClient(resp)
    for event in client.events():
        print(event.event, event.data)

# Template for testing other endpoints
def test_endpoint(path, method="GET", data=None):
    url = f"{BASE_URL}{path}"
    params = {"token": TOKEN}
    headers = {"Origin": "https://v2fun.ai"}
    
    if method == "GET":
        resp = requests.get(url, params=params, headers=headers)
    elif method == "POST":
        resp = requests.post(url, params=params, json=data, headers=headers)
    
    print(f"{resp.status_code} - {resp.text[:200]}")
    return resp.json() if resp.status_code == 200 else None
```

---

## 📞 Need Help?

If you find API endpoints but need help with:
- Creating automation
- Parsing responses
- Building client library
- Testing at scale

Just share the discovered endpoints and I'll help build the automation!

---

**Status:** Waiting for manual API discovery  
**Action:** Explore v2fun.ai with DevTools, document APIs found  
**Goal:** Build automation once APIs are known
