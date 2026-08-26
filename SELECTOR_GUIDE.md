# CodeBuddy Selector Inspection Guide

> Manual guide untuk inspect selectors di CodeBuddy.ai dan update main_codebuddy.py

---

## 🎯 Objective

Mendapatkan **correct selectors** untuk setiap step di CodeBuddy automation flow.

---

## 📋 Steps to Inspect

### 1. Open CodeBuddy.ai

```bash
# Option 1: Use Playwright codegen (recommended)
playwright codegen https://www.codebuddy.ai/home

# Option 2: Use browser manually
# Open Chrome/Edge and navigate to https://www.codebuddy.ai/home
```

---

### 2. Inspect Each Element

Press `F12` to open DevTools, then use Element Picker (Ctrl+Shift+C)

#### **Step 1: Login Button**

**Location:** Home page (`/home`)

**Find:**
- Button or link with text "Login" or "Sign in"

**Inspect:**
1. Right-click element → Inspect
2. Note down:
   - Tag name (button/a/div)
   - ID attribute
   - Class names
   - data-testid attribute
   - href attribute (if link)
   - Text content

**Example selectors to try:**
```javascript
button:has-text("Login")
a:has-text("Login")
[data-testid="login-button"]
a[href*="/login"]
.login-btn
#login-button
```

**Record here:**
```
✓ Working selector: _______________________
  Tag: _______
  Classes: _______
  ID: _______
  data-testid: _______
```

---

#### **Step 2: "I confirm" Checkbox**

**Location:** Login/Signup page

**Find:**
- Checkbox near text "I confirm that..."

**Inspect:**
```javascript
input[type="checkbox"]
input[name="confirm"]
[data-testid="confirm-checkbox"]
.agreement-checkbox
```

**Record here:**
```
✓ Working selector: _______________________
  Label text: _______
  Required: Yes/No
```

---

#### **Step 3: "Sign up with Google" Button**

**Location:** Login/Signup page (after checking "I confirm")

**Find:**
- Button with Google logo or text "Sign up with Google"

**Inspect:**
```javascript
button:has-text("Sign up with Google")
button:has-text("Continue with Google")
[data-testid="google-signup"]
.google-login-btn
button[aria-label*="Google"]
```

**Record here:**
```
✓ Working selector: _______________________
  Exact text: _______
  Has icon: Yes/No
```

---

#### **Step 4: Service Agreement Dialog**

**Location:** After clicking Google button (may not always appear)

**Find:**
- Modal/dialog with terms and conditions
- Button with text "Confirm" or "Accept"

**Inspect:**
```javascript
// Dialog container
.modal
.dialog
[role="dialog"]
.agreement-dialog

// Confirm button
button:has-text("Confirm")
button:has-text("Accept")
[data-testid="agreement-confirm"]
```

**Record here:**
```
✓ Dialog appears: Yes/No
✓ Dialog selector: _______________________
✓ Confirm button: _______________________
```

---

#### **Step 5: Return from Google ("Continue" button)**

**Location:** After Google OAuth, back at CodeBuddy

**Find:**
- Button with text "Continue" or "Lanjutkan"

**Inspect:**
```javascript
button:has-text("Continue")
button:has-text("Lanjutkan")
[data-testid="continue-button"]
.continue-btn
```

**Record here:**
```
✓ Working selector: _______________________
  Text: _______
```

---

#### **Step 6: Profile Page**

**Location:** `https://www.codebuddy.ai/profile/`

**Find:**
- Any element that confirms profile page loaded
- Could be: page title, profile container, user info

**Inspect:**
```javascript
.profile-container
[data-testid="profile-page"]
.user-profile
h1:has-text("Profile")
.profile-header
```

**Record here:**
```
✓ Working selector: _______________________
  URL pattern: _______
```

---

## 🔧 How to Update main_codebuddy.py

### Location of Selectors in Code

```python
# File: main_codebuddy.py

# Line ~1460: Login button
login_selectors = [
    'button:has-text("Login")',  # ← UPDATE HERE
    'a:has-text("Login")',
    # ...
]

# Line ~840: I confirm checkbox
async def handle_confirm_checkbox(page, timeout=15):
    selectors = [
        'input[type="checkbox"]',  # ← UPDATE HERE
        # ...
    ]

# Line ~1490: Google signup button
google_selectors = [
    'button:has-text("Sign up with Google")',  # ← UPDATE HERE
    # ...
]

# Line ~890: Service agreement
async def handle_service_agreement(page, timeout=30):
    confirm_selectors = [
        'button:has-text("Confirm")',  # ← UPDATE HERE
        # ...
    ]

# Line ~970: Continue button
async def handle_codebuddy_return(page, timeout=60):
    continue_selectors = [
        'button:has-text("Continue")',  # ← UPDATE HERE
        # ...
    ]

# Line ~220: Profile page verification
async def verify_profile_page(page) -> bool:
    selectors = [
        '.profile-container',  # ← UPDATE HERE
        # ...
    ]
```

---

## 📝 Testing Workflow

### 1. Manual Test First

```bash
# Test dengan visible browser dan manual mode
python main_codebuddy.py --manual --visible

# Anda login manual, bot observe saja
# Note down setiap step yang berhasil/gagal
```

### 2. Update Selectors

Edit `main_codebuddy.py` dengan selector yang correct dari inspection.

### 3. Test Semi-Auto

```bash
# Test 1 akun dengan visible mode
python main_codebuddy.py 1 1 --visible

# Observe apakah bot bisa click element dengan benar
```

### 4. Test Full Auto

```bash
# Test 1 akun headless
python main_codebuddy.py 1 1

# Check hasil di account_codebuddy.json
python main_codebuddy.py --list
```

---

## ✅ Checklist

- [ ] Inspect login button selector
- [ ] Inspect "I confirm" checkbox selector
- [ ] Inspect "Sign up with Google" button selector
- [ ] Check if Service Agreement dialog appears
- [ ] Inspect Service Agreement confirm button (if exists)
- [ ] Inspect "Continue" button after Google OAuth
- [ ] Inspect profile page verification element
- [ ] Update all selectors in main_codebuddy.py
- [ ] Test with --manual --visible
- [ ] Test with 1 account automatic
- [ ] Test with 2-3 accounts batch

---

## 🐛 Common Issues

### Issue 1: Element not found
**Solution:** Element might be in iframe or shadow DOM. Check:
```javascript
// In DevTools console
document.querySelectorAll('iframe')  // Check iframes
$0.shadowRoot  // Check shadow DOM (select element first)
```

### Issue 2: Element not clickable
**Solution:** Element might be covered or need scroll.
```python
# In code, add:
await page.locator(selector).scroll_into_view_if_needed()
await asyncio.sleep(0.5)
await page.locator(selector).click()
```

### Issue 3: Timing issues
**Solution:** Add more wait time.
```python
await page.wait_for_selector(selector, timeout=15000)
await asyncio.sleep(1)  # Extra wait
```

---

## 📞 Support

Jika selector inspection gagal atau flow berbeda:

1. Capture screenshot di setiap step
2. Save HTML source: `await page.content()`
3. Update documentation dengan actual flow
4. Adjust code accordingly

---

**Last Updated:** 2026-08-26
**Status:** Awaiting Manual Inspection
