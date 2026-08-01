# Kiro Refresh Token Bot v1.0

Bot otomatis untuk mendapatkan refresh token dari Kiro.dev menggunakan Playwright + Stealth.

---

## 🚀 Features

- ✅ Login/Register Kiro via Google OAuth otomatis
- ✅ Capture refresh token dari Cognito
- ✅ Support multiple workers (parallel processing)
- ✅ Mode manual (Anda login manual, bot capture token)
- ✅ Resume support (skip akun yang sudah berhasil)
- ✅ Detailed logging & progress tracking
- ✅ Output ke `kiro_tokens.txt` dan `account.json`

---

## 📋 Requirements

```bash
pip install playwright playwright-stealth rich
playwright install chromium
```

---

## 📁 File Structure

```
KiroApiKey/
├── main.py                  # Script utama
├── account.txt              # Input: email:password (login mode)
├── registerakun.txt         # Input: email:password (register mode)
├── kiro_tokens.txt          # Output: email:refresh_token
├── account.json             # Log semua akun & status
└── README.md                # File ini
```

---

## 🎯 Perintah-Perintah yang Bisa Dijalankan

### 1. Login Mode (Akun Kiro yang Sudah Ada)

```bash
# Proses semua akun di account.txt dengan 2 workers
python main.py

# Proses 10 akun pertama dengan 2 workers
python main.py 10

# Proses 10 akun dengan 4 workers
python main.py 10 4

# Dengan browser visible (untuk debugging)
python main.py 10 4 --visible

# Custom file akun
python main.py 10 4 -a my_accounts.txt
```

**Format `account.txt`:**
```
email1@gmail.com:password123
email2@gmail.com:password456
```

---

### 2. Register Mode (Buat Akun Kiro Baru)

```bash
# Register 10 akun baru dengan 4 workers
python main.py 10 4 --register

# Register dengan browser visible
python main.py 10 2 --register --visible

# Custom file akun
python main.py 10 4 --register -a registerakun_lain.txt
```

**Format `registerakun.txt`:**
```
newemail1@gmail.com:password123
newemail2@gmail.com:password456
```

---

### 3. Manual Mode (⭐ RECOMMENDED)

Mode semi-auto: **Anda login manual**, bot capture token otomatis.

```bash
# Mode manual - bot buka browser, Anda login manual
python main.py 1 1 --manual --visible

# Atau tanpa specify jumlah (akan ambil 1 akun dari account.txt)
python main.py --manual --visible
```

**Keuntungan Mode Manual:**
- ✅ Tidak ada Google detection
- ✅ Handle captcha manual (lebih mudah)
- ✅ Handle verification manual (nomor HP, 2FA, dll)
- ✅ Success rate 100% (jika login manual berhasil)
- ✅ Timeout 5 menit (cukup untuk solve captcha/verification)

---

### 4. List Akun yang Sudah Diproses

```bash
python main.py --list
```

Output:
```
════════════════════════════════════════════════════════════
DAFTAR AKUN KIRO
════════════════════════════════════════════════════════════

>  Total akun : 11
+  Berhasil   : 11
x  Gagal      : 0

# │ Email                    │ Status  │ Refresh Token  │ Timestamp
──┼──────────────────────────┼─────────┼────────────────┼──────────────────
1 │ email1@gmail.com         │ SUCCESS │ ...Ckc0        │ 2026-08-01 10:30
2 │ email2@gmail.com         │ SUCCESS │ ...Abc0        │ 2026-08-01 10:35
```

---

## 📊 Output Files

### `kiro_tokens.txt`

Format: `email:refresh_token_part1:refresh_token_part2`

```
email1@geusil.com:aorAAAAAGrkq4w...:MGQCMDt/vSRO...
email2@geusil.com:aorAAAAAGrkrIU...:MGUCMQDgb43w...
```

**⚠️ PENTING:** Format token Kiro terdiri dari 3 bagian yang dipisahkan `:` (colon)

---

### `account.json`

Log structured semua akun:

```json
{
  "email1@gmail.com": {
    "success": true,
    "refresh_token": "aorAAAAAGrkq4w...:MGQCMDt/vSRO...",
    "error": "",
    "timestamp": "2026-08-01 10:30:15"
  }
}
```

---

## 🔧 Inject ke 9Router (Manual)

**⚠️ CATATAN:** Fitur auto-inject ke 9router saat ini **TIDAK TERSEDIA** karena 9router tidak support provider "kiro".

**Cara manual inject ke 9router:**

1. **Buka dashboard 9router:**
   ```
   http://localhost:20128/dashboard
   ```

2. **Pilih provider yang sesuai** (misalnya: anthropic, openai, dll)

3. **Copy refresh token dari `kiro_tokens.txt`**

4. **Paste manual ke form 9router**

5. **Save connection**

**Format refresh token Kiro:**
```
aorAAAAAGrkq4w...:MGQCMDt/vSRO...
```
(Kedua bagian setelah email dipisahkan dengan `:`)

---

## ⚙️ Command-line Arguments

