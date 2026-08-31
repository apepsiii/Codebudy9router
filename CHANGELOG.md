# Changelog - V2Fun.ai Automation Project

## [2026-08-31] - Backend API for Hermes Agent

### Added
- **v2fun_backend_api.py**: REST API untuk integrasi dengan Hermes agent
  - Round-robin account selection (automatic load balancing)
  - Model priority system (nano-banana-pro → gpt-image-2 → nano-banana-2 → nano-banana-2-lite → qwen-edit)
  - Async job queue dengan background processing
  - Telegram notifications untuk setiap event (start/complete/fail)
  - Health check endpoint
  - Account status endpoint
  - Batch generation support

- **hermes_integration_example.py**: Complete integration examples
  - V2FunBackendClient class
  - HermesAgent workflow example
  - 4 usage examples (simple, batch, hermes workflow, different models)

- **test_backend_api.py**: Automated testing script
  - 6 automated tests
  - Individual test runner
  - Summary report

- **Launcher Scripts**:
  - run_backend_api.bat (Windows)
  - run_backend_api.sh (Linux/Mac)

- **.env.example**: Configuration template
  - Telegram bot settings
  - API configuration
  - Model priority
  - Job settings

### Documentation
- **V2FUN_BACKEND_API_GUIDE.md**: Complete integration guide
  - Architecture overview
  - API endpoints documentation
  - Round-robin explanation
  - Model priority system
  - Telegram notifications setup
  - Integration examples (Python, cURL)
  - Troubleshooting guide

### Features
- 🔄 Round-robin account rotation for load balancing
- 🎯 Model priority system (auto-fallback)
- 📱 Real-time Telegram notifications
- 📊 Job status tracking
- ⚡ Async processing
- 🔍 Health monitoring
- 🧪 Automated testing

### Technical Details
- Port: 5001 (separate from Web UI 5000)
- Threading: Background workers untuk async processing
- Database: SQLite (shared dengan Web UI)
- Token validation: Auto-check sebelum use
- Error handling: Comprehensive error responses

---

## [2026-08-29] - Token Refresh Analysis

### Analyzed
- **Token Refresh Mechanism**: Investigated V2Fun.ai untuk refresh token endpoint
  - ❌ Confirmed: NO refresh token endpoint exists
  - ❌ V2Fun.ai does NOT implement standard OAuth 2.0 refresh flow
  - ✅ JWT token only with ~3 days lifetime
  - ✅ Must re-login via Google OAuth when expired

### Added
- **TOKEN_REFRESH_ANALYSIS.md**: Comprehensive analysis document
  - Detailed investigation of all 31 API endpoints
  - JWT token structure analysis
  - Comparison with standard OAuth 2.0
  - Documentation of our headless re-login workaround
  - Best practices for production use

### Technical Details
- Token lifetime: ~259200 seconds (3 days)
- No refresh_token field in JWT payload
- No /auth/refresh or /token/refresh endpoint
- Workaround: Headless Playwright re-login (~15-20s, 95% success rate)

---

## [2026-08-27] - GSuite Welcome Screen Fix

### Fixed
- **GSuite Welcome Screen Handler**: Menangani popup "Welcome to your new account" yang muncul pada akun GSuite baru
  - Mendeteksi konten halaman welcome secara otomatis
  - Multiple selectors untuk tombol "I understand", "Got it", "Next", dll
  - Fallback mechanism dengan JavaScript click jika selector gagal
  - Fallback terakhir dengan keyboard Enter
  - Screenshot otomatis untuk debugging jika tombol tidak ditemukan
  - Mencegah popup tertutup prematur sebelum OAuth selesai

### Changed
- **OAuth Completion Detection**: Menggunakan URL monitoring untuk mendeteksi redirect sukses
  - Memonitor perubahan URL dari accounts.google.com ke v2fun.ai
  - Wait mechanism yang lebih baik untuk token synchronization
  - Graceful popup closing dengan retry mechanism

### Added
- **Debug Screenshots**: Otomatis menyimpan screenshot saat error
  - `v2fun_data/debug_welcome_screen_{email}.png` - Welcome screen yang tidak bisa di-handle
  - `v2fun_data/debug_email_page.png` - Email input page error
  - `v2fun_data/debug_password_page.png` - Password input page error
  - `v2fun_data/debug_error_page.png` - General error screenshot

### Technical Details
- File modified: `v2fun_scripts/v2fun_google_login.py`
- Function updated: `handle_google_login_popup()`
- New selectors added:
  - `button:has-text("I understand")`
  - `button:has-text("Understand")`
  - `button:has-text("Got it")`
  - `button:has-text("Saya mengerti")`
  - Multiple role and type selectors
- JavaScript fallback for button clicking when Playwright selectors fail

### Usage
```bash
# Test dengan akun GSuite baru
python v2fun_scripts/v2fun_google_login.py

# Jika masih gagal, cek screenshot di folder v2fun_data/
# untuk melihat tampilan popup yang sebenarnya
```

### Troubleshooting
1. **Popup masih tertutup sendiri**:
   - Check screenshot di `v2fun_data/debug_welcome_screen_*.png`
   - Lihat text exact dari tombol yang muncul
   - Tambahkan selector baru jika diperlukan

2. **Tombol tidak terdeteksi**:
   - Script akan otomatis mencoba JavaScript click
   - Jika gagal, akan press Enter sebagai fallback
   - Check console output untuk melihat selector mana yang dicoba

3. **OAuth tidak complete**:
   - Script akan menunggu hingga 30 detik untuk URL redirect
   - Jika timeout, popup akan ditutup manual
   - Check main page untuk memastikan token sudah tersimpan

---

## [2026-08-27] - Admin Account Management

### Added
- **create_admin.py**: CLI tool untuk membuat admin account
  ```bash
  python create_admin.py <email> <password>
  ```

- **manage_users.py**: Comprehensive user management CLI
  ```bash
  python manage_users.py list
  python manage_users.py create <email> <password>
  python manage_users.py reset <email> <new_password>
  ```

- **ADMIN_GUIDE.md**: Dokumentasi lengkap untuk admin management
  - Cara membuat akun admin
  - Cara reset password
  - Security best practices
  - Troubleshooting guide

### Changed
- **Web Registration**: Disabled untuk keamanan
  - Hanya admin yang bisa membuat akun via CLI
  - Route `/register` redirect ke `/login`
  - API `/api/register` mengembalikan error message

### Security
- Password di-hash dengan SHA-256
- Session token: 32-byte random, 7 hari expiry
- Akun admin default: `admin@v2fun.local`

---

## Previous Updates

### [2026-08-26] - Token Auto-Refresh
- JWT token monitoring
- Auto-refresh saat expired
- Headless re-login mechanism

### [2026-08-25] - Web UI Enhancement
- Dashboard quota monitoring
- SSE real-time updates
- Bulk account processing
- Export/import functionality

### [2026-08-24] - Initial Release
- Google OAuth automation
- Multi-account support
- Token extraction
- Database integration

---

**Project**: V2Fun.ai API Automation  
**Repository**: https://github.com/apepsiii/Codebudy9router  
**Maintainer**: apepsiii
