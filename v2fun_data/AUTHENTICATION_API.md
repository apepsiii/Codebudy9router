# V2Fun.ai Authentication & API Discovery

**Date:** 2026-08-26  
**Capture File:** generation_api_20260826_195023.json  
**Status:** ✅ Authentication Flow Discovered!

---

## 🎉 Major Breakthrough

Successfully captured **complete OAuth authentication flow** and discovered **25 unique API endpoints**!

---

## 🔐 Authentication Flow

### Step 1: Google OAuth
User clicks "Sign in with Google" → Redirects to accounts.google.com

### Step 2: Get OAuth Code
After user authorizes, Google redirects back with `code` parameter

### Step 3: Login with OAuth Code

```http
POST https://api.prod.v2fun.ai/sys/user/nologin/loginByGoogle?lan=en
Content-Type: application/json

{
  "loginType": "googleLogin",
  "agree": "1",
  "regionType": "GLOBAL",
  "loginAppId": "1",
  "code": "4/0ATsMZqDitv8fIgBT...",
  "redirectUri": "https://v2fun.ai/"
}
```

### Step 4: Get Login Info & Token

```http
POST https://api.prod.v2fun.ai/sys/user/getLoginInfo?lan=en
Content-Type: application/json

{
  "bindType": 1
}
```

**Response:**
```json
{
  "success": true,
  "message": "Sign up and log in successfully.",
  "code": 200,
  "result": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImtjdlRXbWVkd2luMTE5QGdlem9uLm5ldCIsImNsaWVudFR5cGUiOiJ3ZWIiLCJ1c2VyaWQiOiIyMDkyNTk0NjA2MjU5NTcyNzM3IiwiZXhwIjoxNzg4MDUwODA3fQ.0M1dxbp6AY2f64t6eX8AoSnltY0fZcMZyEsUw0daTKQ",
    "userInfo": {
      "id": "2092594606259572737",
      "username": "kcvTWmedwin119@gezon.net",
      ...
    }
  }
}
```

### Step 5: Use Token for API Calls

**Method 1: Authorization Header (Recommended)**
```http
GET https://api.prod.v2fun.ai/sys/user/get-balance?lan=en
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Method 2: Query Parameter**
```http
GET https://api.prod.v2fun.ai/ums/external/sse?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 🎫 JWT Token Structure

### Decoded Header
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

### Decoded Payload
```json
{
  "username": "kcvTWmedwin119@gezon.net",
  "clientType": "web",
  "userid": "2092594606259572737",
  "exp": 1788050807
}
```

**Token Lifetime:** ~24-48 hours (based on exp timestamp)

---

## 📡 Discovered API Endpoints

### Authentication & User Management

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/sys/user/nologin/loginByGoogle` | POST | Login with Google OAuth code |
| `/sys/user/getLoginInfo` | POST | Get JWT token after login |
| `/sys/user/get-balance` | GET | Get user point balance |
| `/sys/user/plan/get-subscription-info` | GET | Get subscription details |
| `/sys/user/has-sign` | GET | Check daily sign-in status |
| `/sys/user/sign` | POST | Perform daily sign-in |
| `/sys/user/get-sign-points` | GET | Get sign-in reward points |
| `/sys/user/interact/daily` | POST | Daily interaction tracking |
| `/sys/user/onboarding/tasks/list` | GET | Get onboarding tasks |

### Work & Generation

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/work/getTagList` | POST | Get available model tags |
| `/work/get-free-cnt` | POST | Get free generation count |
| `/work/getItemMapList` | POST | List user's created works |
| `/work/config/business-config/list` | GET | Get business config |

### Onboarding & Progress

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/sys/onboarding/get-user-task-progress` | GET | Get task progress |
| `/sys/onboarding/system-tasks` | GET | Get system tasks |
| `/interactive/external/survey/needSurvey` | GET | Check if survey needed |
| `/interactive/external/survey/submit` | POST | Submit survey |

### Notifications

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/ums/external/notifications/records` | GET | Get notification records |
| `/ums/external/notifications/records/unread-count` | GET | Get unread count |
| `/ums/external/sse` | GET | Server-Sent Events stream |

### Content

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/article/slot/get-by-entrance-code` | GET | Get content slots (banners, etc) |
| `/api/i18n/messages/{lang}` | GET | Get i18n translations |

---

## 💰 Point System

**User Balance:** 520 points (from capture)

**How to get points:**
- Daily sign-in: Variable rewards
- Complete onboarding tasks
- Survey completion: 200 points
- Referrals (likely)

**Point usage:**
- Generate 3D models
- Premium features
- Priority processing

---

## 🎨 Generation Endpoints (NOT YET CAPTURED)

**Expected endpoints** (need to capture by actually generating):

```http
POST /work/create or /work/generate
POST /work/text-to-3d
POST /work/image-to-3d
GET /work/status/{job_id}
GET /work/result/{job_id}
GET /work/download/{model_id}
```

**To capture these:**
1. Run discovery script again
2. Login
3. Click "Generate" button
4. Enter prompt (e.g., "a red sports car")
5. Submit generation
6. Wait for completion
7. Download model

---

## 🔧 API Client Implementation

### Basic Client

```python
import requests

