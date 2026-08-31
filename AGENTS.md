# AGENTS.md - V2Fun.ai API Automation Project

**Project:** V2Fun.ai API Exploration & Automation  
**Repository:** https://github.com/apepsiii/Codebudy9router  
**Focus:** API Discovery, Authentication, Image Generation Automation, Web UI  
**Last Updated:** 2026-08-27 12:15 WIB

**Latest Updates:**
- ✅ Fixed GSuite welcome screen handler ("Welcome to your new account")
- ✅ Added admin account management tools (create_admin.py, manage_users.py)
- ✅ Enhanced OAuth popup handling with multiple fallback mechanisms

---

## Project Overview

Automates V2Fun.ai - an AI-powered image/3D model generator. Covers Google OAuth login, API discovery, image generation (CLI + Web UI), database management, and token auto-refresh.

---

## Current Status

| Aspect | Status | Progress |
|--------|--------|----------|
| **API Discovery** | Done | 100% (31 endpoints) |
| **Authentication** | Done | 100% |
| **Google Login Automation** | Done | 100% |
| **Image Generation API** | Done | 100% |
| **CLI Tool** | Done | 100% |
| **Web UI (Full Stack)** | Done | 100% |
| **Database (SQLite)** | Done | 100% |
| **Image Upload to OSS** | Done | 100% |
| **SSE Real-time Monitoring** | Done | 100% |
| **Auto-download Results** | Done | 100% |
| **Token Auto-Refresh** | Done | 100% |
| **Bulk Account Registration** | Done | 100% |

**Phase:** Production Ready  
**Next Milestone:** Batch generation with prompt rotation

---

## Project Structure

```
Codebudy9router/
├── v2fun_scripts/
│   ├── v2fun_google_login.py          # Multi-account Google OAuth login
│   ├── v2fun_cli.py                   # CLI tool for generation
│   ├── v2fun_web_v2.py                # Flask web server (main)
│   ├── database.py                    # SQLite database models
│   ├── sse_monitor.py                 # SSE real-time monitor
│   ├── token_manager.py               # JWT token auto-refresh
│   ├── capture_generation_flow.py     # API network capture tool
│   ├── run_v2fun_login.bat            # Login automation launcher
│
├── create_admin.py                    # Create admin account CLI tool
├── manage_users.py                    # User management CLI (list/create/reset)
├── ADMIN_GUIDE.md                     # Admin account management guide
│   ├── run_capture_generation.bat     # Capture tool launcher
│   └── archive/                       # Old/deprecated scripts
│
├── v2fun_web_v2/
│   └── templates/
│       ├── login.html                 # Login page
│       ├── register.html              # Register page
│       └── dashboard.html             # Main dashboard with SSE
│
├── v2fun_data/
│   ├── v2fun.db                       # SQLite database
│   ├── v2fun_session_*_latest.json    # Saved login tokens
│   ├── v2fun_capture_generation_*.json # Network captures
│   ├── v2fun_generation_api_*.json    # Generation API captures
│   ├── API_GENERATION_ANALYSIS.md     # API documentation
│   ├── uploads/                       # User uploaded reference images
│   ├── generations/                   # Generation result metadata
│   ├── results/                       # Downloaded generated images
│   └── archive/                       # Old docs, captures, tokens
│
├── account.txt                        # Google accounts (gitignored)
├── account.txt.example                # Account format example
├── run_web.bat                        # Web UI launcher
├── requirements.txt                   # Python dependencies
└── README.md
```

---

## Discovered API

### Base URL
```
https://api.prod.v2fun.ai/
```

### Main Generation Endpoint

```http
POST /work/external/generate/image-generate?lan=en
Authorization: {JWT_TOKEN}
X-Access-Token: {JWT_TOKEN}
Content-Type: application/json

{
  "prompt": "your text prompt",
  "model": "nano-banana-pro",
  "ratio": "16:9",
  "num": 1,
  "quality": "medium",
  "referenceImages": ["upload/image/..."]
}
```

