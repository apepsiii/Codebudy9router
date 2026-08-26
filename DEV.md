# CodeBuddy Automation - Rencana Pengembangan

> Web automation untuk register dan login ke CodeBuddy.ai menggunakan akun Gmail, dengan tujuan mendapatkan cookies/session untuk keperluan pembelajaran.

> **📌 Proyek ini adalah ADAPTASI dari proyek Kiro Token Generator yang sudah ada. Struktur kode, arsitektur, dan flow akan mengikuti pola yang sama, hanya berbeda di target platform (Kiro → CodeBuddy).**

---

## Ringkasan Proyek

**Base Project:** Kiro Token Generator (existing)  
**New Target:** CodeBuddy.ai  
**Approach:** Reuse existing architecture, replace Kiro-specific logic with CodeBuddy logic

**Tujuan:** Membuat automation bot yang dapat melakukan registrasi/login ke CodeBuddy.ai menggunakan akun Gmail, lalu mengakses halaman profil sebagai indikator keberhasilan.

**Platform Target:** https://www.codebuddy.ai/

**Output:** Cookies/session yang valid untuk akses ke CodeBuddy.ai

### Perbedaan dengan Proyek Kiro

| Aspek | Kiro Project | CodeBuddy Project |
|-------|--------------|-------------------|
| **Target Platform** | kiro.dev | codebuddy.ai |
| **Output** | Refresh Token (Cognito) | Cookies/Session |
| **OAuth Flow** | Kiro → Google → Cognito | CodeBuddy → Google → CodeBuddy |
| **Success Indicator** | Token extracted | Profile page accessed |
| **Extra Steps** | - | Service Agreement dialog |
| **Auth Domain** | amazoncognito.com | codebuddy.ai/auth |

### Yang Dapat Dipakai Ulang

✅ **Struktur Project:**
- File structure (main.py, web/, database.py)
- CLI interface pattern
- Web dashboard (FastAPI + Alpine.js)
- Database schema (dengan sedikit modifikasi)

✅ **Core Logic:**
- Playwright automation framework
- Human-like typing mechanism
- Multi-worker processing
- Retry & error handling
- Live logging system

✅ **Features:**
- Bulk import accounts
- Export hasil (cookies instead of tokens)
- Web dashboard UI/UX
- Statistics & monitoring

---

## Alur Automation

### 1. Landing Page
- URL: `https://www.codebuddy.ai/home`
- Aksi: Cari dan klik tombol/link "Login"

### 2. Persetujuan Awal
- Checklist: "I confirm that xxx"
- Aksi: Centang checkbox konfirmasi
- Klik: "Sign up with Google"

### 3. Service Agreement
- Dialog: Service Agreement and Privacy Terms
- Isi: 
  - Privacy Policy
  - Data Processing and Security Agreement
  - Tencent Cloud CodeBuddy Service Agreement
  - OneID User Service Agreement
  - OneID Privacy Policy
- Aksi: Klik tombol "Confirm"

### 4. Login Google
- Redirect ke Google OAuth
- Aksi:
  - Input email (typing seperti manusia dengan delay)
  - Klik "Next"
  - Input password (typing seperti manusia dengan delay)
  - Klik "Next"

### 5. Google Workspace Prompt (Conditional)
- Kondisi: Jika akun GSuite/Workspace baru
- Prompt: Izin akses atau "I Understand"
- Aksi: Klik tombol konfirmasi

### 6. Return ke CodeBuddy
- Redirect: Kembali ke codebuddy.ai
- Dialog: Pilih "Lanjutkan" atau "Continue"
- Aksi: Klik tombol lanjutkan

### 7. Verifikasi Sukses
- Target: `https://www.codebuddy.ai/profile/`
- Aksi: 
  - Navigasi ke halaman profil (atau akses langsung URL)
  - Verifikasi halaman profil ter-load
  - Capture cookies/session
  - Tandai sebagai **BERHASIL**

---

## Teknologi Stack

### Core
- **Python 3.8+**
- **Playwright** - Browser automation
- **playwright-stealth** - Anti-detection

### Supporting
- **FastAPI** - Web dashboard (optional)
- **SQLAlchemy** - Database ORM
- **SQLite** - Data storage
- **Rich** - CLI output formatting

### Browser
- **Chromium** - Via Playwright

