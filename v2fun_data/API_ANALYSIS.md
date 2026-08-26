# V2Fun.ai API Analysis

**Date:** 2026-08-26  
**Source:** Network capture analysis from browser inspection  
**Capture Files:** 4 JSON files (190KB - 266KB each)

---

## 📊 Summary Statistics

| Metric | Value |
|--------|-------|
| **Total Requests** | 92 |
| **HTTP Methods** | GET: 85, POST: 7 |
| **V2Fun API Endpoints** | 2 |
| **Analytics Endpoints** | 15+ (Google) |
| **Framework** | Nuxt.js (Vue SSR) |
| **Primary Domain** | v2fun.ai |
| **API Domain** | api.prod.v2fun.ai |

---

## 🎯 Discovered V2Fun Endpoints

### 1. Article Slot API (Landing Page Content)
```
GET https://api.prod.v2fun.ai/article/slot/get-by-entrance-code?lan=en
```

**Purpose:** Fetch landing page content slots  
**Method:** GET  
**Parameters:**
- `lan` - Language code (e.g., `en`, `id`)

**Headers:**
```javascript
{
  "sec-ch-ua-platform": "Windows",
  "referer": "https://v2fun.ai/",
  "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
  "sec-ch-ua": "Chromium;v=151, Not=A?Brand;v=99",
  "sec-ch-ua-mobile": "?0"
}
```

**Status:** ✅ Confirmed working  
**Authentication:** None required (public endpoint)  
**Response:** JSON (content slots for homepage)

---

### 2. Internationalization API
```
GET https://v2fun.ai/api/i18n/messages/en
```

**Purpose:** Get translation messages for the app  
**Method:** GET  
**Language Codes:** `en`, `id`, etc.

**Headers:** Same as above

**Status:** ✅ Confirmed working  
**Authentication:** None required  
**Response:** JSON (translation strings)

---

## 🔍 Missing Endpoints (Need Discovery)

Based on typical AI 3D model generator functionality, these endpoints likely exist but weren't captured in landing page visit:

### Authentication & User Management
```
POST /auth/login
POST /auth/register
POST /auth/logout
GET /auth/me
POST /auth/refresh-token
```

### 3D Model Generation
```
POST /generate/text-to-3d          # Generate from text prompt
POST /generate/image-to-3d         # Generate from image
GET /generate/status/{job_id}      # Check generation status
GET /generate/result/{job_id}      # Get generated model
```

### User Content
```
GET /user/models                   # List user's models
GET /user/profile                  # Get user profile
DELETE /user/models/{id}           # Delete model
```

### Model Management
```
GET /models/{id}                   # Get model details
GET /models/{id}/download          # Download model file
POST /models/{id}/publish          # Publish to gallery
```

---

## 🛠️ Technology Stack Detected

### Frontend
- **Framework:** Nuxt.js 3.x (Vue.js SSR)
- **Build:** Vite/Webpack
- **Assets Path:** `/_nuxt/`
- **Fonts:** Inter (18pt Regular, Medium, Bold)
- **Icons:** Custom iconfont

### Backend
- **API Domain:** `api.prod.v2fun.ai`
- **Environment:** Production
- **Protocol:** HTTPS only

### Analytics & Tracking
- Google Analytics 4 (G-BH37PP25E7)
- Google Ads Conversion (17932665720, 18327802436)
- Google Tag Manager

---

## 🔐 Authentication Flow (Hypothesis)

Based on standard patterns, likely authentication:

1. **OAuth/Social Login:**
   - Google Sign-In
   - Possibly Discord, GitHub, etc.

2. **JWT Tokens:**
   - Access token in Authorization header
   - Refresh token in HTTP-only cookie

3. **Session Management:**
   - Cookies: `session`, `token`, `refresh_token`
   - Local Storage: User data, preferences

---

## 📝 Request Pattern Analysis

### Standard Headers Required
```javascript
{
  "Content-Type": "application/json",
  "Accept": "application/json",
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
  "Referer": "https://v2fun.ai/",
  "Origin": "https://v2fun.ai"
}
```

