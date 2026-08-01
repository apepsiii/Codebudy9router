# Kiro Token Generator - Web Dashboard

Bot otomatis untuk mendapatkan refresh token dari Kiro.dev dengan **Web Interface** yang mudah digunakan.

---

## 🎨 NEW: Web Dashboard Interface

**Sekarang dengan Web Dashboard yang user-friendly!**

No more CLI commands yang rumit. Kelola semua dari browser Anda!

### ✨ Features Web Dashboard:

- 🎯 **Add Accounts** - Single atau bulk import
- 📊 **Real-time Statistics** - Monitor progress & status
- 👁️ **View & Manage** - Lihat semua akun dan tokennya
- 📋 **Process Control** - Start/stop processing dengan mudah
- 📥 **Export Tokens** - Export ke `kiro_tokens.txt` dengan 1 klik
- 🔄 **Auto Refresh** - Real-time update setiap 5 detik
- 💾 **SQLite Database** - Persistent storage
- 🚀 **Easy Command** - Jalankan dengan `kiro start`

---

## 📋 Requirements

```bash
# Install dependencies
pip install -r requirements-web.txt

# Install Playwright
playwright install chromium
```

---

## 🚀 Quick Start - Web Dashboard

### 1. Start Server

```bash
kiro start
```

atau

```bash
python kiro.py start
```

Server akan jalan di: **http://localhost:8000**

### 2. Buka Browser

Akses dashboard di browser Anda:
```
http://localhost:8000
```

### 3. Add Accounts

**Option 1: Single Account**
- Masukkan email dan password
- Pilih type (Login atau Register)
- Klik "Add Account"

**Option 2: Bulk Import**
- Paste multiple accounts dengan format: `email:password`
- Pilih type (Login atau Register)
- Klik "Import Accounts"

### 4. Start Processing

- Atur settings (workers, delay, visible mode)
- Klik "Start Processing"
- Monitor progress di tabel accounts
- Token akan muncul otomatis saat selesai

### 5. Export Tokens

- Klik "Export Tokens"
- Tokens akan di-save ke `kiro_tokens.txt`
- Copy token langsung dari dashboard atau file

---

## 🎯 CLI Commands

```bash
# Start web server (default port 8000)
kiro start

# Start on custom port
kiro start --port 3000

# Start with auto-reload (development mode)
kiro start --reload

# Initialize database
kiro init

# Show version
kiro version

# Show help
kiro help
```

---

## 📊 Web Dashboard Screenshots

### Main Dashboard
- **Statistics Cards**: Total, Success, Failed, Injected
- **Add Accounts**: Single or bulk import
- **Process Settings**: Workers, delay, visible mode, manual mode
- **Accounts Table**: Real-time status, tokens, actions

### Features:
- ✅ View token dengan modal popup
- ✅ Copy token ke clipboard dengan 1 klik
- ✅ Delete individual atau bulk delete
- ✅ Filter by status (pending, success, failed)
- ✅ Real-time auto-refresh
- ✅ Responsive design (mobile-friendly)

---

## 🗄️ Database

**SQLite Database**: `kiro.db`

**Tables:**
- `accounts` - Semua akun dan statusnya
- `config` - Configuration settings
- `process_logs` - Process logs (untuk future debugging)

**Data Persistent:**
- Semua data tersimpan di database
- Resume otomatis saat restart server
- History tetap ada

---

## 🔧 API Endpoints

Backend menyediakan REST API:

```
GET  /api/stats                # Dashboard statistics
GET  /api/accounts             # List accounts (with filters)
POST /api/accounts             # Add single account
POST /api/accounts/bulk        # Bulk import accounts
DELETE /api/accounts/{id}      # Delete account
DELETE /api/accounts           # Delete all accounts
POST /api/process/start        # Start processing
POST /api/export/tokens        # Export tokens to file
GET  /api/logs/{account_id}    # Get account logs
```

---

## 📁 File Structure

```
KiroApiKey/
├── kiro.py                     # CLI entry point
├── kiro.bat                    # Windows launcher
├── kiro.db                     # SQLite database (auto-created)
├── kiro_tokens.txt             # Exported tokens
├── web/
│   ├── __init__.py
│   ├── app.py                  # FastAPI backend
│   ├── database.py             # Database models
│   └── static/
│       └── index.html          # Web dashboard UI
├── main.py                     # Original CLI script (still works)
├── requirements.txt            # Original requirements
└── requirements-web.txt        # Web dashboard requirements
```

