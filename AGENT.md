# CodeBuddy Automation Agent

> AI Agent instructions untuk mengembangkan CodeBuddy automation bot - adaptasi dari Kiro Token Generator project.

---

## Context

Kamu adalah AI agent yang bertugas mengembangkan **CodeBuddy Automation Bot**, sebuah web automation tool untuk register/login ke CodeBuddy.ai menggunakan akun Gmail dan mengambil cookies/session.

**Base Project:** Kiro Token Generator (existing codebase)  
**Target:** CodeBuddy.ai  
**Approach:** Reuse existing architecture, replace Kiro logic dengan CodeBuddy logic

---

## Project Structure

```
Codebudy9router/
├── main.py                     # Kiro automation (existing)
├── kiro.py                     # Kiro CLI (existing)
├── kiro.db                     # Kiro database
├── web/                        # Web dashboard (existing)
│   ├── app.py                  # FastAPI backend
│   ├── database.py             # SQLAlchemy models
│   └── static/
│       └── index.html          # Dashboard UI
├── main_codebuddy.py           # [TO CREATE] CodeBuddy automation
├── codebuddy.py                # [TO CREATE] CodeBuddy CLI
├── codebuddy.db                # [TO CREATE] CodeBuddy database
├── cookies_codebuddy.json      # [TO CREATE] Output cookies
├── DEV.md                      # Development plan
├── AGENT.md                    # This file
├── PROJECT.md                  # Kiro documentation
└── README.md                   # Project readme
```

---

## Your Role

Sebagai AI agent, kamu bertanggung jawab untuk:

1. **Memahami existing codebase** (Kiro project)
2. **Mengadaptasi code** untuk target baru (CodeBuddy)
3. **Implementasi CodeBuddy-specific features**
4. **Testing & debugging**
5. **Documentation**

---

## Development Guidelines

### 1. Code Reuse Strategy

**DO:**
- ✅ Reuse struktur project dari Kiro
- ✅ Reuse Google OAuth flow (human-like typing, navigation)
- ✅ Reuse database architecture (modify schema)
- ✅ Reuse web dashboard (change branding)
- ✅ Reuse CLI interface & Rich console output
- ✅ Reuse worker pool & retry mechanism

**DON'T:**
- ❌ Rewrite code yang sudah ada dan berfungsi
- ❌ Mengubah core architecture tanpa alasan kuat
- ❌ Membuat dependency baru yang tidak perlu

### 2. CodeBuddy-Specific Implementation

**Yang Perlu Dibuat Baru:**

```python
# 1. Constants
CODEBUDDY_LANDING_URL = "https://www.codebuddy.ai/home"
CODEBUDDY_LOGIN_URL = "https://www.codebuddy.ai/login"
CODEBUDDY_PROFILE_URL = "https://www.codebuddy.ai/profile/"

# 2. New Handlers
async def handle_confirm_checkbox(page):
    """Handle 'I confirm that xxx' checkbox"""
    pass

async def handle_service_agreement(page):
    """Handle Service Agreement dialog + click Confirm"""
    pass

async def handle_codebuddy_return(page):
    """Handle return dari Google OAuth, click 'Lanjutkan'"""
    pass

async def extract_cookies(page):
    """Extract cookies setelah login berhasil"""
    pass

async def verify_profile_page(page):
    """Verify halaman /profile/ loaded successfully"""
    pass
```

### 3. Flow Comparison

**Kiro Flow:**
```
1. Go to signin page
2. Click Google OAuth
3. Login with Google (email + password)
4. Handle GSuite prompt (conditional)
5. Extract refresh token from Cognito
6. Save token to database
```

**CodeBuddy Flow:**
```
1. Go to home page
2. Click login button
3. [NEW] Check "I confirm that xxx"
4. Click "Sign up with Google"
5. [NEW] Handle Service Agreement dialog
6. Login with Google (REUSE dari Kiro)
7. Handle GSuite prompt (REUSE dari Kiro)
8. [NEW] Click "Lanjutkan/Continue"
9. Navigate to /profile/
10. Extract cookies
11. Save cookies to database
```

