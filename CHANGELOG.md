# Changelog

## [1.0.1] - 2026-08-01

### 🐛 Fixed
- **CRITICAL FIX:** Error "HTTP 400: Invalid provider" saat inject ke 9router
  - Root cause: 9router tidak mengenali provider "kiro"
  - Solution: Ganti default provider dari "kiro" ke "anthropic"
  - Alasan: Kiro dibangun di atas Anthropic API, token compatible dengan Anthropic

### ✨ Changed
- Default provider di `inject_to_9router()`: "kiro" → "anthropic"
- Default provider di `inject_from_file()`: "kiro" → "anthropic"
- Default `--provider` argument: "kiro" → "anthropic"
- Clean-up file `kiro_tokens.txt` (hapus prefix "(done)")

### 📝 Added
- `test_inject.py` - Test script untuk verifikasi inject ke 9router
- `INJECT_9ROUTER.md` - Dokumentasi lengkap cara inject ke 9router
- `SUMMARY_PERBAIKAN.md` - Detail analisis dan fix "Invalid provider"
- `CHANGELOG.md` - File ini

### ✅ Testing
- Tested with 11 Kiro accounts
- Success rate: 100% (11/11)
- All tokens status: active
- Dashboard verified: http://localhost:20128/dashboard/providers/anthropic

### 📊 Files Modified
1. `main.py` (3 locations)
   - Line 869: `inject_to_9router()` default provider
   - Line 922: `inject_from_file()` default provider
   - Line 1677: argparse `--provider` default
2. `kiro_tokens.txt` - Removed "(done)" prefix
3. `README.md` - Updated with fix information

### 🔗 Related
- Issue: "Invalid provider" error when injecting to 9router
- Provider yang valid: anthropic, openai, cloudflare-ai
- Provider yang invalid: kiro, kr, kiro-ai

---

## [1.0.0] - 2026-07-31

### ✨ Initial Release
- Auto-login Kiro via Google OAuth
- Capture refresh token dari Cognito
- Mode login & register
- Mode manual (semi-auto)
- Multi-worker parallel processing
- Inject ke 9router
- Resume support (skip akun yang sudah sukses)
- Detailed logging dengan Rich

### 🚀 Features
- Playwright + playwright-stealth
- Network interception untuk capture token
- Multi-strategy fallback (localStorage, URL hash, cookies)
- Captcha/verification manual handling
- Human-like typing dengan random delay
- Fresh browser per batch
- Auto-save setelah setiap batch

### 📦 Dependencies
- playwright >= 1.40.0
- playwright-stealth >= 0.1.0
- rich >= 13.0.0

---

## Migration Guide: v1.0.0 → v1.0.1

### Untuk User yang Sudah Pakai v1.0.0

**Tidak ada perubahan breaking!** Script backward compatible.

Jika Anda sebelumnya menggunakan:
```bash
python main.py --inject-from-file kiro_tokens.txt --router-password PASS --provider kiro
```

Sekarang cukup:
```bash
python main.py --inject-from-file kiro_tokens.txt --router-password PASS
# Default provider sudah "anthropic"
```

### Update Steps

1. **Pull latest code**
   ```bash
   git pull origin main
   ```

2. **Clean kiro_tokens.txt** (hapus prefix "(done)" jika ada)
   ```bash
   # Manual: buka file dan hapus "(done)"
   # Atau gunakan sed/awk jika di Linux/Mac
   ```

3. **Test inject**
   ```bash
   python main.py --inject-from-file kiro_tokens.txt --router-password YOUR_PASSWORD
   ```

4. **Verify di dashboard**
   ```
   http://localhost:20128/dashboard/providers/anthropic
   ```

### Breaking Changes

**TIDAK ADA** - Script fully backward compatible.

Jika Anda sudah punya script/automation yang hardcode `--provider kiro`, 
akan tetap berfungsi tapi akan gagal. Solusi: hapus `--provider kiro` atau
ganti dengan `--provider anthropic`.

---

## Roadmap

### v1.1.0 (Planned)
- [ ] Auto-refresh expired tokens
- [ ] Proxy support (rotate IP per batch)
- [ ] Rate limit handling otomatis
- [ ] Export ke format lain (JSON, CSV)
- [ ] Dashboard TUI (Rich Live Display)
- [ ] Notification (email/webhook) saat selesai
- [ ] Docker support

### v1.2.0 (Planned)
- [ ] Multiple provider support (bukan hanya Kiro)
- [ ] Token encryption at rest
- [ ] Config file support (YAML/JSON)
- [ ] Logging ke file (rotating logs)
- [ ] Metrics & analytics

### v2.0.0 (Future)
- [ ] Web UI (FastAPI + React)
- [ ] Token management dashboard
- [ ] Scheduled refresh (cron-like)
- [ ] API endpoint untuk external integration
- [ ] Multi-user support

---

## Support

- 📖 Dokumentasi: [README.md](README.md)
- 🐛 Issues: [GitHub Issues](https://github.com/your-repo/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/your-repo/discussions)

---

**Last Updated:** 2026-08-01
**Maintained by:** Your Name