---

## Struktur File (Rencana)

```
Codebudy9router/
├── main.py                     ← Entry point CLI
├── codebuddy.py                ← Automation logic utama
├── codebuddy.db                ← SQLite database
├── cookies_codebuddy.json      ← Output cookies
├── account.txt                 ← Input akun (email:password)
├── requirements.txt            ← Dependencies
├── web/
│   ├── app.py                  ← FastAPI backend
│   ├── database.py             ← Models & DB schema
│   └── static/
│       └── index.html          ← Web dashboard UI
├── DEV.md                      ← File ini
└── PROJECT.md                  ← Dokumentasi lengkap
```

---

## Database Schema

### Table: accounts
| Column | Type | Keterangan |
|--------|------|-----------|
| id | INTEGER PRIMARY KEY | Auto increment |
| email | TEXT UNIQUE NOT NULL | Email Gmail |
| password | TEXT NOT NULL | Password Gmail |
| status | TEXT | pending/processing/success/failed |
| cookies | TEXT | JSON cookies (jika berhasil) |
| profile_url | TEXT | URL profil (verifikasi) |
| error_message | TEXT | Pesan error (jika gagal) |
| created_at | TIMESTAMP | Waktu dibuat |
| updated_at | TIMESTAMP | Waktu update terakhir |

### Table: config
| Column | Type | Keterangan |
|--------|------|-----------|
| key | TEXT PRIMARY KEY | Config key |
| value | TEXT | Config value (JSON) |

### Table: process_logs
| Column | Type | Keterangan |
|--------|------|-----------|
| id | INTEGER PRIMARY KEY | Auto increment |
| account_id | INTEGER | FK ke accounts |
| step | TEXT | Nama step yang dijalankan |
| status | TEXT | success/failed/warning |
| message | TEXT | Detail log |
| timestamp | TIMESTAMP | Waktu log |

---

## Fitur Utama

### 1. CLI Mode
```bash
# Process semua akun
python main.py

# Process N akun dengan M workers
python main.py 10 4

# Visible mode (tampilkan browser)
python main.py 10 4 --visible

# Manual mode (user login, bot capture cookies)
python main.py --manual --visible

# List akun yang sudah diproses
python main.py --list

# Export cookies
python main.py --export-cookies
```

### 2. Web Dashboard
- **URL:** `http://localhost:8000`
- **Fitur:**
  - Add accounts (single/bulk)
  - Start/stop processing
  - Live log realtime
  - Statistics (total, success, failed)
  - Export cookies (JSON/Text)
  - Filter by status
  - Retry failed accounts

### 3. Automation Features
- **Human-like typing** dengan random delay
- **Anti-detection** via playwright-stealth
- **Retry mechanism** untuk step yang gagal
- **Cookie capture** otomatis setelah login berhasil
- **Multi-worker** parallel processing
- **Resume support** (skip akun yang sudah sukses)

---

## Tahapan Pengembangan

### Phase 0: Code Adaptation dari Kiro Project 🔄
- [ ] Copy base structure dari main.py (Kiro)
- [ ] Rename variabel Kiro → CodeBuddy
- [ ] Update URL constants:
  - [ ] `KIRO_LANDING_URL` → `CODEBUDDY_LANDING_URL`
  - [ ] `KIRO_SIGNIN_URL` → `CODEBUDDY_SIGNIN_URL`
  - [ ] Auth domains
- [ ] Modifikasi database schema:
  - [ ] Replace `refresh_token` column → `cookies`
  - [ ] Add `profile_url` column
  - [ ] Keep structure sama untuk reuse web dashboard
- [ ] Update file names:
  - [ ] `kiro.py` → `codebuddy.py`
  - [ ] `kiro.db` → `codebuddy.db`
  - [ ] `kiro_tokens.txt` → `cookies_codebuddy.json`

### Phase 1: Core Automation ✅ (Target)
- [ ] Setup project structure (reuse dari Kiro)
- [ ] Install dependencies (sudah ada dari requirements.txt)
- [ ] **Implementasi CodeBuddy-specific flow:**
  - [ ] Navigate ke landing page (`/home`)
  - [ ] Klik login button
  - [ ] **[NEW]** Handle checkbox "I confirm that xxx"
  - [ ] Klik "Sign up with Google"
  - [ ] **[NEW]** Handle Service Agreement dialog
  - [ ] **[NEW]** Klik "Confirm" pada agreement
