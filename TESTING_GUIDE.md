# Testing Guide - CodeBuddy Automation

> Step-by-step guide untuk testing CodeBuddy automation bot

---

## 🎯 Testing Phases

### Phase 1: Manual Inspection ✅
**Status:** Ready  
**Action Required:** Manual selector inspection

### Phase 2: Manual Mode Test
**Status:** Ready  
**Goal:** Verify bot can capture cookies when user login manually

### Phase 3: Single Account Test
**Status:** Pending Phase 2  
**Goal:** Verify full automation works with 1 account

### Phase 4: Batch Test
**Status:** Pending Phase 3  
**Goal:** Verify multi-worker processing

---

## 📋 Pre-Testing Checklist

- [ ] Python 3.8+ installed
- [ ] Dependencies installed: `pip install -r requirements-web.txt`
- [ ] Playwright browser installed: `playwright install chromium`
- [ ] Test account prepared (Gmail with password)
- [ ] Create `account.txt` from `account.txt.example`
- [ ] Selectors inspected (see `SELECTOR_GUIDE.md`)

---

## 🧪 Test 1: Manual Mode (User Login, Bot Capture)

### Purpose
Verify bot can capture cookies without doing automation.

### Steps

```bash
# 1. Prepare account file
echo "your-email@gmail.com:not-used-in-manual" > account.txt

# 2. Run manual mode with visible browser
python main_codebuddy.py --manual --visible

# 3. Follow instructions in console:
#    - Manually click "Login"
#    - Manually check "I confirm"
#    - Manually click "Sign up with Google"
#    - Manually login with Google
#    - Manually handle any verification
#    - Manually click "Continue"
#    - Wait for bot to capture cookies

# 4. Check results
python main_codebuddy.py --list
```

### Expected Result

```
✓ Browser opens
✓ You navigate manually
✓ Bot detects profile page
✓ Bot captures cookies
✓ Console shows: "Cookies captured: X items"
✓ File created: cookies_codebuddy.json
✓ File created: account_codebuddy.json
```

### If Failed

**Problem:** Bot doesn't detect profile page
**Solution:** Check URL pattern, update `verify_profile_page()` function

**Problem:** No cookies captured
**Solution:** Check if you're logged in, verify cookies exist in browser

---

## 🧪 Test 2: Single Account Auto (Full Automation)

### Purpose
Verify full automation flow works end-to-end.

### Steps

```bash
# 1. Prepare account file with REAL credentials
echo "real-email@gmail.com:RealPassword123" > account.txt

# 2. Run with visible browser (to debug)
python main_codebuddy.py 1 1 --visible

# 3. Observe automation:
#    Watch console output
#    Watch browser actions
#    Note any failures

# 4. Check results
python main_codebuddy.py --list
cat cookies_codebuddy.json
cat account_codebuddy.json
```

### Expected Result

```
✓ Browser opens automatically
✓ Navigates to CodeBuddy home
✓ Clicks login button
✓ Checks "I confirm" checkbox
✓ Clicks "Sign up with Google"
✓ Handles service agreement (if appears)
✓ Types email (human-like)
✓ Types password (human-like)
✓ Handles GSuite prompt (if appears)
✓ Returns to CodeBuddy
✓ Clicks "Continue"
✓ Navigates to /profile/
✓ Captures cookies
✓ Console shows: "AKUN #1 BERHASIL!"
```

### Common Issues & Fixes

#### Issue 1: Login button not found
```python
# Edit main_codebuddy.py line ~1460
# Update login_selectors with correct selector from inspection
login_selectors = [
    'YOUR_CORRECT_SELECTOR_HERE',  # Add from inspection
    'button:has-text("Login")',
    # ...
]
```

#### Issue 2: Checkbox not found
```python
# Edit main_codebuddy.py line ~840
# Update checkbox selectors
selectors = [
    'YOUR_CORRECT_SELECTOR_HERE',
    'input[type="checkbox"]',
    # ...
]
```

#### Issue 3: Google button not found
```python
# Edit main_codebuddy.py line ~1490
google_selectors = [
    'YOUR_CORRECT_SELECTOR_HERE',
    'button:has-text("Sign up with Google")',
    # ...
]
```

#### Issue 4: Timeout / Page not loading
```python
# Increase timeout in goto_robust() call
# Edit main_codebuddy.py line ~1323
await goto_robust(page, CODEBUDDY_LANDING_URL, desc="CodeBuddy Home Page")
# or add more wait time
await asyncio.sleep(5)  # Extra wait
```

---

## 🧪 Test 3: Headless Mode

### Purpose
Verify automation works without visible browser.

### Steps

```bash
# Run in headless mode (default)
python main_codebuddy.py 1 1

# Check results
python main_codebuddy.py --list
```

