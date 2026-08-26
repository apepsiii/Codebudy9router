# AGENTS-DEPLOY.md - V2Fun.ai Deployment Guide

**Panduan lengkap deploy V2Fun Web UI ke VPS dengan domain dan SSL**

---

## Prasyarat

### VPS Requirements
- **OS:** Ubuntu 22.04 LTS atau Debian 12
- **RAM:** Minimal 2GB (4GB recommended untuk Playwright)
- **Storage:** 20GB+
- **Python:** 3.10+
- **Access:** Root atau sudo user

### Domain
- Domain yang sudah di-point ke IP VPS (A record)
- Contoh: `v2fun.yourdomain.com`

---

## Step 1: Setup VPS

### 1.1 Connect ke VPS

```bash
ssh root@your-vps-ip
```

### 1.2 Update System

```bash
apt update && apt upgrade -y
```

### 1.3 Install Dependencies

```bash
# Install Python
apt install -y python3 python3-pip python3-venv

# Install Playwright system dependencies
apt install -y libnss3 libatk1.0-0 libatk-bridge2.0-0 \
libcups2 libxkbcommon0 libxcomposite1 libxdamage1 \
libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2 \
libxshmfence1 libglib2.0-0 libgtk-3-0

# Install nginx
apt install -y nginx

# Install certbot for SSL
apt install -y certbot python3-certbot-nginx

# Install git
apt install -y git
```

---

## Step 2: Clone & Setup Project

### 2.1 Clone Repository

```bash
cd /opt
git clone https://github.com/apepsiii/Codebudy9router.git v2fun
cd v2fun
```

### 2.2 Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2.3 Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2.4 Install Playwright Browser

```bash
playwright install chromium
playwright install-deps
```

### 2.5 Initialize Database

```bash
python -c "from v2fun_scripts.database import init_db; init_db()"
```

### 2.6 Create Admin User

```bash
python v2fun_scripts/admin_create_user.py --email admin@yourdomain.com --password yourpassword
```

### 2.7 Setup Account File

```bash
# Create account.txt with your Google accounts
nano account.txt
# Format: email:password (one per line)
```

### 2.8 Login & Get Tokens

```bash
# Run login automation (headless mode for VPS)
# Edit v2fun_google_login.py: change headless=False to headless=True
python v2fun_scripts/v2fun_google_login.py
```

---

## Step 3: Configure Gunicorn

### 3.1 Install Gunicorn

```bash
pip install gunicorn
```

### 3.2 Test Gunicorn

```bash
cd /opt/v2fun
source venv/bin/activate
gunicorn --bind 0.0.0.0:5000 "v2fun_scripts.v2fun_web_v2:app"
```

Tekan Ctrl+C untuk stop.

### 3.3 Create Systemd Service

```bash
nano /etc/systemd/system/v2fun.service
```

Isi dengan:

```ini
[Unit]
Description=V2Fun Web UI
After=network.target

[Service]
User=root
WorkingDirectory=/opt/v2fun
Environment="PATH=/opt/v2fun/venv/bin"
ExecStart=/opt/v2fun/venv/bin/gunicorn \
    --workers 3 \
    --bind 127.0.0.1:5000 \
    --timeout 300 \
    "v2fun_scripts.v2fun_web_v2:app"
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 3.4 Start Service

```bash
systemctl daemon-reload
systemctl enable v2fun
systemctl start v2fun
systemctl status v2fun
```

---

## Step 4: Configure Nginx Reverse Proxy

### 4.1 Create Nginx Config

```bash
nano /etc/nginx/sites-available/v2fun
```

Isi dengan (ganti `v2fun.yourdomain.com`):

```nginx
server {
    listen 80;
    server_name v2fun.yourdomain.com;

    # Upload size (for reference images)
    client_max_body_size 20M;

    # Main app
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # SSE support (important for real-time monitoring)
    location /api/generation-stream/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
        proxy_connect_timeout 10s;
        chunked_transfer_encoding on;
    }

    # Static uploads
    location /uploads/ {
        alias /opt/v2fun/v2fun_data/uploads/;
        expires 30d;
    }

    # Results
    location /results/ {
        alias /opt/v2fun/v2fun_data/results/;
        expires 30d;
    }
}
```

### 4.2 Enable Site

```bash
ln -s /etc/nginx/sites-available/v2fun /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

---

## Step 5: Setup SSL with Certbot

### 5.1 Obtain SSL Certificate

```bash
certbot --nginx -d v2fun.yourdomain.com
```

Pilih:
- Enter email
- Agree to terms
- Redirect HTTP to HTTPS (Yes/2)

### 5.2 Verify SSL

```bash
# Test auto-renewal
certbot renew --dry-run
```

---

