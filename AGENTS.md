# AGENTS.md - V2Fun.ai API Automation Project

**Project:** V2Fun.ai API Exploration & Automation  
**Repository:** https://github.com/apepsiii/Codebudy9router  
**Focus:** API Discovery, Authentication Flow, 3D Model Generation Automation  
**Last Updated:** 2026-08-26

---

## 🎯 Project Overview

This project focuses on exploring and automating the V2Fun.ai API - an AI-powered 3D model generator. The goal is to discover API endpoints, map authentication flows, and build automation tools for programmatic 3D model generation.

**Key Objectives:**
1. Discover all V2Fun.ai API endpoints
2. Map authentication and authorization flows
3. Build Python automation client for 3D generation
4. Document API schemas and responses
5. Create reusable automation tools

---

## 📊 Current Status

| Aspect | Status | Progress |
|--------|--------|----------|
| **API Discovery** | 🔄 In Progress | 9% (2/23 endpoints) |
| **Authentication** | ⏳ Pending | 0% |
| **Core API (Generation)** | ⏳ Pending | 0% |
| **Automation Client** | ⏳ Pending | 0% |
| **Documentation** | ✅ Complete | 100% |

**Phase:** Discovery & Analysis  
**Next Milestone:** Complete authentication flow capture

---

## 🏗️ Project Structure

```
Codebudy9router/
├── v2fun_scripts/              # Automation & exploration tools
│   ├── v2fun_interactive_discovery.py  # Main discovery tool
│   ├── capture_v2fun_api.py            # Network capture
│   ├── capture_v2fun_simple.py         # Simple capture
│   ├── explore_v2fun.py                # API testing
│   ├── explore_v2fun_v2.py             # Token-based testing
│   └── run_v2fun_discovery.bat         # Windows launcher
│
├── v2fun_data/                 # Data & documentation
│   ├── API_ANALYSIS.md                 # Comprehensive analysis ⭐
│   ├── V2FUN_API_DISCOVERY.md          # API findings
│   ├── V2FUN_DISCOVERY_HOWTO.md        # How-to guide
│   ├── V2FUN_MANUAL_GUIDE.md           # Manual inspection
│   ├── v2fun_capture_*.json            # 4 capture files (265KB)
│   └── v2fun_endpoints.txt             # Endpoint list
│
├── archive/                    # Archived projects
│   ├── codebuddy/              # CodeBuddy automation (80% complete)
│   └── kiro/                   # Kiro token generator (production)
│
├── README.md                   # Main documentation
├── CLEANUP_SUMMARY.md          # Reorganization docs
└── requirements.txt            # Dependencies
```

---

## 🔍 Discovered Endpoints

### Base URL
```
https://api.prod.v2fun.ai/
```

### Public Endpoints (No Auth Required)

#### 1. Article Slot API
```http
GET /article/slot/get-by-entrance-code?lan=en
```
**Purpose:** Fetch landing page content slots  
**Parameters:** `lan` (language code: en, id, etc.)  
**Response:** JSON with article slots  
**Status:** ✅ Verified

#### 2. Internationalization API
```http
GET https://v2fun.ai/api/i18n/messages/en
```
**Purpose:** Get translation messages  
**Parameters:** Language code in path  
**Response:** JSON with i18n strings  
**Status:** ✅ Verified

---

## 🔐 Authentication (To Be Discovered)

**Expected Endpoints:**
```http
POST /auth/login
POST /auth/register
POST /auth/logout
GET /auth/me
POST /auth/refresh-token
POST /auth/google
POST /auth/discord
```

**Expected Flow:**
1. User registers/logs in via OAuth or email
2. Server returns JWT access token + refresh token
3. Access token in `Authorization: Bearer <token>` header
4. Refresh token stored in HTTP-only cookie
5. Token refresh before expiry

**Action Items for AI Agent:**
- [ ] Manual browser inspection with DevTools
- [ ] Capture login/register flow
- [ ] Extract token format and storage location
- [ ] Test token validation and refresh
- [ ] Document authentication headers

---

## 🎨 3D Generation API (To Be Discovered)

**Expected Core Endpoints:**
```http
POST /generate/text-to-3d
POST /generate/image-to-3d
GET /generate/status/{job_id}
GET /generate/result/{job_id}
POST /generate/cancel/{job_id}
```

**Expected Flow:**
1. Submit generation request (text or image)
2. Receive job_id
3. Poll status endpoint
4. Download result when complete

**Request Schema (Hypothesis):**
```json
{
  "prompt": "a red sports car",
  "quality": "high",
  "style": "realistic",
  "format": "glb"
}
```

**Response Schema (Hypothesis):**
```json
{
  "job_id": "uuid",
  "status": "processing",
  "progress": 45,
  "estimated_time": 30
}
```