- [ ] **Reuse Google OAuth logic dari Kiro:**
  - [ ] Input email (human-like typing) ✅ sudah ada
  - [ ] Input password (human-like typing) ✅ sudah ada
  - [ ] Handle "Next" buttons ✅ sudah ada
  - [ ] Handle conditional GSuite prompt ✅ sudah ada
- [ ] **[NEW]** Return ke CodeBuddy:
  - [ ] Detect redirect dari Google
  - [ ] Klik "Lanjutkan/Continue"
- [ ] **[MODIFIED]** Verifikasi & capture:
  - [ ] Navigate ke `/profile/`
  - [ ] Verifikasi page load
  - [ ] Capture cookies (bukan token)
  - [ ] Save ke database/file

### Phase 2: Database & Storage (Reuse dari Kiro)
- [ ] ✅ Setup SQLite database (struktur sama)
- [ ] ✅ Create tables (modifikasi column saja)
- [ ] ✅ Implement CRUD operations (reuse)
- [ ] 🔄 Cookie storage & retrieval (ganti dari token)
- [ ] ✅ Process logging system (reuse)

### Phase 3: CLI Interface (Reuse dari Kiro)
- [ ] ✅ Argument parser (argparse) - reuse
- [ ] ✅ Rich console output - reuse
- [ ] ✅ Progress tracking - reuse
- [ ] ✅ Worker pool management - reuse
- [ ] 🔄 Export functionality (export cookies, bukan token)

### Phase 4: Error Handling (Reuse dari Kiro)
- [ ] ✅ Timeout handling - reuse
- [ ] ✅ Retry mechanism - reuse
- [ ] ✅ Error logging - reuse
- [ ] ✅ Fallback strategies - reuse
- [ ] 🔄 Conditional steps (tambah Service Agreement handling)

### Phase 5: Web Dashboard (Reuse dari Kiro)
- [ ] ✅ FastAPI backend - reuse dengan minor adjustment
- [ ] ✅ REST API endpoints - reuse struktur
- [ ] ✅ Frontend UI (Alpine.js + Tailwind) - reuse, ganti branding
- [ ] ✅ Real-time updates - reuse
- [ ] 🔄 Export features (cookies format)

### Phase 6: Testing & Optimization
- [ ] Test dengan berbagai kondisi
- [ ] Optimize selector strategies (CodeBuddy-specific)
- [ ] Performance tuning
- [ ] Anti-detection improvements
- [ ] Documentation

---

## Selector Strategy

### Approach
1. **Prioritas:** `data-testid` > `id` > `class` > `text` > `xpath`
2. **Fallback:** Multiple selector untuk setiap element
3. **Wait Strategy:** Wait for element dengan timeout yang sesuai

### Key Selectors (Perlu Inspect)

```python
SELECTORS = {
    "landing": {
        "login_button": [
            'button:has-text("Login")',
            'a:has-text("Login")',
            '[data-testid="login-button"]',
        ]
    },
    "signup": {
        "confirm_checkbox": [
            'input[type="checkbox"]',
            '[data-testid="confirm-checkbox"]',
        ],
        "google_signup_button": [
            'button:has-text("Sign up with Google")',
            '[data-testid="google-signup"]',
        ]
    },
    "agreement": {
        "confirm_button": [
            'button:has-text("Confirm")',
            '[data-testid="agreement-confirm"]',
        ]
    },
    "google_oauth": {
        "email_input": 'input[type="email"]',
        "password_input": 'input[type="password"]',
        "next_button": 'button:has-text("Next")',
        "gsuite_understand": 'button:has-text("I understand")',
    },
    "codebuddy_return": {
        "continue_button": [
            'button:has-text("Lanjutkan")',
            'button:has-text("Continue")',
            '[data-testid="continue-button"]',
        ]
    },
    "profile": {
        "verify_element": [
            '.profile-container',
            '[data-testid="profile-page"]',
            'h1:has-text("Profile")',
        ]
    }
}
```

---

## Challenges & Solutions

### Challenge 1: Service Agreement Dialog
**Problem:** Dialog mungkin tidak muncul setiap kali  
**Solution:** Conditional check dengan timeout pendek, skip jika tidak ada