---

## 🆚 Web Dashboard vs CLI

### Web Dashboard (Recommended)
✅ User-friendly interface  
✅ Visual monitoring  
✅ Easy account management  
✅ Real-time statistics  
✅ Click & copy tokens  
✅ Persistent database  
✅ Multi-session support  

### CLI (Still Available)
✅ Automation scripts  
✅ CI/CD integration  
✅ Lightweight  
✅ No browser needed  

**Recommendation:** Use Web Dashboard untuk daily usage, CLI untuk automation.

---

## 🔄 Workflow

### Web Dashboard Workflow:

1. **Start Server**: `kiro start`
2. **Open Browser**: `http://localhost:8000`
3. **Add Accounts**: Single atau bulk import
4. **Configure**: Set workers, delay, visible mode
5. **Process**: Click "Start Processing"
6. **Monitor**: Real-time status updates
7. **Export**: Click "Export Tokens"
8. **Inject**: Manual inject ke 9router via dashboard

### Manual Inject ke 9Router:

1. Export tokens dari web dashboard
2. Buka: `http://localhost:20128/dashboard`
3. Pilih provider (anthropic/openai)
4. Copy token dari web dashboard atau file
5. Paste dan save

---

## 💡 Tips

### Web Dashboard:
- Start dengan 1-2 akun untuk testing
- Gunakan "visible mode" untuk debug
- Enable "manual mode" untuk akun penting
- Monitor statistics real-time
- Filter by status untuk lihat failed accounts

### Performance:
- Workers: 2-4 (optimal)
- Delay: 3-5 seconds (safe)
- Batch size: 5-10 accounts per run
- Use manual mode untuk better success rate

---

## 🐛 Troubleshooting

### Server Won't Start
```bash
# Check if port is in use
netstat -ano | findstr :8000

# Use different port
kiro start --port 3000
```

### Database Issues
```bash
# Re-initialize database
kiro init
```

### Process Not Starting
- Check accounts have "pending" status
- Check workers & delay settings
- Check browser automation requirements

### Browser Issues
- Install Playwright: `playwright install chromium`
- Use visible mode for debugging
- Check Chrome/Chromium installation

---

## 🔐 Security

**Database:**
- SQLite file stored locally
- Passwords stored (consider encryption for production)
- No external connections

**Web Server:**
- Default: localhost only
- Production: use `--host 0.0.0.0` with caution
- Add authentication for production use

**Recommendations:**
- Don't expose to public internet
- Use strong passwords
- Keep tokens secure
- Regular backups

---

## 📚 Documentation

- **README.md** - This file (main documentation)
- **QUICK_REFERENCE.txt** - Command quick reference
- **FINAL_SUMMARY.txt** - Setup summary

---

## 🚀 Next Steps

1. Install dependencies:
   ```bash
   pip install -r requirements-web.txt
   playwright install chromium
   ```

2. Start server:
   ```bash
   kiro start
   ```

3. Open browser:
   ```
   http://localhost:8000
   ```

4. Add accounts dan start processing!

---

## ❓ FAQ

**Q: Web dashboard vs CLI, mana yang lebih baik?**  
A: Web dashboard lebih user-friendly. CLI untuk automation.

**Q: Apakah data aman?**  
A: Ya, semua data tersimpan lokal di SQLite database.

**Q: Bisa akses dari device lain?**  
A: Ya, gunakan `kiro start --host 0.0.0.0` lalu akses via IP.

**Q: Database bisa di-backup?**  
A: Ya, copy file `kiro.db` untuk backup.

**Q: Masih bisa pakai CLI command lama?**  
A: Ya, `python main.py` masih berfungsi normal.

---

## 📝 Changelog

### v1.0.0 - Web Dashboard Edition
- ✨ NEW: Web dashboard interface
- ✨ NEW: SQLite database
- ✨ NEW: REST API backend
- ✨ NEW: Real-time monitoring
- ✨ NEW: Click-to-copy tokens
- ✨ NEW: `kiro start` command
- ✅ CLI masih tersedia

---

## 📄 License

MIT License - Use at your own risk

---

**Happy Token Generating with Web Dashboard! 🎉**

**Version:** 1.0.0 Web Edition  
**Last Updated:** 2026-08-01