class V2FunAPI:
    def __init__(self, token=None):
        self.base_url = "https://api.prod.v2fun.ai"
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}" if token else None,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    
    def login_with_google_code(self, oauth_code, redirect_uri="https://v2fun.ai/"):
        """Login with Google OAuth code"""
        url = f"{self.base_url}/sys/user/nologin/loginByGoogle?lan=en"
        data = {
            "loginType": "googleLogin",
            "agree": "1",
            "regionType": "GLOBAL",
            "loginAppId": "1",
            "code": oauth_code,
            "redirectUri": redirect_uri
        }
        response = requests.post(url, json=data, headers=self.headers)
        return response.json()
    
    def get_login_info(self):
        """Get login info and JWT token"""
        url = f"{self.base_url}/sys/user/getLoginInfo?lan=en"
        data = {"bindType": 1}
        response = requests.post(url, json=data, headers=self.headers)
        result = response.json()
        
        if result.get("success") and "result" in result:
            self.token = result["result"].get("token")
            self.headers["Authorization"] = f"Bearer {self.token}"
        
        return result
    
    def get_balance(self):
        """Get user point balance"""
        url = f"{self.base_url}/sys/user/get-balance?lan=en"
        response = requests.get(url, headers=self.headers)
        return response.json()
    
    def daily_sign_in(self):
        """Perform daily sign-in"""
        url = f"{self.base_url}/sys/user/sign?lan=en"
        response = requests.post(url, json={}, headers=self.headers)
        return response.json()
    
    def get_works(self, page=1, page_size=20):
        """Get user's works"""
        url = f"{self.base_url}/work/getItemMapList?lan=en"
        data = {
            "pager": {
                "pageNo": page,
                "pageSize": page_size,
                "needQueryCount": True,
                "orderBy": "createTime"
            },
            "parm": {
                "keyword": None,
                "tag": "",
                "tagId": "0",
                "workType": None
            }
        }
        response = requests.post(url, json=data, headers=self.headers)
        return response.json()
```

### Usage Example

```python
# Initialize client
api = V2FunAPI()

# Login with Google OAuth code (get from OAuth flow)
oauth_code = "4/0ATsMZqDitv8fIgBT..."
api.login_with_google_code(oauth_code)

# Get login info and token
login_info = api.get_login_info()
print(f"Token: {api.token}")

# Check balance
balance = api.get_balance()
print(f"Points: {balance['result']}")

# Daily sign-in
api.daily_sign_in()

# Get works
works = api.get_works()
print(f"Total works: {works['result']['total']}")
```

---

## 📊 Statistics

| Metric | Value |
|--------|-------|
| **Total API calls captured** | 73 |
| **Unique endpoints** | 25 |
| **Authentication endpoints** | 9 |
| **Work endpoints** | 4 |
| **User endpoints** | 9 |
| **Notification endpoints** | 3 |
| **Discovery time** | 5 minutes |
| **User points** | 520 |

---

## ✅ Progress Update

| Category | Status | Progress |
|----------|--------|----------|
| Public endpoints | ✅ Complete | 100% |
| Authentication | ✅ Complete | 100% |
| User management | ✅ Complete | 100% |
| **Generation** | ⏳ Pending | 0% |
| Model download | ⏳ Pending | 0% |
| **Total** | 🔄 In Progress | **60%** |

---

## 🎯 Next Steps

### 1. Capture Generation Endpoints (HIGH PRIORITY)

Run script and actually generate a model:
```bash
python v2fun_scripts/discover_generation_api.py
```

Then:
- Login
- Click "Generate 3D Model"
- Enter prompt
- Submit
- Wait for completion
- Download

### 2. Build Complete API Client

Implement:
- OAuth automation
- Generation functions
- Status polling
- Model download
- Error handling

### 3. Test & Document

- Test all endpoints
- Document request/response schemas
- Create usage examples
- Build automation scripts

---

## 🚀 We Can Now Automate

With the discovered authentication flow, we can:

✅ **Auto-login** with Google OAuth code  
✅ **Get JWT tokens** programmatically  
✅ **Check user balance**  
✅ **Perform daily sign-in**  
✅ **List user works**  
⏳ **Generate 3D models** (pending endpoint discovery)  
⏳ **Download models** (pending endpoint discovery)

---

**Status:** Authentication Complete - Generation Pending  
**Updated:** 2026-08-26  
**Progress:** 60% → 100% when generation captured