### Challenge 2: Google Workspace Prompt
**Problem:** Hanya muncul untuk akun GSuite baru  
**Solution:** Conditional handling, detect & handle jika ada

### Challenge 3: Anti-bot Detection
**Problem:** CodeBuddy mungkin punya anti-bot  
**Solution:** 
- playwright-stealth
- Human-like typing dengan delay random
- Random user agent
- Headless detection bypass

### Challenge 4: Dynamic Selectors
**Problem:** Selector bisa berubah  
**Solution:** Multiple selector fallbacks per element

### Challenge 5: Timing Issues
**Problem:** Page load timing tidak konsisten  
**Solution:** Smart waiting strategies (wait for network idle, specific elements)

---

## Configuration

### Process Settings
```python
CONFIG = {
    "workers": 2,              # Parallel workers
    "delay_between": 3.0,      # Delay antar akun (detik)
    "typing_delay_min": 50,    # Min typing delay (ms)
    "typing_delay_max": 150,   # Max typing delay (ms)
    "timeout_navigation": 30,  # Timeout navigasi (detik)
    "timeout_element": 10,     # Timeout element (detik)
    "headless": True,          # Headless mode
    "stealth": True,           # Enable stealth
}
```

### Retry Strategy
```python
RETRY_CONFIG = {
    "max_retries": 3,
    "retry_delay": 5,          # Detik
    "exponential_backoff": True,
}
```

---

## API Endpoints (Web Dashboard)

| Method | Endpoint | Keterangan |
|--------|----------|-----------|
| GET | `/api/stats` | Dashboard statistics |
| GET | `/api/accounts` | List semua akun |
| POST | `/api/accounts` | Tambah akun baru |
| POST | `/api/accounts/bulk` | Bulk import akun |
| DELETE | `/api/accounts/{id}` | Hapus akun |
| POST | `/api/process/start` | Start processing |
| POST | `/api/process/stop` | Stop processing |
| GET | `/api/logs/{id}` | Get logs per akun |
| GET | `/api/logs/recent` | Real-time logs |
| POST | `/api/export/cookies` | Export cookies |

---

## Testing Checklist

### Manual Testing
- [ ] Test dengan 1 akun baru (register flow)
- [ ] Test dengan 1 akun existing (login flow)
- [ ] Test dengan akun GSuite (conditional prompt)
- [ ] Test dengan akun regular Gmail
- [ ] Test retry mechanism
- [ ] Test timeout handling
- [ ] Test cookie capture & storage

### Automation Testing
- [ ] Unit test per step
- [ ] Integration test full flow
- [ ] Error scenario testing
- [ ] Performance test (10+ workers)

---

## Success Criteria

✅ Bot berhasil jika:
1. Login ke CodeBuddy berhasil
2. Halaman `/profile/` ter-load dengan benar
3. Cookies tersimpan di database/file
4. Cookies valid untuk akses selanjutnya
5. Error rate < 10% untuk batch processing

---

## Timeline Estimasi

| Phase | Estimasi (Original) | Estimasi (Reuse) | Target |
|-------|---------------------|------------------|--------|
| Phase 0: Code Adaptation | - | **1-2 hari** | Week 1 |
| Phase 1: Core Automation | 2-3 hari | **2-3 hari** | Week 1 |
| Phase 2: Database & Storage | 1 hari | **0.5 hari** ✅ reuse | Week 1 |
| Phase 3: CLI Interface | 1 hari | **0.5 hari** ✅ reuse | Week 1 |
| Phase 4: Error Handling | 1-2 hari | **0.5 hari** ✅ reuse | Week 1 |
| Phase 5: Web Dashboard | 2-3 hari | **1 hari** ✅ reuse | Week 2 |
| Phase 6: Testing & Optimization | 2 hari | **1-2 hari** | Week 2 |
| **Total** | **9-12 hari** | **5-8 hari** 🚀 | **1-2 minggu** |

**💡 Keuntungan reuse dari Kiro project: menghemat 4-5 hari development time!**

---

## Dependencies

```txt
# requirements.txt (sama dengan Kiro project)
playwright>=1.40.0
playwright-stealth>=1.0.6
fastapi>=0.104.0
uvicorn>=0.24.0
sqlalchemy>=2.0.0
aiosqlite>=0.19.0
pydantic>=2.5.0
rich>=13.7.0
openpyxl>=3.1.0
```