```
python main.py [jumlah] [workers] [options]

Positional:
  jumlah              Jumlah akun yang diproses (default: all)
  workers             Jumlah worker paralel (default: 2)

Options:
  -a, --accounts      Path file akun (default: account.txt)
  -o, --output        Path file output (default: kiro_tokens.txt)
  -d, --delay         Delay antar batch dalam detik (default: 3)
  --visible           Tampilkan browser (default: headless)
  --register          Mode registrasi: sign-up akun Kiro baru
  --manual            Mode semi-auto: Anda login manual, bot capture token
  --list              List akun dari account.json
  --chrome            Gunakan system Chrome (lebih natural)
```

---

## 🐛 Troubleshooting

### Error: Google Detection "unusual traffic"

**Solusi:**
1. **Gunakan mode manual** (RECOMMENDED):
   ```bash
   python main.py --manual --visible
   ```
2. Kurangi jumlah workers (max 1-2)
3. Tambah delay: `--delay 10`
4. Proses max 5-10 akun per run

---

### Error: Halaman Blank

**Solusi:**
1. Gunakan `--visible` untuk debug
2. Gunakan mode manual
3. Install Chrome di system
4. Clear browser data

---

### Error: Captcha/Turnstile

**Solusi:**
1. Gunakan mode manual dan solve manual
2. Script akan pause 180 detik untuk solve manual
3. Kurangi workers

---

### Error: Phone Verification

**Solusi:**
1. Gunakan mode manual
2. Script akan pause 180 detik untuk input manual
3. Gunakan akun Google yang sudah verified

---

### Error: Refresh Token Tidak Ditemukan

**Solusi:**
1. Gunakan `--visible` untuk debug
2. Pastikan redirect ke app.kiro.dev berhasil
3. Cek network tab untuk `/oauth2/token` response
4. Gunakan mode manual

---

## 💡 Tips & Best Practices

1. **Start small:** Test dengan 1-2 akun dulu
2. **Use manual mode:** Untuk akun penting atau saat auto mode gagal
3. **Monitor rate limits:** Tambah delay jika rate limited
4. **Resume support:** Script auto-skip akun yang sudah sukses
5. **System Chrome:** Lebih natural daripada Playwright Chromium
6. **Visible mode:** Gunakan untuk debugging
7. **Batch kecil:** Max 5-10 akun per run untuk avoid detection

---

## 📝 Workflow

### Login/Register Flow

1. Navigasi ke `https://kiro.dev/` (Landing Page)
2. Klik "Sign in" di landing page
3. Redirect ke `app.kiro.dev/signin`
4. Klik "Continue with Google"
5. Login Google (email → password)
6. Handle consent page ("Allow")
7. Redirect ke `app.kiro.dev`
8. Capture refresh token via network interception
9. Save ke `kiro_tokens.txt` dan `account.json`

---

### Token Capture Strategy

Bot menggunakan multi-strategy:

1. **Network Interception** (Primary) - Monitor `/oauth2/token` endpoint
2. **localStorage** (Fallback #1) - Polling setiap 2 detik
3. **URL Hash** (Fallback #2) - Parse URL fragment
4. **Cookies** (Fallback #3) - Scan cookies

---

## 📚 Documentation

- **README.md** - File ini (dokumentasi utama)
- **account.json** - Log semua akun yang sudah diproses
- **kiro_tokens.txt** - Output refresh tokens

---

## ❓ FAQ

**Q: Kenapa tidak bisa auto-inject ke 9router?**
A: 9router tidak support provider "kiro". Inject manual saja via dashboard 9router dengan pilih provider yang sesuai (anthropic/openai/dll).

**Q: Format refresh token Kiro seperti apa?**
A: Format: `part1:part2` (dipisahkan dengan colon). Kedua bagian diperlukan untuk authentication.

**Q: Apakah token akan expired?**
A: Ya, refresh token bisa expired. Monitor status di aplikasi yang menggunakan token.

**Q: Berapa success rate mode auto vs manual?**
A: Mode auto: 60-80% (tergantung detection). Mode manual: 100% (jika login berhasil).

**Q: Bisa inject ke multiple 9router?**
A: Tidak support auto-inject. Lakukan manual untuk setiap instance 9router.

---

## 🔐 Security Notes

1. **Jangan commit tokens:** Add ke `.gitignore`
   ```
   kiro_tokens.txt
   account.txt
   registerakun.txt
   account.json
   ```

2. **Password:** Jangan hardcode di script

3. **Google credentials:** Gunakan akun test, bukan production

4. **Rate limiting:** Gunakan delay yang wajar

---

## 📞 Support

Jika ada pertanyaan atau issue:
1. Cek troubleshooting section di atas
2. Gunakan `--visible` untuk debugging
3. Gunakan mode manual jika auto mode gagal
4. Buat issue di repository

---

## 📄 License

MIT License - Use at your own risk

---

**Happy Automating! 🚀**

**Version:** 1.0.0  
**Last Updated:** 2026-08-01
