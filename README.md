# V2Fun.ai API Automation

> Web automation dan API exploration tool untuk V2Fun.ai - AI Image Generator

**Repository:** https://github.com/apepsiii/Codebudy9router  
**Version:** 3.0.0  
**Last Updated:** 2026-08-27

---

## Current Status

**Phase:** Production Ready

| Feature | Status |
|---------|--------|
| Google OAuth Login (multi-account) | Done |
| API Discovery (31 endpoints) | Done |
| Image Generation API | Done |
| CLI Tool | Done |
| Web UI (Full Stack) | Done |
| SQLite Database | Done |
| Image Upload to V2Fun OSS | Done |
| SSE Real-time Monitoring | Done |
| Auto-download Results | Done |
| Token Auto-Refresh (headless) | Done |
| Bulk Account Registration | Done |

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
│   ├── run_v2fun_login.bat            # Login launcher
│   ├── run_capture_generation.bat     # Capture launcher
│   └── archive/                       # Old/deprecated scripts
│
├── v2fun_web_v2/
│   └── templates/
│       ├── login.html
│       ├── register.html
│       └── dashboard.html
│
├── v2fun_data/
│   ├── v2fun.db                       # SQLite database
│   ├── v2fun_session_*_latest.json    # Saved login tokens
│   ├── v2fun_capture_generation_*.json # Network captures
│   ├── v2fun_generation_api_*.json    # Generation API captures
│   ├── API_GENERATION_ANALYSIS.md     # API documentation
│   ├── uploads/                       # Uploaded reference images
│   ├── generations/                   # Generation results
│   ├── results/                       # Downloaded images
│   └── archive/                       # Old docs, captures, tokens
│
├── account.txt                        # Google accounts (gitignored)
├── account.txt.example
├── run_web.bat                        # Web UI launcher
└── requirements.txt
```

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Add Google Accounts

```bash
cp account.txt.example account.txt
# Edit with your accounts (email:password format)
```

### 3. Login & Extract Tokens

```bash
python v2fun_scripts/v2fun_google_login.py
```

### 4. Start Web UI

```bash
python v2fun_scripts/v2fun_web_v2.py
# Open: http://localhost:5000
```

**Web UI Flow:**
1. Register akun baru
2. Login
3. Connect V2Fun session (halaman Connect)
4. Generate images (halaman Generate)
5. View gallery & download results (halaman Gallery)
6. Manage accounts & refresh tokens (halaman Manage Accounts)

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
- Session tokens are random 32-byte strings
- Tokens auto-refresh before expiry

---

## Disclaimer

This tool is for educational and personal use only. Always respect website Terms of Service and rate limits.

---

**Author:** apepsiii  
**Version:** 3.0.0