**Action Items for AI Agent:**
- [ ] Login to V2Fun.ai
- [ ] Trigger text-to-3D generation
- [ ] Capture all API calls in DevTools
- [ ] Document request/response schemas
- [ ] Test different parameters
- [ ] Map error responses

---

## 🛠️ Technology Stack

### Frontend
- **Framework:** Nuxt.js 3.x (Vue.js SSR)
- **Build Tool:** Vite
- **Assets:** `/_nuxt/` path structure
- **Styling:** Tailwind CSS (likely)
- **Fonts:** Inter (18pt Regular, Medium, Bold)

### Backend
- **API Domain:** api.prod.v2fun.ai
- **Environment:** Production
- **Protocol:** HTTPS only
- **Authentication:** JWT (hypothesis)

### Our Tools
- **Language:** Python 3.8+
- **Automation:** Playwright + playwright-stealth
- **HTTP Client:** requests / httpx
- **CLI UI:** Rich console
- **Data Format:** JSON

---

## 📝 AI Agent Instructions

### Phase 1: API Discovery (Current)

**Task:** Discover all API endpoints through manual inspection

**Steps:**
1. Open https://v2fun.ai/ in Playwright browser
2. Enable DevTools network capture
3. Filter XHR/Fetch requests only
4. Perform these actions:
   - Click "Login" → Capture auth endpoints
   - Register new account → Capture registration flow
   - Generate 3D model from text → Capture generation API
   - Check generation status → Capture polling endpoints
   - Download model → Capture download endpoints
   - View profile → Capture user endpoints
   - Browse gallery → Capture public endpoints
5. Export all captured requests to JSON
6. Analyze and document each endpoint

**Script to Use:**
```bash
python v2fun_scripts/v2fun_interactive_discovery.py
```

**Expected Output:**
- `v2fun_capture_YYYYMMDD_HHMMSS.json` with all requests
- Updated `v2fun_endpoints.txt` with new endpoints
- Updated `API_ANALYSIS.md` with schemas

---

### Phase 2: Authentication Implementation

**Task:** Implement authentication flow

**Steps:**
1. Analyze captured auth endpoints
2. Extract token format (JWT structure)
3. Identify token storage location (cookies/localStorage)
4. Implement login function:
   ```python
   def login(email: str, password: str) -> dict:
       """Login and return tokens"""
       # POST to /auth/login
       # Extract access_token and refresh_token
       # Store tokens for future requests
       return {"access_token": "...", "refresh_token": "..."}
   ```
5. Implement token refresh:
   ```python
   def refresh_token(refresh_token: str) -> str:
       """Refresh access token"""
       # POST to /auth/refresh-token
       # Return new access_token
   ```
6. Test with real credentials
7. Document in `AUTH_FLOW.md`

**Expected Files:**
- `v2fun_scripts/auth.py` - Authentication module
- `v2fun_data/AUTH_FLOW.md` - Documentation
- `v2fun_data/tokens_example.json` - Token format example

---

### Phase 3: Core API Implementation

**Task:** Build 3D generation automation

**Steps:**
1. Analyze captured generation endpoints
2. Implement V2FunClient class:
   ```python
   class V2FunClient:
       def __init__(self, token: str):
           self.token = token
           self.base_url = "https://api.prod.v2fun.ai"
       
       def generate_3d(self, prompt: str, **kwargs) -> str:
           """Generate 3D model, return job_id"""
           pass
       
       def get_status(self, job_id: str) -> dict:
           """Check generation status"""
           pass
       
       def download_model(self, job_id: str, output_path: str):
           """Download generated model"""
           pass
   ```
3. Implement progress tracking with Rich
4. Add error handling and retry logic
5. Test with multiple prompts
6. Document in `CLIENT_API.md`

**Expected Files:**
- `v2fun_scripts/client.py` - Main API client ⭐
- `v2fun_data/CLIENT_API.md` - Usage documentation
- `examples/generate_model.py` - Usage example

---

### Phase 4: Automation Tools

**Task:** Build user-facing automation scripts

**Tools to Create:**

1. **Batch Generator** (`batch_generate.py`)
   - Read prompts from file
   - Generate multiple models
   - Download all results
   - Report statistics

2. **Monitor** (`monitor_generation.py`)
   - Real-time progress tracking
   - Rich console UI
   - Notifications on completion

3. **Gallery Scraper** (`scrape_gallery.py`)
   - Browse public gallery
   - Extract model metadata
   - Download popular models

4. **CLI Tool** (`v2fun_cli.py`)
   - Command-line interface
   - All features accessible via CLI
   - Example: `v2fun generate "a red car"`

---

## 🎯 Success Criteria

