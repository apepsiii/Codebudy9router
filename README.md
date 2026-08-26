# V2Fun.ai API Automation

> Web automation dan API exploration tool untuk V2Fun.ai - AI 3D Model Generator

**Repository:** https://github.com/apepsiii/Codebudy9router

---

## 📁 Project Structure

```
Codebudy9router/
├── v2fun_scripts/          # Scripts untuk exploration & automation
│   ├── capture_v2fun_api.py         # Network capture tool
│   ├── capture_v2fun_simple.py      # Simplified capture
│   ├── explore_v2fun.py             # API testing script
│   ├── explore_v2fun_v2.py          # Token-based testing
│   ├── v2fun_interactive_discovery.py  # Interactive discovery
│   └── run_v2fun_discovery.bat      # Windows launcher
│
├── v2fun_data/             # Data capture & documentation
│   ├── v2fun_capture_*.json         # Network captures (4 files)
│   ├── v2fun_endpoints.txt          # Discovered endpoints
│   ├── V2FUN_API_DISCOVERY.md       # API findings
│   ├── V2FUN_DISCOVERY_HOWTO.md     # Discovery instructions
│   └── V2FUN_MANUAL_GUIDE.md        # Manual inspection guide
│
├── archive/                # Old projects (archived)
│   ├── codebuddy/          # CodeBuddy automation (80% complete)
│   └── kiro/               # Kiro token generator (production-ready)
│
├── requirements.txt        # Python dependencies
├── requirements-web.txt    # Web dashboard dependencies
└── README.md              # This file
```

---

## 🎯 Current Status

**Project:** V2Fun.ai API Exploration  
**Status:** 🔄 In Progress (20% complete)  
**Phase:** Discovery & API mapping  
**Last Updated:** 2026-08-26

### What's Done
- ✅ Network capture tools created (5 scripts)
- ✅ Initial API endpoint discovery
- ✅ Documentation framework ready
- ✅ Project structure reorganized

### What's Next
- ⏳ Deep API endpoint analysis
- ⏳ Authentication flow mapping
- ⏳ API automation implementation
- ⏳ Cookie/token management

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Required packages:**
- `playwright` - Browser automation
- `playwright-stealth` - Anti-detection
- `rich` - Beautiful CLI output

### 2. Install Browser

```bash
playwright install chromium
```

### 3. Run Network Capture

```bash
# Interactive discovery mode
python v2fun_scripts/v2fun_interactive_discovery.py

# Simple capture mode
python v2fun_scripts/capture_v2fun_simple.py

# Windows batch launcher
v2fun_scripts/run_v2fun_discovery.bat
```

---

## 🔍 Discovered API Endpoints

Based on network capture analysis:

### Base API URL
```
https://api.prod.v2fun.ai/
```

### Endpoints Found

1. **Article Slot (Landing Page Content)**
   ```
   GET /article/slot/get-by-entrance-code?lan=en
   ```
   - Purpose: Get landing page content slots
   - Method: GET
   - Language parameter: `lan=en`

2. **Internationalization**
   ```
   GET https://v2fun.ai/api/i18n/messages/en
   ```
   - Purpose: Get translation messages
   - Language: English (en)

### Statistics
- **Total API requests captured:** 91
- **Total responses received:** 72
- **Unique endpoints found:** 1 (API endpoint)
- **Framework detected:** Nuxt.js (SSR)

---

## 📊 Network Analysis

### Request Headers Pattern
```javascript
{
  "sec-ch-ua-platform": "Windows",
  "referer": "https://v2fun.ai/",
  "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
  "sec-ch-ua": "Chromium;v=151, Not=A?Brand;v=99",
  "sec-ch-ua-mobile": "?0"
}
```

### Technologies Detected
- **Frontend:** Nuxt.js (Vue.js SSR framework)
- **Assets:** `/_nuxt/` path structure
- **CDN:** Own domain hosting
- **Analytics:** Google Analytics + Google Ads tracking

---

## 📝 Documentation

Detailed documentation available in `v2fun_data/`:

- **V2FUN_API_DISCOVERY.md** - API findings and analysis
- **V2FUN_DISCOVERY_HOWTO.md** - Step-by-step discovery guide
- **V2FUN_MANUAL_GUIDE.md** - Manual inspection instructions

---

## 🔧 Available Tools

### 1. Interactive Discovery
```bash
python v2fun_scripts/v2fun_interactive_discovery.py
```
Interactive tool untuk explore API endpoints dengan menu.

### 2. Capture API Calls
```bash
python v2fun_scripts/capture_v2fun_api.py
```
Capture semua network requests ke file JSON.

### 3. Simple Capture
```bash
python v2fun_scripts/capture_v2fun_simple.py
```
Simplified version untuk quick capture.

### 4. Explore API
```bash
python v2fun_scripts/explore_v2fun.py
```
Test discovered API endpoints.

---

## 🎓 Learning & Insights

### Challenges
- ⚠️ Limited API endpoint visibility (Nuxt.js SSR)
- ⚠️ Need to trigger user actions for more endpoints
- ⚠️ Authentication flow not yet discovered

### Recommendations
- 💡 Manual browser inspection needed for full flow
- 💡 Login/signup flow analysis required
- 💡 Check browser DevTools Network tab for XHR requests
- 💡 Test API endpoints with different parameters

---

## 📦 Archived Projects

Old projects moved to `archive/` folder:

### CodeBuddy Automation Bot
- **Status:** 80% complete, ready for testing
- **Purpose:** Automated login/registration to CodeBuddy.ai
- **Location:** `archive/codebuddy/`

### Kiro Token Generator
- **Status:** Production-ready
- **Purpose:** Generate tokens for Kiro.dev via Google OAuth
- **Location:** `archive/kiro/`

---

## 🤝 Contributing

This is a personal learning project for API exploration and automation.

---

## ⚠️ Disclaimer

This tool is for educational purposes only. Always respect website Terms of Service and rate limits.

---

## 📞 Support

For questions or issues, create an issue on GitHub:  
https://github.com/apepsiii/Codebudy9router/issues

---

**Last Updated:** 2026-08-26  
**Version:** 0.2.0 (V2Fun Focus)  
**Author:** apepsiii
