# V2Fun.ai API Discovery

## Token Info

```
JWT Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Payload:
  - username: SsZvh0johnston7503@gezon.net
  - clientType: web
  - userid: 2092576809102086146
  - exp: 1788046564 (2026-08-30 06:36:04)
```

## Known Working Endpoint

### SSE (Server-Sent Events)
```
GET https://api.prod.v2fun.ai/ums/external/sse?token=<JWT>
Status: 200 OK
Response: text/event-stream
Content: heartbeat pings

event:heartbeat
data:ping
```

## Exploration Results

### Tested Endpoints (All 404)

**UMS (User Management Service):**
- `/ums/user/info` - 404
- `/ums/user/profile` - 404
- `/ums/user/current` - 404
- `/ums/account/info` - 404
- `/ums/external/user` - 404
- `/ums/external/profile` - 404

**Chat/Conversation:**
- `/chat/conversations` - 404
- `/chat/history` - 404
- `/api/chat/list` - 404
- `/api/conversation/list` - 404

**Models/Usage:**
- `/model/list` - 404
- `/usage` - 404
- `/credits` - 404

## Next Steps

### Option 1: Browser Network Inspection
Use browser DevTools to capture actual API calls:
1. Open https://v2fun.ai/
2. Login with token
3. Open DevTools (F12) → Network tab
4. Interact with the site
5. Record all API calls

### Option 2: Use Playwright to Capture Network
```python
from playwright.async_api import async_playwright

async def capture_api_calls():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Listen to all network requests
        page.on("request", lambda req: print(f"→ {req.method} {req.url}"))
        page.on("response", lambda resp: print(f"← {resp.status} {resp.url}"))
        
        # Navigate and interact
        await page.goto("https://v2fun.ai/")
        # ... interact with site
        
        input("Press Enter when done...")
        await browser.close()
```

### Option 3: Check Common AI Platform Patterns

Based on similar platforms, likely endpoints might be:
- `/api/v1/chat/completions`
- `/api/v1/models`
- `/api/user/quota`
- `/api/user/usage`
- `/llm/chat`
- `/conversation/create`

## Recommendations

**Action Required:**
1. Open v2fun.ai in browser with DevTools
2. Navigate through the interface:
   - Dashboard
   - Chat/conversation
   - Settings
   - Profile
3. Capture all API calls
4. Document the actual endpoints
5. Document request/response format

**What to Look For:**
- Authentication method (Bearer token, cookie, query param)
- API base paths
- Request payload structure
- Response data structure
- Available models
- Usage/quota endpoints

## Notes

- Token expires: 2026-08-30 06:36:04
- Token must be included as `?token=<JWT>` query parameter
- Response format: JSON
- Base URL: `https://api.prod.v2fun.ai`
- Origin: `https://v2fun.ai`

---

**Status:** Need browser inspection to discover actual API endpoints
**Last Updated:** 2026-08-26
