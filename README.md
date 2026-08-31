# V2Fun.ai API Automation

> Web automation dan API exploration tool untuk V2Fun.ai - AI Image Generator

**Repository:** https://github.com/apepsiii/Codebudy9router  
**Version:** 3.3.0  
**Last Updated:** 2026-08-31 14:36 WIB

**Latest Updates:**
- ✅ **NEW: Integrations Menu** - UGC Generator API configuration in dashboard
- ✅ **NEW: Auto-download Images** - Generated images saved to local storage
- ✅ Backend API for Hermes Agent integration (round-robin, model priority)
- ✅ REST API with Telegram notifications
- ✅ Fixed static Flask secret key for Gunicorn multi-worker
- ✅ Persist selected V2Fun email in session
- ✅ Admin account management tools (create_admin.py, manage_users.py)

---

## Current Status

**Phase:** Production Ready

| Feature | Status |
|---------|--------|
| Google OAuth Login (multi-account) | ✅ Done |
| GSuite Welcome Screen Handler | ✅ Done |
| API Discovery (31 endpoints) | ✅ Done |
| Image Generation API | ✅ Done |
| **Integrations Menu (UGC Generator)** | ✅ **New** |
| **Auto-download to Local Storage** | ✅ **New** |
| Backend API for Hermes Agent | ✅ Done |
| Round-Robin Account Selection | ✅ Done |
| Model Priority System | ✅ Done |
| CLI Tool | ✅ Done |
| Web UI (Full Stack) | ✅ Done |
| Admin Account Management | ✅ Done |
| SQLite Database | ✅ Done |
| Image Upload to V2Fun OSS | ✅ Done |
| SSE Real-time Monitoring | ✅ Done |
| Token Auto-Refresh (headless) | ✅ Done |
| Bulk Account Registration | ✅ Done |
| Telegram Notifications | ✅ Done |

---

## Project Structure

```
Codebudy9router/
├── v2fun_scripts/
│   ├── v2fun_google_login.py          # Multi-account Google OAuth login
│   ├── v2fun_cli.py                   # CLI tool for generation
│   ├── v2fun_web_v2.py                # Flask web server (main)
│   ├── database.py                    # SQLite database models
│   ├── image_downloader.py            # Auto-download images to local
│   ├── sse_monitor.py                 # SSE real-time monitor
│   ├── token_manager.py               # JWT token auto-refresh
│   └── archive/                       # Old/deprecated scripts
│
├── v2fun_web_v2/
│   └── templates/
│       ├── login.html                 # Login page
│       ├── register.html              # Register page
│       └── dashboard.html             # Main dashboard (with Integrations)
│
├── v2fun_data/
│   ├── v2fun.db                       # SQLite database
│   ├── v2fun_session_*_latest.json    # Saved login tokens
│   ├── uploads/                       # User uploaded reference images
│   ├── results/                       # Auto-downloaded generated images
│   ├── generations/                   # Generation metadata
│   └── archive/                       # Old captures, tokens
│
├── hermes-integration/                # UGC Generator API client
│   ├── UGC_API_INTEGRATION_GUIDE.md   # Integration documentation
│   ├── ugc_generator_client.py        # Python client library
│   ├── content_with_visuals.py        # Content + visuals generation
│   └── ugc_api_config.yaml            # Config template
│
├── docs/                              # 📁 Documentation (organized)
│   ├── guides/                        # User guides & tutorials
│   │   ├── ADMIN_GUIDE.md
│   │   ├── CHEATSHEET.md
│   │   └── V2FUN_CLI_GUIDE.md
│   ├── api/                           # API documentation
│   │   ├── BACKEND_API_QUICKREF.md
│   │   └── V2FUN_BACKEND_API_GUIDE.md
│   ├── technical/                     # Technical docs
│   │   ├── TOKEN_REFRESH_ANALYSIS.md
│   │   ├── TOKEN_REFRESH_QUICKREF.md
│   │   ├── GSUITE_FLOW_DIAGRAM.md
│   │   └── GSUITE_WELCOME_FIX.md
│   └── archive/                       # Old summaries
│       ├── SUMMARY.md
│       ├── SESSION_SUMMARY_20260826.md
│       └── CLEANUP_SUMMARY.md
│
├── create_admin.py                    # Create admin account CLI
├── manage_users.py                    # User management CLI
├── v2fun_backend_api.py               # Backend API for Hermes
├── test_backend_api.py                # API test script
│
├── AGENTS.md                          # Project overview for AI agents
├── AGENTS-DEPLOY.md                   # Deployment guide
├── CHANGELOG.md                       # Version history
├── README.md                          # This file
│
├── account.txt                        # Google accounts (gitignored)
├── account.txt.example                # Account format example
├── run_web.bat                        # Web UI launcher
├── run_backend_api.bat                # Backend API launcher
└── requirements.txt                   # Python dependencies
```

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Create Admin Account

```bash
# Create admin account for web UI
python create_admin.py admin@example.com YourPassword123

# Or use management tool
python manage_users.py create admin@example.com Password123
```

### 3. Login & Extract Tokens

```bash
# Login multiple Google accounts (with GSuite welcome screen fix)
python v2fun_scripts/v2fun_google_login.py
```

### 4. Start Services

**Option A: Backend API (for Hermes Agent)**
```bash
# Windows
run_backend_api.bat

# Linux/Mac
chmod +x run_backend_api.sh
./run_backend_api.sh

# Or manually
python v2fun_backend_api.py
# API: http://localhost:5001
```