### Authenticated Requests (Hypothesis)
```javascript
{
  "Authorization": "Bearer <access_token>",
  "Content-Type": "application/json",
  "Accept": "application/json"
}
```

---

## 🎯 Next Steps for Full Discovery

### 1. Manual Browser Inspection (HIGH PRIORITY)
**Action:**
1. Open https://v2fun.ai/ in browser
2. Open DevTools (F12) → Network tab
3. Filter: XHR/Fetch requests only
4. Perform these actions:
   - Click "Sign Up" / "Login"
   - Create account or login
   - Generate a 3D model (text-to-3D)
   - View profile
   - Download model
   - Check gallery

**Capture:** All API calls during these actions

### 2. Authentication Testing
```bash
# Test with Playwright
python v2fun_scripts/v2fun_interactive_discovery.py

# Login and capture session
# Extract cookies/tokens
# Test authenticated endpoints
```

### 3. API Response Analysis
- Document request/response schemas
- Identify required fields
- Map error responses
- Find rate limits

### 4. Automation Implementation
Once endpoints are known:
```python
class V2FunAPI:
    def __init__(self, token=None):
        self.base_url = "https://api.prod.v2fun.ai"
        self.token = token
    
    def generate_3d_model(self, prompt):
        """Generate 3D model from text"""
        pass
    
    def get_generation_status(self, job_id):
        """Check generation status"""
        pass
    
    def download_model(self, model_id):
        """Download generated model"""
        pass
```

---

## 📊 Endpoint Discovery Progress

| Category | Found | Total (Est.) | Progress |
|----------|-------|--------------|----------|
| **Public** | 2 | 5 | 40% |
| **Auth** | 0 | 5 | 0% |
| **Generation** | 0 | 4 | 0% |
| **User Content** | 0 | 5 | 0% |
| **Model Management** | 0 | 4 | 0% |
| **Total** | **2** | **23** | **~9%** |

---

## 🔧 Tools for Discovery

### 1. Browser DevTools
```
Chrome/Edge DevTools → Network → XHR/Fetch
- Filter by: api.prod.v2fun.ai
- Export as HAR
- Analyze with har-analyzer
```

### 2. Playwright Network Capture
```python
# Already created: capture_v2fun_api.py
python v2fun_scripts/capture_v2fun_api.py
```

### 3. Postman/Insomnia
- Import HAR file
- Test endpoints
- Document responses
- Generate code snippets

### 4. Network Proxy
```bash
# Use mitmproxy or Charles Proxy
mitmproxy --mode reverse:https://api.prod.v2fun.ai --listen-port 8080
```

---

## ⚠️ Challenges & Notes

### Challenges
1. **Limited Landing Page Discovery** - Most endpoints require user actions
2. **Authentication Required** - Need valid session for most features
3. **Rate Limiting** - Likely present, unknown limits
4. **WebSocket Usage** - May use WS for real-time generation updates

### Notes
- Site uses Nuxt.js SSR - some data hydrated server-side
- Heavy analytics tracking (15+ Google tracking calls)
- No visible API documentation
- No robots.txt or sitemap.xml found

### Best Practices
- Use realistic User-Agent
- Respect rate limits
- Don't hammer endpoints
- Use stealth mode for automation

---

## 📁 Related Files

- **Capture Data:** `v2fun_capture_20260826_191008.json` (primary)
- **Scripts:** `v2fun_scripts/`
- **Docs:** `V2FUN_API_DISCOVERY.md`, `V2FUN_MANUAL_GUIDE.md`

---

## 🎓 Key Learnings

### What Worked
✅ Playwright network capture successfully captured all requests  
✅ Identified API domain structure (`api.prod.v2fun.ai`)  
✅ Found public endpoints without authentication  
✅ Detected technology stack (Nuxt.js)

### What's Needed
⏳ Manual interaction to trigger authenticated endpoints  
⏳ Account creation to test full user flow  
⏳ Model generation to find core API endpoints  
⏳ Token/cookie extraction for automation

---

**Status:** 🟡 Discovery Phase - 9% Complete  
**Next Action:** Manual browser inspection with DevTools (see Next Steps #1)  
**Updated:** 2026-08-26
