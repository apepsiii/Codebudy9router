# V2Fun.ai - Command Cheat Sheet

## 🚀 Quick Commands Reference

### Admin Management

```bash
# List all users in database
python manage_users.py list

# Create new admin account
python create_admin.py admin@example.com YourPassword123

# Create regular user
python manage_users.py create user@example.com Password456

# Reset password for existing user
python manage_users.py reset admin@v2fun.local NewPassword789

# Check users directly in database
python -c "from v2fun_scripts.database import get_db; conn = get_db(); cursor = conn.cursor(); cursor.execute('SELECT id, email, created_at FROM users'); [print(f'ID: {r[0]} | Email: {r[1]} | Created: {r[2]}') for r in cursor.fetchall()]; conn.close()"
```

### Google OAuth Login

```bash
# Login multiple Google accounts (with GSuite welcome fix)
python v2fun_scripts/v2fun_google_login.py

# Login in headless mode (edit script: headless=True)
# Check token status
python v2fun_scripts/token_manager.py

# Verify token validity
python -c "from v2fun_scripts.token_manager import get_all_tokens_status; statuses = get_all_tokens_status(); [print(f'{s[\"email\"]}: {s[\"status\"]} ({s[\"remaining\"]})') for s in statuses]"
```

### CLI Tools

```bash
# Generate image via CLI
python v2fun_scripts/v2fun_cli.py generate --prompt "a red car"

# Generate with options
python v2fun_scripts/v2fun_cli.py generate --prompt "cat" --quality high --ratio 1:1

# Show user info
python v2fun_scripts/v2fun_cli.py generate --prompt "dog" --show-info

# List available sessions
python v2fun_scripts/v2fun_cli.py list-sessions

# Batch generation (bash script example)
for prompt in "car" "house" "tree"; do
  python v2fun_scripts/v2fun_cli.py generate --prompt "$prompt"
  sleep 5
done
```

### Web Server

```bash
# Start web UI server
python v2fun_scripts/v2fun_web_v2.py

# Start on different port
# Edit v2fun_web_v2.py line 1841: app.run(host='0.0.0.0', port=8080)

# Access web UI
# Local: http://localhost:5000
# Network: http://YOUR_IP:5000
```

### CLI Tools

```bash
# Generate image via CLI
python v2fun_scripts/v2fun_cli.py generate --prompt "a beautiful sunset"

# Generate with options
python v2fun_scripts/v2fun_cli.py generate --prompt "a red car" --model nano-banana-pro --ratio 16:9 --quality high

# List available sessions
python v2fun_scripts/v2fun_cli.py list-sessions

# Check quota
python v2fun_scripts/v2fun_cli.py check-quota
```

### Database Operations

```bash
# Initialize database
python v2fun_scripts/database.py

# Backup database
cp v2fun_data/v2fun.db v2fun_data/v2fun.db.backup_$(date +%Y%m%d_%H%M%S)

# Check V2Fun accounts status
python -c "from v2fun_scripts.database import get_all_v2fun_accounts; accounts = get_all_v2fun_accounts(); print(f'Total: {len(accounts)}'); [print(f'{a[\"email\"]}: {a[\"status\"]}') for a in accounts]"

# Sync session files to database
python -c "from v2fun_scripts.database import sync_v2fun_sessions_to_db; synced = sync_v2fun_sessions_to_db(); print(f'Synced {synced} accounts')"
```

### Debugging

```bash
# Check for debug screenshots
ls -la v2fun_data/debug_*.png

# View latest session file
cat v2fun_data/v2fun_session_*_latest.json | python -m json.tool

# Check network captures
ls -la v2fun_data/v2fun_capture_*.json

# View logs (if any)
tail -f v2fun_data/logs/*.log
```

### Account.txt Format

```bash
# Format 1: Pipe separator
email1@gmail.com|password1
email2@gmail.com|password2

# Format 2: Colon separator
email1@gmail.com:password1
email2@gmail.com:password2

# Comments (start with #)
# This is a comment
email@gmail.com|password

# Create from template
echo "email@gmail.com|password" > account.txt
```

### Token Management

```bash
# Check token expiry
python -c "from v2fun_scripts.token_manager import get_token_status, get_time_remaining; import json; data = json.load(open('v2fun_data/v2fun_session_email_at_gmail_com_latest.json')); token = data['tokens']['cookie_token']; print(f'Status: {get_token_status(token)}'); print(f'Remaining: {get_time_remaining(token)}')"

# Refresh expired token
python -c "from v2fun_scripts.token_manager import check_and_refresh_if_needed; status, new_token = check_and_refresh_if_needed('OLD_TOKEN', 'email@gmail.com', 'password'); print(f'New Status: {status}')"

# List all tokens
python -c "from pathlib import Path; import json; files = Path('v2fun_data').glob('v2fun_session_*_latest.json'); [print(f'{f.stem}: {json.load(open(f)).get(\"email\")}') for f in files]"
```