**Option B: Web UI (for manual use)**
```bash
python v2fun_scripts/v2fun_web_v2.py
# Web: http://localhost:5000
```

**Option C: CLI (for terminal use)**
```bash
python v2fun_scripts/v2fun_cli.py generate --prompt "a red car"
```

---

## API Reference

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
```

**Request Body:**
```json
{
  "prompt": "your text prompt",
  "model": "nano-banana-pro",
  "ratio": "16:9",
  "num": 1,
  "quality": "medium",
  "referenceImages": ["upload/image/..."]
}
```

**Parameters:**

| Field | Options |
|-------|---------|
| `model` | nano-banana-pro, nano-banana-2, nano-banana-2-lite, gpt-image-2, qwen-image |
| `ratio` | 1:1, 16:9, 9:16, 4:3, 3:4 |
| `quality` | low, medium, high |
| `num` | 1, 2, 4 |

### Authentication

- Dual JWT header: `Authorization` + `X-Access-Token`
- Token expires in 3 days
- No refresh token endpoint - auto-refresh via headless Playwright

### Image Upload Flow

1. `POST /sys/oss/nologin/getAliSTS` - Get Alibaba Cloud OSS credentials
2. Upload to OSS using STS credentials
3. Use OSS path as `referenceImages` in generation request

### Status Monitoring (SSE)

- `GET /ums/external/sse?token={JWT}` - Real-time push events
- Events include progress, status, and result URL

---

## Database Schema

```sql
users (id, email, password_hash, google_email, v2fun_token, credits)
generations (id, user_id, prompt, model, quality, ratio, status, result_url)
uploaded_images (id, user_id, filename, file_path)
sessions (id, user_id, session_token, expires_at)
```

---

## Admin Account Management

### Create Admin Account

```bash
# Method 1: Using create_admin.py
python create_admin.py admin@example.com Password123

# Method 2: Using manage_users.py
python manage_users.py create admin@example.com Password123
```

### Manage Users

```bash
# List all users
python manage_users.py list

# Reset password
python manage_users.py reset admin@example.com NewPassword456
```

**Note:** Web registration is disabled for security. Only admins can create accounts via CLI.

**Documentation:** See `ADMIN_GUIDE.md` for complete guide.

---

## GSuite Welcome Screen Fix

The automation now handles GSuite "Welcome to your new account" popup automatically.

**Features:**
- Auto-detects welcome screen
- 13 button selector variants
- JavaScript click fallback
- Keyboard Enter fallback
- Auto-screenshot for debugging
- OAuth completion monitoring

**If login fails:**
1. Check screenshots in `v2fun_data/debug_*.png`
2. View console output for error details
3. Retry with: `python v2fun_scripts/v2fun_google_login.py`

**Documentation:** See `GSUITE_WELCOME_FIX.md` for technical details.

---

## Documentation

### 📚 Organized Documentation Structure

All documentation is now organized in the `docs/` folder:

#### 📖 User Guides (`docs/guides/`)
- **ADMIN_GUIDE.md** - Admin account management & user creation
- **CHEATSHEET.md** - Quick commands reference
- **V2FUN_CLI_GUIDE.md** - CLI tool complete guide

#### 🔌 API Documentation (`docs/api/`)
- **BACKEND_API_QUICKREF.md** - Backend API quick reference
- **V2FUN_BACKEND_API_GUIDE.md** - Backend API for Hermes integration

#### 🔧 Technical Documentation (`docs/technical/`)
- **TOKEN_REFRESH_ANALYSIS.md** - Token refresh mechanism analysis
- **TOKEN_REFRESH_QUICKREF.md** - Token refresh quick reference
- **GSUITE_FLOW_DIAGRAM.md** - Visual flow diagrams
- **GSUITE_WELCOME_FIX.md** - GSuite welcome screen fix details

#### 📦 Archive (`docs/archive/`)
- **SUMMARY.md** - Complete project summary
- **SESSION_SUMMARY_20260826.md** - Session history
- **CLEANUP_SUMMARY.md** - Cleanup documentation

#### 🔗 Integration Guides
- **hermes-integration/UGC_API_INTEGRATION_GUIDE.md** - UGC Generator API integration
- **CHANGELOG.md** - Version history
- **AGENTS.md** - Project overview for AI agents

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Automation | Python + Playwright + playwright-stealth |
| Web Backend | Flask + SQLite |
| Web Frontend | Vanilla JS + CSS (Flat Design) |
| CLI | argparse + Rich |
| SSE | sseclient-py |
| Database | SQLite3 |

---

## Roadmap

### Phase 6: Batch Generation
- Read prompts from file
- Rotate across multiple accounts
- Progress report

### Phase 7: API Rate Limiting
- Request throttling
- Account rotation on rate limit

---

## Security

- `account.txt` and token files are gitignored
- Passwords stored as SHA-256 hashes
- Session tokens are random 32-byte strings (7 day expiry)
- Tokens auto-refresh before expiry
- Registration disabled (admin-only account creation)

---

## Disclaimer

This tool is for educational and personal use only. Always respect website Terms of Service and rate limits.

---

**Author:** apepsiii  
**Version:** 3.1.0  
**Last Updated:** 2026-08-27 12:19 WIB  
**Version:** 3.0.0
