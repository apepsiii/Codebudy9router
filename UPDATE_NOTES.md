# UPDATE - 2026-08-01 (20:14 UTC)

## ✅ Changes Made

### 1. Reverted Auto-Inject Changes
- `main.py` line 869: inject_to_9router() provider → "kiro" (reverted)
- `main.py` line 922: inject_from_file() provider → "kiro" (reverted)
- `main.py` line 1677: --provider default → "kiro" (reverted)

**Alasan:** 
- Inject via provider "anthropic" bukan solusi yang tepat untuk production
- 9router tidak support provider "kiro"
- **Solusi terbaik: Manual inject via dashboard 9router**

---

### 2. Updated README.md

#### Added Sections:
- ✅ Perintah-perintah yang bisa dijalankan
- ✅ Login mode dengan berbagai variasi
- ✅ Register mode dengan contoh lengkap
- ✅ Manual mode (recommended)
- ✅ List akun command
- ✅ Output files format & contoh
- ✅ Inject ke 9router (manual workflow)
- ✅ Command-line arguments lengkap
- ✅ Troubleshooting section
- ✅ Tips & best practices
- ✅ Workflow detail
- ✅ FAQ section

#### Removed/Changed:
- ❌ Auto-inject ke 9router (tidak tersedia)
- ✅ Panduan manual inject via dashboard 9router
- ✅ Catatan bahwa 9router tidak support provider "kiro"

---

## 📋 Command Reference

### Basic Commands

```bash
# Login mode (default)
python main.py                        # Semua akun, 2 workers
python main.py 10                     # 10 akun, 2 workers
python main.py 10 4                   # 10 akun, 4 workers
python main.py 10 4 --visible         # 10 akun, 4 workers, browser visible

# Register mode
python main.py 10 4 --register        # Register 10 akun baru
python main.py 10 4 --register --visible

# Manual mode (RECOMMENDED)
python main.py --manual --visible     # Semi-auto: Anda login manual
python main.py 1 1 --manual --visible

# List akun
python main.py --list                 # Lihat akun yang sudah diproses

# Custom file
python main.py 10 4 -a my_accounts.txt
python main.py 10 4 --register -a registerakun_lain.txt
```

---

## 🔧 Manual Inject ke 9Router

**Workflow:**

1. Generate tokens:
   ```bash
   python main.py 10 4
   ```

2. Tokens akan tersimpan di `kiro_tokens.txt`:
   ```
   email1@geusil.com:aorAAAAAGrkq4w...:MGQCMDt/vSRO...
   email2@geusil.com:aorAAAAAGrkrIU...:MGUCMQDgb43w...
   ```

3. Buka dashboard 9router:
   ```
   http://localhost:20128/dashboard
   ```

4. Pilih provider yang sesuai (anthropic/openai/dll)

5. Copy refresh token dari `kiro_tokens.txt`

6. Paste manual ke form 9router

7. Save connection

**Format token:**
- Token Kiro format: `part1:part2` (2 bagian dipisahkan colon)
- Kedua bagian diperlukan untuk authentication
- Copy semua karakter setelah email (termasuk colon di tengah)

---

## 📊 Output Files

### kiro_tokens.txt
```
email1@geusil.com:aorAAAAAGrkq4w...:MGQCMDt/vSRO...
email2@geusil.com:aorAAAAAGrkrIU...:MGUCMQDgb43w...
email3@geusil.com:aorAAAAAGrkrYA...:MGUCMEJKmKj...
```

### account.json
```json
{
  "email1@geusil.com": {
    "success": true,
    "refresh_token": "aorAAAAAGrkq4w...:MGQCMDt/vSRO...",
    "error": "",
    "timestamp": "2026-08-01 10:30:15"
  },
  "email2@geusil.com": {
    "success": false,
    "refresh_token": "",
    "error": "Refresh token tidak ditemukan",
    "timestamp": "2026-08-01 10:31:02"
  }
}
```

---

## ✅ Status

- **Code:** Reverted to original (provider "kiro")
- **README:** Updated dengan perintah lengkap
- **Auto-inject:** Disabled (manual only)
- **Documentation:** Complete

---

## 🎯 Next Steps for Users

1. **Generate tokens:**
   ```bash
   python main.py 10 4
   ```

2. **Check output:**
   ```bash
   type kiro_tokens.txt
   # atau
   python main.py --list
   ```

3. **Manual inject ke 9router via dashboard**

4. **Verify tokens working di 9router**

---

## 📝 Notes

- Auto-inject feature removed karena 9router compatibility issue
- Manual inject via dashboard adalah solusi yang paling reliable
- Token format Kiro: `part1:part2` (2 bagian)
- Semua perintah sudah didokumentasikan di README.md

---

**Updated:** 2026-08-01 20:14 UTC  
**Status:** ✅ Complete  
**Action Required:** None (users can use manual inject workflow)