### Expected Result

```
✓ No browser window opens
✓ Console shows progress
✓ Account processed successfully
✓ Cookies saved
```

---

## 🧪 Test 4: Batch Processing (2-3 Accounts)

### Purpose
Verify multi-worker parallel processing.

### Steps

```bash
# 1. Prepare multiple accounts
cat > account.txt << EOF
email1@gmail.com:password1
email2@gmail.com:password2
email3@gmail.com:password3
EOF

# 2. Run with 2 workers
python main_codebuddy.py 3 2

# 3. Observe:
#    - Workers run in parallel
#    - Batch delay between batches
#    - All accounts processed

# 4. Check results
python main_codebuddy.py --list
```

### Expected Result

```
Batch 1/2 — 2 akun...
  Worker 1: email1@gmail.com
  Worker 2: email2@gmail.com
  Batch 1/2 selesai

Menunggu 3.0s...

Batch 2/2 — 1 akun...
  Worker 1: email3@gmail.com
  Batch 2/2 selesai

RINGKASAN HASIL
Total Akun  : 3
+ Berhasil  : 3
x Gagal     : 0
Rate        : 100.0%
```

---

## 🧪 Test 5: Resume Support

### Purpose
Verify bot skips already successful accounts.

### Steps

```bash
# 1. Process accounts
python main_codebuddy.py 3 2

# 2. Run again with same accounts
python main_codebuddy.py 3 2

# Expected output:
# "3 akun sudah diproses sebelumnya"
# "3 akun dilewati (sudah sukses)"
# "Semua akun sudah diproses sebelumnya!"
```

---

## 🧪 Test 6: Error Handling

### Purpose
Verify bot handles errors gracefully.

### Test Cases

#### Test 6.1: Wrong Password
```bash
# Use wrong password
echo "test@gmail.com:WrongPassword" > account.txt
python main_codebuddy.py 1 1 --visible

# Expected: 
# - Google shows error
# - Bot logs error
# - Account marked as failed
# - Console shows "AKUN #1 GAGAL"
```

#### Test 6.2: Network Timeout
```bash
# Disconnect network during processing
# Bot should timeout gracefully
# Error logged to account_codebuddy.json
```

#### Test 6.3: Element Not Found
```bash
# If selector wrong, bot should:
# - Try fallback selectors
# - Log error if all fail
# - Mark account as failed
```

---

## 📊 Success Metrics

### Minimum Acceptable Results

- **Success Rate:** ≥ 90% for valid accounts
- **Performance:** < 60s per account
- **Error Handling:** All errors logged, no crashes
- **Resume:** Successfully skips processed accounts
- **Cookies:** Valid and usable for subsequent access

### Excellent Results

- **Success Rate:** ≥ 95%
- **Performance:** < 45s per account
- **No false failures** (due to selector issues)

---

## 📝 Testing Log Template

```markdown
## Test Log - [Date]

### Test 1: Manual Mode
- Status: [ ] Pass [ ] Fail
- Time: _____ seconds
- Issues: _____
- Notes: _____

### Test 2: Single Account Auto
- Status: [ ] Pass [ ] Fail
- Time: _____ seconds
- Issues: _____
- Selectors updated: [ ] Yes [ ] No
- Notes: _____

### Test 3: Headless Mode
- Status: [ ] Pass [ ] Fail
- Time: _____ seconds
- Issues: _____
- Notes: _____

### Test 4: Batch Processing
- Accounts tested: _____
- Success rate: _____%
- Average time: _____ seconds
- Issues: _____
- Notes: _____

### Test 5: Resume Support
- Status: [ ] Pass [ ] Fail
- Notes: _____

### Test 6: Error Handling
- Wrong password: [ ] Pass [ ] Fail
- Network timeout: [ ] Pass [ ] Fail
- Element not found: [ ] Pass [ ] Fail
- Notes: _____

### Overall Assessment
- Ready for production: [ ] Yes [ ] No
- Critical issues: _____
- Recommendations: _____
```

---

## 🚀 After Testing Complete

### If All Tests Pass

1. Update README.md with verified status
2. Commit changes with test results
3. Create release notes
4. Document any selector customizations made

### If Tests Fail

1. Document exact failure point
2. Capture screenshots/HTML at failure
3. Update selectors in code
4. Re-run tests
5. Iterate until pass

---

## 🔄 Continuous Testing

Recommend periodic testing (weekly/monthly) because:
- CodeBuddy.ai may update their UI
- Selectors may change
- New verification steps may be added

---

**Last Updated:** 2026-08-26  
**Status:** Ready for Testing  
**Next:** Run Test 1 (Manual Mode)