### API Testing

```bash
# Capture generation flow
python v2fun_scripts/capture_generation_flow.py

# Test V2Fun API directly
python -c "from v2fun_scripts.v2fun_web_v2 import V2FunClient; import json; token = json.load(open('v2fun_data/v2fun_session_email_latest.json'))['tokens']['cookie_token']; client = V2FunClient(token); print(client.get_balance())"

# Check quota
python -c "from v2fun_scripts.v2fun_web_v2 import V2FunClient; import json; token = json.load(open('v2fun_data/v2fun_session_email_latest.json'))['tokens']['cookie_token']; client = V2FunClient(token); print(client.get_free_count())"
```

### Export/Import

```bash
# Export all data (via web UI)
# Go to: http://localhost:5000 -> Settings -> Export Data

# Or via Python
python -c "from v2fun_scripts.database import get_db; import json; conn = get_db(); cursor = conn.cursor(); cursor.execute('SELECT * FROM users'); users = [dict(row) for row in cursor.fetchall()]; print(json.dumps(users, indent=2, default=str)); conn.close()"

# Backup everything
tar -czf v2fun_backup_$(date +%Y%m%d_%H%M%S).tar.gz v2fun_data/ account.txt v2fun_scripts/*.py

# Restore backup
tar -xzf v2fun_backup_YYYYMMDD_HHMMSS.tar.gz
```

### Git Operations

```bash
# Check status
git status

# Commit changes
git add .
git commit -m "Fixed GSuite welcome screen handler"

# Push to remote
git push origin main

# Pull updates
git pull origin main

# View recent commits
git log --oneline -10
```

### System Check

```bash
# Check Python version
python --version

# Check installed packages
pip list | grep -E "(playwright|flask|requests|rich)"

# Install missing dependencies
pip install -r requirements.txt

# Update Playwright browsers
playwright install chromium

# Check disk space
du -sh v2fun_data/

# Count session files
ls -1 v2fun_data/v2fun_session_*_latest.json | wc -l
```

### Troubleshooting

```bash
# Remove failed session files
rm v2fun_data/v2fun_session_*_failed*.json

# Clear debug screenshots
rm v2fun_data/debug_*.png

# Reset database (CAUTION!)
rm v2fun_data/v2fun.db
python v2fun_scripts/database.py

# Check port availability
netstat -ano | findstr :5000

# Kill process on port 5000 (Windows)
# netstat -ano | findstr :5000
# taskkill /PID <PID> /F

# Kill process on port 5000 (Linux/Mac)
# lsof -ti:5000 | xargs kill -9
```

### Performance Monitoring

```bash
# Count successful logins
ls v2fun_data/v2fun_session_*_latest.json | wc -l

# Count generations
python -c "from v2fun_scripts.database import get_db; conn = get_db(); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM generations'); print(f'Total generations: {cursor.fetchone()[0]}'); conn.close()"

# Check database size
ls -lh v2fun_data/v2fun.db

# View quota dashboard
# http://localhost:5000 -> Dashboard -> View Usage
```

---

## 🔗 Quick Links

- **Web UI:** http://localhost:5000
- **Login:** http://localhost:5000/login
- **Dashboard:** http://localhost:5000 (after login)
- **API Docs:** `v2fun_data/API_GENERATION_ANALYSIS.md`
- **Repository:** https://github.com/apepsiii/Codebudy9router

---

## 📝 Common Workflows

### Initial Setup
```bash
1. pip install -r requirements.txt
2. playwright install chromium
3. python create_admin.py admin@v2fun.local Password123
4. Add Google accounts to account.txt
5. python v2fun_scripts/v2fun_google_login.py
6. python v2fun_scripts/v2fun_web_v2.py
```

### Daily Usage
```bash
1. python v2fun_scripts/v2fun_web_v2.py
2. Open http://localhost:5000
3. Login with admin credentials
4. Select V2Fun account from dropdown
5. Generate images!
```

### Add New Accounts
```bash
1. Edit account.txt (add new lines)
2. python v2fun_scripts/v2fun_google_login.py
3. Refresh web UI dashboard
```

### Troubleshoot Failed Login
```bash
1. Check: ls v2fun_data/debug_*.png
2. Retry: python v2fun_scripts/v2fun_google_login.py
3. Manual: Open browser, check popup behavior
```

---

**Last Updated:** 2026-08-27 12:18 WIB  
**Quick Reference:** Keep this file handy!
