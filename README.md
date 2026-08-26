# CodeBuddy Automation Bot

> Web automation tool untuk register/login ke CodeBuddy.ai menggunakan akun Gmail dan mengambil cookies/session untuk keperluan pembelajaran.

**Base Project:** Adaptasi dari [Kiro Token Generator](https://github.com/apepsiii/Codebudy9router)

---

## 🚀 Features

- ✅ **Automated Google OAuth Login** - Login otomatis menggunakan Gmail
- ✅ **Human-like Typing** - Mengetik seperti manusia dengan random delay
- ✅ **Anti-detection** - Menggunakan playwright-stealth untuk bypass detection
- ✅ **Multi-worker** - Process multiple accounts parallel
- ✅ **Cookie Capture** - Automatic cookie extraction setelah login
- ✅ **Resume Support** - Skip akun yang sudah berhasil
- ✅ **Manual Mode** - User login manual, bot capture cookies otomatis
- ✅ **Rich Console Output** - Beautiful CLI dengan progress tracking

---

## 📋 Requirements

- Python 3.8+
- pip

---

## 🔧 Installation

### 1. Install Dependencies

```bash
pip install -r requirements-web.txt
```

Packages yang diinstall:
- `playwright` - Browser automation
- `playwright-stealth` - Anti-detection
- `rich` - Beautiful CLI output
- `fastapi` - Web dashboard (optional)
- `uvicorn` - Web server (optional)

### 2. Install Browser

```bash
playwright install chromium
```

---

## 📖 Usage

### Quick Start

```bash
# Process all accounts dengan 2 workers
python main_codebuddy.py

# Process 10 accounts dengan 4 workers
python main_codebuddy.py 10 4

# Show browser (non-headless mode)
python main_codebuddy.py 10 4 --visible

# Manual mode (user login manual, bot capture cookies)
python main_codebuddy.py --manual --visible

# List processed accounts
python main_codebuddy.py --list
```

### File Input

Buat file `account.txt` dengan format:
```
email1@gmail.com:password1
email2@gmail.com:password2
email3@gmail.com:password3
```

### Command Options

```bash
python main_codebuddy.py [jumlah] [workers] [options]

Positional Arguments:
  jumlah              Jumlah akun yang diproses (default: all)
  workers             Jumlah worker paralel (default: 2)

Options:
  -a, --accounts FILE    Path file akun (default: account.txt)
  -o, --output FILE      Path output cookies (default: cookies_codebuddy.json)
  -d, --delay SECONDS    Delay antar batch (default: 3.0)
  --visible              Tampilkan browser (default: headless)
  --register             Mode register (akun baru)
  --list                 List akun dari account_codebuddy.json
  --manual               Mode manual (user login, bot capture)
```

---

## 🔄 Automation Flow

1. **Navigate** ke `https://www.codebuddy.ai/home`
2. **Click** tombol "Login"
3. **Handle** checkbox "I confirm that xxx"
4. **Click** "Sign up with Google"
5. **Handle** Service Agreement dialog (conditional)
6. **Login** dengan Google OAuth:
   - Input email (human-like typing)
   - Input password (human-like typing)
   - Handle GSuite prompt (conditional)
7. **Return** ke CodeBuddy (klik "Continue/Lanjutkan")
8. **Navigate** ke `/profile/`
9. **Capture** cookies
10. **Save** ke file

---

## 📁 File Structure

```
Codebudy9router/
├── main_codebuddy.py           # Main automation script
├── account.txt                 # Input accounts (email:password)
├── cookies_codebuddy.json      # Output cookies (JSON)
├── account_codebuddy.json      # Process log (email → status/cookies)
├── requirements-web.txt        # Python dependencies
├── DEV.md                      # Development plan
├── AGENT.md                    # AI agent instructions
├── PROJECT.md                  # Kiro project documentation
└── README.md                   # This file
```

---

## 📊 Output Files

### 1. `cookies_codebuddy.json`
Cookies hasil capture per akun:
```json
{
  "user@gmail.com": {
    "cookies": [...],
    "profile_url": "https://www.codebuddy.ai/profile/",
    "timestamp": "2026-08-26 10:30:45"
  }
}
```

### 2. `account_codebuddy.json`
Log proses per akun:
```json
{
  "user@gmail.com": {
    "success": true,
    "cookies": {...},
    "profile_url": "https://www.codebuddy.ai/profile/",
    "error": "",
    "timestamp": "2026-08-26 10:30:45"
  }
}
```

---

## 🎯 Success Criteria

Bot dianggap berhasil jika:
1. ✅ Login ke CodeBuddy.ai berhasil
2. ✅ Halaman `/profile/` ter-load dengan benar
3. ✅ Cookies tersimpan di file
4. ✅ Cookies valid untuk akses selanjutnya
5. ✅ Error rate < 10% untuk batch processing

---

## 🐛 Troubleshooting

### Browser tidak ditemukan
```bash
playwright install chromium
```

### Syntax Error
```bash
python -m py_compile main_codebuddy.py
```

### Cookies tidak ter-capture
- Pastikan halaman profile berhasil dimuat
- Coba gunakan `--visible` mode untuk debug
- Check network connection

### Akun gagal login
- Verify email & password correct
- Check for 2FA/verification
- Try `--manual` mode

---

## ⚙️ Configuration

### Browser Settings
- **Headless:** Default `True`, gunakan `--visible` untuk show browser
- **Workers:** Default `2`, increase untuk faster processing
- **Delay:** Default `3.0s` antar batch

### Typing Simulation
- **Delay per char:** 50-100ms (random)
- **Delay after action:** 0.3-0.8s (random)

---

## 🔒 Security Notes

- ⚠️ Jangan commit file `account.txt` ke git
- ⚠️ Cookies bersifat sensitif, jangan share
- ⚠️ Gunakan untuk pembelajaran saja
- ⚠️ Respect CodeBuddy.ai Terms of Service

---

## 📝 Development

### Phase Status

- ✅ **Phase 0:** Code Adaptation dari Kiro (1-2 hari)
- ✅ **Phase 1:** Core Automation (2-3 hari)
- ⏳ **Phase 2:** Database & Storage (0.5 hari)
- ⏳ **Phase 3:** CLI Interface (0.5 hari)
- ⏳ **Phase 4:** Error Handling (0.5 hari)
- ⏳ **Phase 5:** Web Dashboard (1 hari)
- ⏳ **Phase 6:** Testing & Optimization (1-2 hari)

**Total Estimasi:** 5-8 hari

### Documentation

- `DEV.md` - Development plan & architecture
- `AGENT.md` - AI agent instructions
- `PROJECT.md` - Kiro project reference

---

## 🤝 Contributing

Contributions are welcome! Please read the development docs first.

---

## 📄 License

For educational purposes only.

---

## 🙏 Credits

- Base project: [Kiro Token Generator](https://github.com/apepsiii/Codebudy9router)
- Playwright: https://playwright.dev/python/
- playwright-stealth: https://github.com/AtuboDad/playwright_stealth

---

**Last Updated:** 2026-08-26  
**Version:** 1.0.0  
**Status:** 🟢 Phase 1 Complete