### 4. Selector Discovery

Sebelum implementasi, kamu HARUS inspect selectors di CodeBuddy.ai:

```python
# Prioritas selector: data-testid > id > class > text > xpath

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

**Action:** Gunakan browser DevTools atau Playwright inspector untuk menemukan selector yang tepat.

### 5. Database Schema Changes

```python
# Modify existing Kiro schema

# BEFORE (Kiro)
class Account(Base):
    email = Column(String, unique=True)
    password = Column(String)
    status = Column(String)  # pending/processing/success/failed
    refresh_token = Column(String)  # Kiro token
    injected = Column(Boolean)
    router_connection_id = Column(String)

# AFTER (CodeBuddy)
class Account(Base):
    email = Column(String, unique=True)
    password = Column(String)
    status = Column(String)  # pending/processing/success/failed
    cookies = Column(String)  # JSON cookies (CHANGED)
    profile_url = Column(String)  # NEW: verification URL
    error_message = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
```

### 6. Error Handling

**Mandatory checks:**

```python
# 1. Timeout handling
try:
    await page.wait_for_selector(selector, timeout=10000)
except TimeoutError:
    log_error(f"Element not found: {selector}")
    # Try fallback selector or fail gracefully

# 2. Conditional elements
try:
    agreement_dialog = await page.wait_for_selector(
        '.agreement-dialog', 
        timeout=5000
    )
    await handle_service_agreement(page)
except TimeoutError:
    # Dialog tidak muncul, skip
    pass

# 3. Cookie validation
cookies = await page.context.cookies()
if not cookies or len(cookies) == 0:
    raise Exception("No cookies captured")
```

### 7. Testing Requirements

**Manual Testing Checklist:**
- [ ] Test dengan 1 akun Gmail baru (register flow)
- [ ] Test dengan 1 akun Gmail existing (login flow)
- [ ] Test dengan akun GSuite (conditional prompt)
- [ ] Test retry mechanism saat gagal
- [ ] Verify cookies tersimpan dengan benar
- [ ] Verify cookies bisa digunakan untuk akses ulang

**Automated Testing:**
- [ ] Unit test per handler function
- [ ] Integration test full flow
- [ ] Error scenario testing
- [ ] Performance test (multi-worker)

---

## Implementation Steps

### Phase 0: Code Adaptation (1-2 hari)

```bash
# 1. Copy base files
cp main.py main_codebuddy.py
cp kiro.py codebuddy.py

# 2. Update imports & constants
# 3. Modify database schema
# 4. Test basic structure
```

### Phase 1: Core Automation (2-3 hari)

**Tasks:**
1. Inspect selectors di CodeBuddy.ai
2. Implementasi `handle_confirm_checkbox()`
3. Implementasi `handle_service_agreement()`
4. Implementasi `handle_codebuddy_return()`
5. Implementasi `extract_cookies()`
6. Implementasi `verify_profile_page()`
7. Integration test end-to-end
8. Fix bugs & optimize

### Phase 2-5: Reuse & Adapt (2-3 hari)

**Tasks:**
1. Database setup (reuse dengan modify schema)
2. CLI interface (reuse, ganti branding)
3. Web dashboard (reuse, adjust endpoints)
4. Export functionality (cookies format)
5. Testing & documentation

---

## Code Quality Standards

### 1. Code Style
- Follow PEP 8
- Type hints untuk function signatures
- Docstrings untuk public functions
- Comments untuk logic kompleks

### 2. Error Messages
```python
# BAD
raise Exception("Error")