## Step 6: Firewall Setup

```bash
# Allow SSH, HTTP, HTTPS
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

---

## Step 7: Verify Deployment

### 7.1 Check Services

```bash
systemctl status v2fun
systemctl status nginx
```

### 7.2 Test Access

```bash
# From VPS
curl -I http://localhost:5000

# From browser
https://v2fun.yourdomain.com
```

### 7.3 Login

- Buka `https://v2fun.yourdomain.com`
- Login dengan admin account yang sudah dibuat
- Test generate image

---

## Maintenance Commands

### View Logs

```bash
# App logs
journalctl -u v2fun -f

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### Restart Services

```bash
systemctl restart v2fun
systemctl restart nginx
```

### Update Project

```bash
cd /opt/v2fun
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
systemctl restart v2fun
```

### Add New User

```bash
cd /opt/v2fun
source venv/bin/activate
python v2fun_scripts/admin_create_user.py --email newuser@email.com --password theirpassword
```

### Refresh V2Fun Tokens

```bash
cd /opt/v2fun
source venv/bin/activate

# Edit login script for headless mode
sed -i 's/headless=False/headless=True/' v2fun_scripts/v2fun_google_login.py

# Run login automation
python v2fun_scripts/v2fun_google_login.py
```

---

## Troubleshooting

### Issue: Gunicorn tidak start
```bash
# Check error
journalctl -u v2fun -n 50

# Test manual
cd /opt/v2fun
source venv/bin/activate
gunicorn --bind 127.0.0.1:5000 "v2fun_scripts.v2fun_web_v2:app"
```

### Issue: Playwright error di VPS
```bash
# Install all deps
playwright install-deps
playwright install chromium

# Test
python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); b = p.chromium.launch(headless=True); print('OK'); b.close(); p.stop()"
```

### Issue: SSE tidak work di production
```bash
# Pastikan proxy_buffering off di nginx
# Check nginx config
grep -r "proxy_buffering" /etc/nginx/
```

### Issue: Upload file gagal (413 Request Entity Too Large)
```bash
# Edit nginx config
nano /etc/nginx/sites-available/v2fun
# Pastikan: client_max_body_size 20M;

# Reload
systemctl reload nginx
```

### Issue: Database locked
```bash
# Stop service
systemctl stop v2fun

# Check database
sqlite3 /opt/v2fun/v2fun_data/v2fun.db ".tables"

# Start service
systemctl start v2fun
```

---

## Security Hardening (Optional)

### 1. Disable Root SSH Login
```bash
# Create sudo user first
adduser deploy
usermod -aG sudo deploy

# Then disable root
nano /etc/ssh/sshd_config
# Set: PermitRootLogin no
systemctl restart sshd
```

### 2. Change SSH Port
```bash
nano /etc/ssh/sshd_config
# Set: Port 2222 (or any custom port)
systemctl restart sshd

# Remember to update firewall
ufw allow 2222/tcp
ufw delete allow 22/tcp
```

### 3. Setup Fail2Ban
```bash
apt install -y fail2ban
systemctl enable fail2ban
systemctl start fail2ban
```

### 4. Auto Security Updates
```bash
apt install -y unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades
```

---

## Backup Strategy

### Database Backup
```bash
# Manual
cp /opt/v2fun/v2fun_data/v2fun.db /backup/v2fun-$(date +%Y%m%d).db

# Cron job (daily at 3am)
crontab -e
# Add: 0 3 * * * cp /opt/v2fun/v2fun_data/v2fun.db /backup/v2fun-$(date +\%Y\%m\%d).db
```

### Token Backup
```bash
# Backup session files
tar -czf /backup/v2fun-tokens-$(date +%Y%m%d).tar.gz /opt/v2fun/v2fun_data/v2fun_session_*.json
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Start app | `systemctl start v2fun` |
| Stop app | `systemctl stop v2fun` |
| Restart app | `systemctl restart v2fun` |
| App status | `systemctl status v2fun` |
| App logs | `journalctl -u v2fun -f` |
| Nginx restart | `systemctl restart nginx` |
| Nginx test | `nginx -t` |
| Add user | `python v2fun_scripts/admin_create_user.py` |
| Update code | `git pull && pip install -r requirements.txt && systemctl restart v2fun` |
| Refresh tokens | `python v2fun_scripts/v2fun_google_login.py` |
| SSL renew | `certbot renew` |

---

## Architecture Diagram

```
Internet → Nginx (443/SSL) → Gunicorn (127.0.0.1:5000) → Flask App
                                    ↓
                              SQLite Database
                                    ↓
                         V2Fun API (api.prod.v2fun.ai)
```

---

**Version:** 1.0  
**Last Updated:** 2026-08-27