### Phase 1: Discovery (Current)
- [ ] Find all authentication endpoints
- [ ] Find all generation endpoints
- [ ] Find all user management endpoints
- [ ] Document request/response schemas
- [ ] Map error codes and responses

### Phase 2: Authentication
- [ ] Working login function
- [ ] Token refresh implementation
- [ ] Session management
- [ ] Error handling

### Phase 3: Core API
- [ ] Working 3D generation
- [ ] Status polling with progress
- [ ] Model download
- [ ] Comprehensive error handling

### Phase 4: Tools
- [ ] Batch generation tool
- [ ] CLI interface
- [ ] Documentation
- [ ] Example scripts

---

## 📊 Progress Tracking

| Endpoint Category | Found | Total (Est.) | Progress |
|-------------------|-------|--------------|----------|
| Public | 2 | 5 | 40% |
| Authentication | 0 | 5 | 0% |
| Generation | 0 | 4 | 0% |
| User Management | 0 | 5 | 0% |
| Model Management | 0 | 4 | 0% |
| **Total** | **2** | **23** | **9%** |

---

## 🔧 Development Guidelines

### Code Style
- Follow PEP 8
- Use type hints
- Document all functions
- Write descriptive variable names
- Add error handling

### Error Handling
```python
try:
    response = requests.post(url, json=data)
    response.raise_for_status()
except requests.HTTPError as e:
    if e.response.status_code == 401:
        # Handle authentication error
    elif e.response.status_code == 429:
        # Handle rate limit
    else:
        # Handle other errors
```

### Logging
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info(f"Starting generation for prompt: {prompt}")
logger.error(f"Failed to generate: {error}")
```

### Testing
- Test with valid inputs
- Test with invalid inputs
- Test error scenarios
- Test rate limiting
- Document all tests

---

## 📚 Key Files for AI Agent

### Must Read First
1. `README.md` - Project overview
2. `v2fun_data/API_ANALYSIS.md` - Current findings ⭐
3. `v2fun_data/V2FUN_DISCOVERY_HOWTO.md` - Discovery guide

### Tools to Use
1. `v2fun_scripts/v2fun_interactive_discovery.py` - Main tool ⭐
2. `v2fun_scripts/capture_v2fun_api.py` - Network capture

### Output Files
1. `v2fun_data/v2fun_capture_*.json` - Captured requests
2. `v2fun_data/v2fun_endpoints.txt` - Endpoint list
3. `v2fun_data/API_ANALYSIS.md` - Analysis results

---

## ⚠️ Important Notes

### Rate Limiting
- V2Fun likely has rate limits
- Don't hammer endpoints
- Add delays between requests
- Implement exponential backoff

### Authentication
- Never commit tokens/credentials
- Store in environment variables
- Use `.env` file (gitignored)
- Rotate tokens regularly

### Legal & Ethics
- Respect Terms of Service
- Don't abuse the API
- This is for learning purposes
- Use responsibly

### Best Practices
- Use realistic User-Agent
- Mimic browser behavior
- Add random delays
- Handle errors gracefully
- Log all operations

---

## 🤝 Collaboration

### When Adding New Endpoints
1. Document in `API_ANALYSIS.md`
2. Add to `v2fun_endpoints.txt`
3. Update progress table
4. Add usage example
5. Commit with clear message

### When Creating New Scripts
1. Add to `v2fun_scripts/`
2. Add docstring with usage
3. Update README with description
4. Create example in comments
5. Test thoroughly before commit

### Git Workflow
```bash
# Feature branch
git checkout -b feature/auth-implementation

# Commit frequently
git add .
git commit -m "feat: implement login function"

# Push and create PR
git push origin feature/auth-implementation
```

---

## 📞 Support & Resources

### Documentation
- Main docs in `v2fun_data/`
- Code examples in scripts
- Inline comments in code

### Tools
- Playwright for automation
- Rich for beautiful CLI
- Requests for HTTP calls
- JSON for data handling

### External Resources
- V2Fun.ai website: https://v2fun.ai/
- Playwright docs: https://playwright.dev/python/
- Rich docs: https://rich.readthedocs.io/

---

## 🎉 Summary

**Current State:** API discovery phase, 9% complete  
**Next Action:** Manual browser inspection with DevTools  
**Expected Duration:** 1-2 hours for full endpoint discovery  
**Final Goal:** Complete Python automation client for V2Fun.ai

**AI Agent, your mission is to:**
1. 🔍 Discover all API endpoints
2. 🔐 Implement authentication
3. 🎨 Build 3D generation automation
4. 📦 Create user-friendly tools
5. 📚 Document everything

Good luck! 🚀

---

**Version:** 1.0.0  
**Last Updated:** 2026-08-26  
**Maintainer:** apepsiii
