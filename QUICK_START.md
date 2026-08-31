# 🚀 Quick Start Guide - V2Fun.ai Automation

**Last Updated:** 2026-08-31 16:58 WIB

---

## 📋 Prerequisites

### Required Software
```bash
✅ Python 3.10+
✅ Git
✅ Google Chrome/Chromium (untuk login automation)
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

**Main Dependencies:**
- Flask (web framework)
- Playwright (browser automation)
- Requests (HTTP client)
- SQLite3 (database)

---

## 🎬 Quick Start (3 Steps)

### 1️⃣ Setup Google Accounts

**File:** `account.txt` (di root folder)

**Format:**
```
email1@gmail.com|password1
email2@gmail.com|password2
email3@gmail.com|password3
```

**Example:**
```bash
# Copy template
cp account.txt.example account.txt

# Edit dengan text editor
notepad account.txt
```

---

### 2️⃣ Login Accounts (One-time)

Jalankan script login untuk authenticate semua akun:

```bash
python v2fun_scripts/v2fun_google_login.py
```

**Apa yang terjadi:**
- Browser Chrome akan terbuka otomatis
- Login ke Google satu per satu
- Selesaikan OAuth flow
- Token disimpan ke `v2fun_data/v2fun_session_*_latest.json`
- Account disimpan ke database

**Output:**
```
Processing account 1/3: email1@gmail.com
✓ Login successful!
✓ Token saved

Processing account 2/3: email2@gmail.com
✓ Login successful!
✓ Token saved

All accounts processed!
```

---

### 3️⃣ Start Web UI

Jalankan web server:

```bash
python v2fun_scripts/v2fun_web_v2.py
```

**Output:**
```
V2Fun.ai Web UI V2 - Enhanced
Starting server...
Open browser: http://localhost:5000
```

**Atau pakai launcher:**
```bash
# Windows
run_web.bat

# Linux/Mac
./run_web.sh
```

---

## 🌐 Akses Web Interface

### Main Web UI
```
http://localhost:5000
```

**Features:**
- Register/Login
- Connect V2Fun accounts
- Generate images dengan prompt
- Upload reference images
- Gallery hasil generate
- Real-time progress monitoring

---

## 🔧 Backend API (Optional - untuk Hermes Integration)

### Start Backend API

```bash
python v2fun_backend_api.py
```

**Output:**
```
V2Fun Backend API for Hermes Agent
Accounts available: 23
Model priority: nano-banana-pro > gpt-image-2 > nano-banana-2 > nano-banana-2-lite > qwen-edit

API Endpoints:
  POST http://localhost:5001/api/generate
  GET  http://localhost:5001/api/status/<job_id>
  GET  http://localhost:5001/api/health
  GET  http://localhost:5001/api/accounts

Starting server...
```

### Access Backend Dashboard
```
http://localhost:5001/ui
```

**Production URL:**
```
https://image-gen-v2.gxa.my.id/ui
```

---

## 📱 Usage Examples

### A. Via Web UI (Recommended)

1. **Buka browser:** http://localhost:5000
2. **Register akun** atau **Login**
3. **Connect V2Fun account** dari dropdown
4. **Isi prompt:** "a cute cat on the moon"
5. **Click Generate**
6. **Wait** sampai progress 100%
7. **Download** hasil dari gallery

---

### B. Via CLI Tool

```bash
# Generate single image
python v2fun_scripts/v2fun_cli.py generate --prompt "a red apple on table"

# List saved sessions
python v2fun_scripts/v2fun_cli.py list-sessions

# Check credits
python v2fun_scripts/v2fun_cli.py check-credits
```

---

### C. Via Backend API

**Generate Image:**
```bash
curl -X POST http://localhost:5001/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "a beautiful sunset",
    "model": "nano-banana-pro",
    "quality": "high",
    "ratio": "16:9"
  }'
```

**Check Status:**
```bash
curl http://localhost:5001/api/status/<job_id>
```

---

## 🗂️ File Structure

### Important Files

```
v2fun/
├── account.txt              # Google accounts (GITIGNORED)
├── v2fun_data/
│   ├── v2fun.db            # SQLite database
│   ├── results/            # Downloaded images
│   └── v2fun_session_*.json # Login tokens
│
├── v2fun_scripts/
│   ├── v2fun_google_login.py    # Login automation
│   ├── v2fun_web_v2.py          # Main web server
│   └── v2fun_cli.py             # CLI tool
│
└── v2fun_backend_api.py    # Backend API for Hermes
```

---

## 🔐 Admin Operations

### Create Admin Account

```bash
python create_admin.py
```

**Follow prompts:**
```
Email: admin@example.com
Password: ********
✓ Admin account created!
```

### Manage Users

```bash
# List all users
python manage_users.py list

# Reset password
python manage_users.py reset admin@example.com NewPassword123
```

---

## 🐛 Troubleshooting

### Problem: Login fails

**Solution:**
```bash
# Check browser automation
playwright install chromium

# Retry login
python v2fun_scripts/v2fun_google_login.py
```

---

### Problem: "No V2Fun token"

**Solution:**
1. Login accounts first: `python v2fun_scripts/v2fun_google_login.py`
2. Check database: `v2fun_data/v2fun.db`
3. Verify token files exist: `v2fun_data/v2fun_session_*_latest.json`

---

### Problem: Port 5000 already in use

**Solution:**
```bash
# Change port di v2fun_web_v2.py line 1270
app.run(host='0.0.0.0', port=5001, debug=True)
```

---

### Problem: Database error

**Solution:**
```bash
# Recreate database
python v2fun_scripts/database.py
```

---

## 📊 Monitoring

### Check Account Status

```bash
# Via Python
python -c "from v2fun_scripts.token_manager import get_all_tokens_status; print(get_all_tokens_status())"

# Via Web UI
# Go to: http://localhost:5000 → Dashboard → Usage Monitor
```

### Check Quota

```bash
# Via CLI
python v2fun_scripts/v2fun_cli.py check-credits

# Via Web UI
# Dashboard page shows quota for all accounts
```

---

## 🔄 Token Refresh

Tokens expire after 3 days. Auto-refresh via:

```bash
python v2fun_scripts/token_manager.py
```

**Auto-refresh happens:**
- Before each generation
- Via background scheduler
- Manual trigger via web UI

---

## 🚀 Production Deployment

### VPS Setup

1. **Clone repository:**
```bash
git clone https://github.com/apepsiii/Codebudy9router.git
cd Codebudy9router
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
playwright install chromium
```

3. **Setup accounts:**
```bash
nano account.txt
# Add your accounts
```

4. **Login accounts:**
```bash
python v2fun_scripts/v2fun_google_login.py
```

5. **Start with systemd:**
```bash
# Create service file
sudo nano /etc/systemd/system/v2fun-web.service

[Unit]
Description=V2Fun Web UI
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/Codebudy9router
ExecStart=/usr/bin/python3 v2fun_scripts/v2fun_web_v2.py
Restart=always

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl enable v2fun-web
sudo systemctl start v2fun-web
```

6. **Setup Nginx reverse proxy:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 📚 Documentation

- **User Guides:** `docs/guides/`
- **API Docs:** `docs/api/`
- **Technical:** `docs/technical/`
- **Enhancement Plan:** `BACKEND_ENHANCEMENT_PLAN.md`

---

## 🆘 Support

**Issues:** https://github.com/apepsiii/Codebudy9router/issues  
**Documentation:** Check `docs/` folder  

---

**Version:** 3.3.0  
**Status:** ✅ Production Ready  
**Last Updated:** 2026-08-31