### Models Available
- `nano-banana-pro`
- `nano-banana-2`
- `nano-banana-2-lite`
- `gpt-image-2`
- `qwen-image`

### Image Sizes
- `1:1` Square
- `16:9` Landscape
- `9:16` Portrait
- `4:3`
- `3:4`

### All Discovered Endpoints (31 total)

**Work/Generation:**
- `POST /work/external/generate/image-generate` - Main generation
- `POST /work/ai/images/getPromptEnhancement` - AI prompt enhance
- `POST /work/getResourceList` - Resource list
- `POST /work/get-free-cnt` - Free credits check
- `POST /work/get-retry-cnt` - Retry count
- `GET /work/config/business-config/list` - Model configs

**Authentication & User:**
- `POST /sys/user/getLoginInfo` - Get user info
- `GET /sys/user/get-balance` - Credit balance
- `GET /sys/user/has-sign` - Daily sign check
- `POST /sys/user/interact/daily` - Daily interaction
- `GET /sys/user/plan/get-subscription-info` - Subscription info
- `POST /sys/oss/nologin/getAliSTS` - OSS upload credentials

**Real-time & Notifications:**
- `GET /ums/external/sse` - SSE real-time updates
- `GET /ums/external/notifications/records` - Notifications

### Authentication
- **Token:** JWT, expires in 3 days
- **Headers:** `Authorization` + `X-Access-Token` (dual header)
- **No refresh token endpoint** - must re-login via Google OAuth
- **Auto-refresh:** Headless Playwright re-login when token expires

### Status Monitoring (SSE)
- `GET /ums/external/sse?token={JWT}` - Push-based real-time updates
- Events: `{taskId, status, progress, workUrl}`

---

## Tools Available

### 1. Multi-Account Google Login
```bash
python v2fun_scripts/v2fun_google_login.py
```
Reads from `account.txt`, automates login + survey + token extraction.

### 2. CLI Tool
```bash
python v2fun_scripts/v2fun_cli.py generate --prompt "a red car"
python v2fun_scripts/v2fun_cli.py list-sessions
```

### 3. Web UI (Full Stack)
```bash
python v2fun_scripts/v2fun_web_v2.py
# Open: http://localhost:5000
```
Features: Register, Login, Upload, Generate, Gallery, Token Management.

### 4. API Capture Tool
```bash
python v2fun_scripts/capture_generation_flow.py
```

### 5. Token Manager
```bash
python v2fun_scripts/token_manager.py
```
Checks all token statuses, auto-refreshes expired tokens via headless re-login.

---

## Database Schema

SQLite at `v2fun_data/v2fun.db`:

- `users` - App accounts + V2Fun token
- `generations` - Generation history per user
- `uploaded_images` - Reference images
- `sessions` - Login sessions (7 day expiry)

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Automation | Python + Playwright + playwright-stealth |
| Web Backend | Flask + SQLite |
| Web Frontend | Vanilla JS + CSS (Space Grotesk / DM Sans) |
| CLI | argparse + Rich |
| HTTP Client | requests |
| SSE | sseclient-py |
| Database | SQLite3 |
| Token Management | Headless Playwright re-login |

---

## Development Guidelines

- Follow PEP 8
- Use type hints where practical
- No comments unless necessary
- Error handling on all API calls
- Archive old scripts to `archive/` folders

---

## Next Steps (Roadmap)

### Phase 6: Batch Generation
- Read prompts from file
- Rotate across multiple accounts
- Progress report

### Phase 7: API Rate Limiting
- Implement request throttling
- Account rotation on rate limit
- Queue management

---

## Security Notes

- `account.txt` is in `.gitignore`
- `v2fun_data/*.json` token files are gitignored
- Passwords stored as SHA-256 hashes
- Session tokens are random 32-byte strings

---

**Version:** 3.0.0  
**Last Updated:** 2026-08-27  
**Maintainer:** apepsiii