# GOOD
raise Exception(f"Failed to click login button: {selector} not found after 10s timeout")
```

### 3. Logging
```python
# Use structured logging
log_info(f"[{email}] Starting CodeBuddy login flow")
log_info(f"[{email}] Clicked login button")
log_info(f"[{email}] Checking 'I confirm' checkbox")
log_success(f"[{email}] Login successful, cookies saved")
log_error(f"[{email}] Login failed: {error_message}")
```

### 4. Configuration
```python
# Centralized config
CONFIG = {
    "workers": 2,
    "delay_between": 3.0,
    "typing_delay_min": 50,
    "typing_delay_max": 150,
    "timeout_navigation": 30,
    "timeout_element": 10,
    "headless": True,
    "stealth": True,
}
```

---

## Communication Protocol

### When to Ask User

**ASK jika:**
- ❓ Selector tidak ditemukan dan butuh manual inspection
- ❓ Flow berbeda dari ekspektasi (ada step tambahan)
- ❓ Butuh credential untuk testing
- ❓ Keputusan architecture yang significant

**DON'T ASK jika:**
- ✅ Bug minor yang bisa langsung difix
- ✅ Code style improvements
- ✅ Error handling implementation
- ✅ Testing & documentation

### Progress Updates

**Format:**
```
Phase X: [Task Name]
Status: ✅ Done / 🔄 In Progress / ❌ Blocked

Progress:
- [x] Task 1 completed
- [x] Task 2 completed
- [ ] Task 3 in progress

Issues:
- Issue 1: Description + solution

Next Steps:
- Step 1
- Step 2
```

---

## Success Criteria

Bot dianggap berhasil jika:

✅ **Functional:**
1. Login ke CodeBuddy.ai berhasil
2. Halaman `/profile/` ter-load dengan benar
3. Cookies tersimpan di database
4. Cookies valid untuk akses selanjutnya
5. Error rate < 10% untuk batch processing

✅ **Technical:**
1. Code reuse dari Kiro minimal 60%
2. Selector strategy dengan fallback
3. Error handling comprehensive
4. Logging clear & informative
5. Documentation lengkap

✅ **Performance:**
1. Single account: < 30 detik
2. Multi-worker: 2-5 accounts parallel
3. Success rate: > 90%
4. Memory usage: < 500MB per worker

---

## Resources

### Documentation
- **DEV.md** - Development plan & architecture
- **PROJECT.md** - Kiro project documentation (reference)
- **Playwright Docs** - https://playwright.dev/python/

### Code Reference
- **main.py** - Existing Kiro automation logic
- **kiro.py** - CLI implementation reference
- **web/app.py** - FastAPI backend reference
- **web/database.py** - Database schema reference

### Tools
- Playwright Inspector: `playwright codegen https://www.codebuddy.ai/home`
- Browser DevTools: F12 untuk inspect elements
- Rich Console: untuk debug & logging

---

## Timeline

| Phase | Duration | Status |
|-------|----------|--------|
| Phase 0: Code Adaptation | 1-2 hari | ⏳ Pending |
| Phase 1: Core Automation | 2-3 hari | ⏳ Pending |
| Phase 2: Database & Storage | 0.5 hari | ⏳ Pending |
| Phase 3: CLI Interface | 0.5 hari | ⏳ Pending |
| Phase 4: Error Handling | 0.5 hari | ⏳ Pending |
| Phase 5: Web Dashboard | 1 hari | ⏳ Pending |
| Phase 6: Testing & Optimization | 1-2 hari | ⏳ Pending |
| **Total** | **5-8 hari** | ⏳ Pending |

---

## Notes

- **Priority:** Core automation (Phase 0-1) harus solid dulu sebelum lanjut ke dashboard
- **Testing:** Test setiap step secara isolated sebelum integration
- **Documentation:** Update DEV.md setiap kali ada perubahan significant
- **Commit:** Commit setiap feature/fix selesai dengan message yang jelas

---

**Last Updated:** 2026-08-26  
**Agent Version:** 1.0  
**Status:** 🟡 Ready to Start