**Note:** Dependencies sudah tersedia di `requirements-web.txt` dan `requirements.txt` dari proyek Kiro.

---

## Code Reuse Strategy

### 1. File yang Bisa Langsung Copy + Rename
✅ **Full Reuse (minor changes):**
- `kiro.py` → `codebuddy.py` (CLI entry point)
- `web/database.py` → modify schema sedikit
- `web/static/index.html` → ganti branding CodeBuddy

### 2. File yang Perlu Modifikasi Significant
🔄 **Partial Reuse:**
- `main.py` → `main_codebuddy.py`
  - Keep: Google OAuth flow, typing logic, worker pool
  - Change: URL constants, flow steps (add agreement dialog)
  - Change: Token extraction → Cookie extraction
- `web/app.py` → minor changes di endpoint `/export/`

### 3. Function yang 100% Reuse
✅ **No changes needed:**
- `human_type()` - typing simulation
- `wait_for_element()` - element waiting
- Worker pool management
- Database CRUD operations
- CLI argument parser
- Rich console rendering
- Live log streaming

### 4. New Code yang Perlu Dibuat
🆕 **CodeBuddy-specific:**
- Service Agreement dialog handler
- "I confirm that xxx" checkbox handler
- CodeBuddy return flow handler
- Cookie extraction & validation
- Profile page verification

---

## Migration Plan (Kiro → CodeBuddy)

### Step 1: Prepare New Files
```bash
# Copy base files
cp main.py main_codebuddy.py
cp kiro.py codebuddy.py
cp -r web/ web_codebuddy/

# Keep same structure
```

### Step 2: Update Constants
```python
# Before (Kiro)
KIRO_LANDING_URL = "https://kiro.dev/"
KIRO_SIGNIN_URL = "https://app.kiro.dev/signin"
KIRO_AUTH_DOMAIN = "kiro-prod-us-east-1.auth.us-east-1.amazoncognito.com"

# After (CodeBuddy)
CODEBUDDY_LANDING_URL = "https://www.codebuddy.ai/home"
CODEBUDDY_LOGIN_URL = "https://www.codebuddy.ai/login"
CODEBUDDY_PROFILE_URL = "https://www.codebuddy.ai/profile/"
```

### Step 3: Modify Flow Function
```python
# Kiro flow
async def process_kiro_login(page, email, password):
    # 1. Go to signin
    # 2. Click Google OAuth
    # 3. Login Google
    # 4. Extract token from Cognito

# CodeBuddy flow (adapted)
async def process_codebuddy_login(page, email, password):
    # 1. Go to home
    # 2. Click login
    # 3. [NEW] Check "I confirm"
    # 4. Click "Sign up with Google"
    # 5. [NEW] Handle Service Agreement
    # 6. Login Google (REUSE)
    # 7. [NEW] Click "Lanjutkan"
    # 8. Go to /profile/
    # 9. Extract cookies
```

### Step 4: Database Schema Changes
```python
# Change column name
# Before: refresh_token TEXT
# After:  cookies TEXT

# Add new column
# profile_url TEXT

# Keep everything else same
```

---

## Next Steps

1. ✅ Buat file `DEV.md` (dokumen ini)
2. ⏳ **Inspect selectors di CodeBuddy.ai** (prioritas tinggi)
3. ⏳ Copy & rename files dari Kiro project
4. ⏳ Update constants & URLs
5. ⏳ Implementasi CodeBuddy-specific handlers
6. ⏳ Testing dengan 1 akun
7. ⏳ Integration dengan web dashboard
8. ⏳ Batch testing & optimization

---

## Notes

- Proyek ini untuk **keperluan pembelajaran** automation
- Pastikan comply dengan Terms of Service CodeBuddy.ai
- Gunakan rate limiting untuk menghindari ban
- Simpan credentials dengan aman (jangan commit ke git)
- Cookies bersifat sensitif, handle dengan hati-hati

---

## References

- Playwright Docs: https://playwright.dev/python/
- playwright-stealth: https://github.com/AtuboDad/playwright_stealth
- CodeBuddy.ai: https://www.codebuddy.ai/

---

**Last Updated:** 2026-08-26  
**Author:** Development Team  
**Status:** 🟡 Planning Phase
