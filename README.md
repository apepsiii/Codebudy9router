# Kiro API Key Bot v1.0

Bot otomatis untuk membuat Kiro refresh token massal menggunakan Playwright + playwright-stealth.

## Fitur

- Auto-login Google → Kiro → capture refresh token
- **Mode registrasi: sign-up akun Kiro baru via Google** (`--register`)
- Bypass Cloudflare Turnstile/captcha dengan stealth mode
- Multi-worker paralel (configurable)
- Headless mode (default) atau visible browser
- Log akun sudah diproses (skip re-run)
- Inject akun ke 9router setelah refresh token berhasil

## Install

```bash
pip install -r requirements.txt
playwright install chromium
```

**requirements.txt:**
```
playwright
playwright-stealth
rich
```

## Persiapan

### 1. Buat `account.txt` (mode login) atau `registerakun.txt` (mode register)

Format: `email:password` (satu akun per baris)

```
akun1@gmail.com:password123
akun2@gmail.com:password456
akun3@gmail.com:password789
```

> **Mode login** (`account.txt`): akun harus sudah terdaftar di Kiro dan bisa login via Google.
> **Mode register** (`registerakun.txt`): akun Google bisa baru (belum terdaftar di Kiro).

File terpisah untuk memudahkan:
| File | Mode | Digunakan saat |
|------|------|----------------|
| `account.txt` | Login | `python main.py` (default) |
| `registerakun.txt` | Register | `python main.py --register` |

> Gunakan flag `-a` untuk override file akun manual, contoh: `python main.py --register -a akun_lain.txt`

### 2. (Opsional) Siapkan 9router

Pastikan 9router server berjalan di `http://localhost:20128` jika ingin inject otomatis.

## Cara Pakai

### Dasar

```bash
# Proses semua akun, 2 workers, headless
python main.py

# Proses 10 akun pertama
python main.py 10

# Proses 10 akun dengan 4 workers
python main.py 10 4
```

### Mode Semi-Auto (Manual Login) ⭐ RECOMMENDED

Mode semi-auto: **Anda login manual**, bot otomatis capture token. Paling reliable untuk menghindari detection!

```bash
# Mode manual - bot buka browser, Anda login manual
python main.py 1 1 --manual --visible

# Atau tanpa specify jumlah (akan ambil 1 akun dari account.txt)
python main.py --manual --visible
```

**Flow Mode Manual:**
1. Bot buka browser dan navigasi ke kiro.dev
2. **Anda klik Sign in dan login Google manual**
3. **Anda handle captcha/verification sendiri**
4. **Anda klik Allow/Izinkan untuk consent**
5. Tunggu redirect ke app.kiro.dev
6. **Bot otomatis capture refresh token** 🎉
7. Selesai!

**Keuntungan Mode Manual:**
- ✅ **Tidak ada Google detection** (Anda login seperti user biasa)
- ✅ **Handle captcha manual** (lebih mudah)
- ✅ **Handle verification manual** (nomor HP, 2FA, dll)
- ✅ **Success rate 100%** (jika login manual berhasil)
- ✅ **Timeout 5 menit** (cukup untuk solve captcha/verification)

> **Rekomendasi:** Gunakan mode manual untuk akun-akun penting atau saat auto mode gagal!

### Semua Argumen

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
  --register          Mode registrasi: sign-up akun Kiro baru via Google
  --manual            Mode semi-auto: Anda login manual, bot capture token (RECOMMENDED)
  --list              List akun dari account.json
  --inject-9router    Inject akun ke 9router setelah refresh token berhasil
  --inject-from-file  Inject dari file kiro_tokens.txt ke 9router
  --router-url        URL 9router (default: http://localhost:20128)
  --router-password   Password 9router (opsional, auto-login)
  --provider          Provider name untuk 9router (default: kiro)
```

### Contoh Lengkap

```bash
# 10 akun, 4 workers, visible browser
python main.py 10 4 --visible

# Semua akun, 4 workers, inject ke 9router
python main.py all 4 --inject-9router --router-password MyPassword123

# 5 akun, 2 workers, file akun custom
python main.py 5 2 -a my_accounts.txt

# 20 akun, 6 workers, output custom, inject ke 9router remote
python main.py 20 6 -o hasil.txt --inject-9router --router-url http://192.168.1.100:20128

# Inject dari file ke 9router (tanpa buat refresh token baru)
python main.py --inject-from-file kiro_tokens.txt --router-password MyPassword123

# List akun yang sudah diproses
python main.py --list
```

### Mode Registrasi

Mode `--register` untuk membuat akun Kiro **baru** via Google sign-up (bukan login akun yang sudah ada).

File akun default: `registerakun.txt` (bukan `account.txt`).

```bash
# Registrasi 10 akun baru, 4 workers, headless (baca dari registerakun.txt)
python main.py 10 4 --register

# Registrasi dengan browser visible (debug)
python main.py 10 2 --register --visible

# Registrasi + inject ke 9router
python main.py all 4 --register --inject-9router --router-password MyPassword123

# Override file akun manual
python main.py 10 4 --register -a akun_register_lain.txt
```

**Flow Login/Register Kiro:**

1. **Navigasi ke Kiro Landing Page**
   - Bot membuka `https://kiro.dev/` (halaman utama)
   - Delay 2-4 detik (seperti user membaca halaman)
   - **Lebih natural daripada direct access ke signin URL**

2. **Klik "Sign in" di Landing Page**
   - Bot mencari dan klik tombol "Sign in" di halaman utama
   - Redirect ke `app.kiro.dev/signin`
   - Jika tombol tidak ditemukan, fallback ke direct access

3. **Klik Google Button**
   - Bot otomatis mencari dan klik tombol "Continue with Google" atau "Sign in with Google"
   - Redirect ke Google OAuth

4. **Login Google**
   - Input email Google (char-by-char, delay 50-100ms per char)
   - Klik "Next"
   - Input password (char-by-char, delay 40-100ms per char)
   - Klik "Next"
   - Handle "I understand" + "Continue" jika ada (akun GSuite baru)

5. **Consent Page (Google → Cognito)**
   - Jika diminta izin: "Google will allow kiro-prod-us-east-1.auth.us-east-1.amazoncognito.com to access this info about you"
   - Bot otomatis klik **"Allow"** atau **"Continue"**
   - Ini adalah consent untuk Cognito OAuth

6. **Redirect ke Kiro App**
   - Setelah consent, redirect ke `app.kiro.dev`
   - Akun baru otomatis dibuat (register mode)
   - Atau login berhasil (login mode)

7. **Capture Refresh Token**
   - Bot monitor network untuk `/oauth2/token` response (primary method)
   - Fallback: localStorage, URL hash, cookies
   - Jika sukses, refresh token disimpan ke `kiro_tokens.txt` dan `account.json`

> **Catatan Penting:**
> - **Flow lebih natural**: akses landing page dulu → klik Sign in (seperti user normal)
> - **Human-like typing**: char-by-char dengan random delay per character
> - **Random delays**: 2-4.5 detik antar action untuk menghindari bot detection
> - Akun Google baru kadang diminta **verifikasi nomor HP** saat OAuth pertama
> - Script akan **pause dan menunggu** solve manual (timeout 180s)
> - **Captcha/Turnstile**: jika muncul, solve manual di browser, script otomatis lanjut
> - Refresh token format: JWT dari AWS Cognito (~1000+ characters)

**Error handling:**
- Akun **berhasil** → dicatat di `account.json` dengan `success: true` (skip saat re-run)
- Akun **gagal** → dicatat di `account.json` dengan `success: false` + error message (bisa diproses ulang)

## Output

### `kiro_tokens.txt`

Format: `email:refresh_token` (satu per baris)

```
akun1@gmail.com:eyJraWQiOiJXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
akun2@gmail.com:eyJraWQiOiJXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

### `account.json`

Log semua akun yang sudah diproses. Format:

```json
{
  "user@gmail.com": {
    "success": true,
    "refresh_token": "eyJraWQiOiJXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "error": "",
    "timestamp": "2026-07-31 10:30:45"
  },
  "user2@gmail.com": {
    "success": false,
    "refresh_token": "",
    "error": "Refresh token tidak ditemukan",
    "timestamp": "2026-07-31 10:31:02"
  }
}
```

> Akun yang sudah sukses di `account.json` akan dilewati saat re-run.

## Inject ke 9router

Setelah refresh token berhasil dibuat, bot bisa langsung inject ke 9router.

### Cara Kerja

1. Login ke 9router (`POST /api/auth/login`) → dapat `auth_token`
2. POST ke `/api/providers` dengan data:
   ```json
   {
     "provider": "kiro",
     "apiKey": "eyJraWQiOiJXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
     "name": "user@gmail.com",
     "priority": 1,
     "testStatus": "active",
     "providerSpecificData": {}
   }
   ```

### Contoh

```bash
# Inject dengan auto-login
python main.py 10 4 --inject-9router --router-password MyPassword123

# Inject tanpa password (jika 9router tidak pakai auth)
python main.py 10 4 --inject-9router

# Inject ke 9router remote
python main.py 10 4 --inject-9router --router-url http://192.168.1.100:20128 --router-password pass123

# Custom provider name
python main.py 10 4 --inject-9router --router-password pass123 --provider kiro-ai
```

### Output di Terminal

```
>  Batch 1/5 — Memproses 2 akun...
+  Refresh token captured (...12345678)
+  Injected ke 9router: user1@gmail.com
+  Refresh token captured (...87654321)
+  Injected ke 9router: user2@gmail.com
>  Batch 1/5 selesai
```

### Inject dari File

Jika sudah punya `kiro_tokens.txt` dan ingin inject ke 9router tanpa buat refresh token baru:

```bash
python main.py --inject-from-file kiro_tokens.txt --router-password MyPassword123
```

**Multi-Worker Inject:**

Gunakan argumen pertama untuk mengatur jumlah worker paralel:

```bash
# 4 workers paralel untuk inject
python main.py --inject-from-file kiro_tokens.txt 4 --router-password MyPassword123

# 8 workers untuk inject cepat
python main.py --inject-from-file kiro_tokens.txt 8 --router-password MyPassword123

# 8 workers untuk inject cepat via url custom
python main.py --inject-from-file kiro_tokens.txt 8 --router-password MyPassword123 --router-url http://192.168.1.250:20128 
```

**Validasi Duplikat:**
- Sebelum inject, bot cek koneksi yang sudah ada di 9router
- Jika `email` sudah ada (provider = kiro), entry akan dilewati (skip)
- Tidak ada duplikat yang masuk ke 9router

**Output:**
```
═══════════════════════════════════════════════════════
  INJECT KIRO REFRESH TOKEN KE 9ROUTER DARI FILE
═══════════════════════════════════════════════════════

>  File: C:\laragon\www\KiroApiKey\kiro_tokens.txt
>  9router: http://localhost:20128
>  Provider: kiro
>  Workers: 4

+  Total entry: 50
+  Berhasil inject: 45
>  Duplicate skip: 5
═══════════════════════════════════════════════════════
  SELESAI
═══════════════════════════════════════════════════════
```

## Troubleshooting

| Masalah | Solusi |
|---------|--------|
| **Halaman app.kiro.dev blank saat automation** | Website detect automation. Solusi: <br>1. Script sekarang gunakan **system Chrome** (channel="chrome")<br>2. Hapus `--incognito` flag yang mencurigakan<br>3. Gunakan **mode manual** (`--manual --visible`)<br>4. Jika masih blank, install Chrome di system<br>5. Pastikan Chrome versi terbaru (131+)<br>6. Clear browser data: hapus folder `.browser_data/` |
| **Google detection: "unusual traffic"** | Google mendeteksi bot. Solusi: <br>1. Kurangi jumlah workers (gunakan 1-2 workers max)<br>2. Tambah delay antar batch: `--delay 10`<br>3. Gunakan `--visible` untuk monitoring<br>4. **RECOMMENDED: Gunakan mode manual** (`--manual --visible`)<br>5. Jangan proses terlalu banyak akun sekaligus (max 5-10 per run)<br>6. Gunakan IP berbeda atau proxy<br>7. Tunggu beberapa jam sebelum run lagi |
| Turnstile timeout | Coba `--visible` untuk debug, atau kurangi workers |
| Login Google gagal | Pastikan akun valid dan tidak kena 2FA |
| Verifikasi HP (mode register) | Akun Google baru sering diminta nomor HP — solve manual di browser (script akan pause 180s) |
| Refresh token tidak ditemukan | Coba `--visible` untuk debug, pastikan redirect ke app.kiro.dev berhasil |
| Gagal inject 9router | Cek 9router jalan di `--router-url`, cek password |
| `account.txt tidak ditemukan` | Buat file `account.txt` (mode login) atau `registerakun.txt` (mode register) di folder yang sama dengan `main.py` |
| Browser tidak muncul | Gunakan flag `--visible` |
| Inject dari file gagal | Pastikan format file benar: `email:refresh_token` (satu per baris) |
| Duplikat di 9router | Normal — bot skip akun yang sudah ada, tidak perlu hapus manual |

### Tips Menghindari Google Detection

**⭐ SOLUSI TERBAIK: GUNAKAN MODE MANUAL!**

```bash
python main.py --manual --visible
```

Mode manual = Anda login sendiri, bot hanya capture token. **100% success rate!**

**Kenapa Mode Manual Lebih Baik:**
- ✅ **Zero detection** - Anda login seperti user biasa
- ✅ **No blank page** - Website load normal tanpa masalah
- ✅ **No JavaScript errors** - React app work perfectly
- ✅ **Easy captcha solve** - Handle manual sendiri
- ✅ **Easy verification** - Nomor HP, 2FA, dll mudah handle
- ✅ **100% success rate** - Jika login manual berhasil, token pasti dapat

**Mode Auto (untuk batch besar):**

1. **Kurangi Workers**: Max 1-2 workers, jangan terlalu banyak concurrent requests
   ```bash
   python main.py 5 1 --delay 10  # 5 akun, 1 worker, delay 10s antar batch
   ```

2. **Gunakan Proxy/VPN**: Rotasi IP address untuk setiap batch
   - Hindari menggunakan VPS/datacenter IP (Google lebih strict)
   - Gunakan residential proxy jika memungkinkan

3. **Batch Kecil**: Proses max 5-10 akun per run, tunggu beberapa jam sebelum run lagi
   ```bash
   python main.py 5 1 --delay 15  # Conservative approach
   ```

4. **Delay Lebih Lama**: Tambah delay antar batch
   ```bash
   python main.py 10 2 --delay 20  # Delay 20 detik antar batch
   ```

5. **Visible Mode**: Monitor apakah ada captcha atau detection
   ```bash
   python main.py 5 1 --visible --delay 10
   ```

6. **Jangan Berlebihan**: Google tracking per IP dan per session
   - Max 10-20 akun per IP per hari
   - Jangan run 24/7 non-stop

### Stealth Features (Minimal & Safe)

Script menggunakan teknik anti-detection yang **minimal dan aman**:
- ✅ System Chrome (channel="chrome") untuk natural browser
- ✅ Simplified launch args (no aggressive flags)
- ✅ Minimal init script (only override navigator.webdriver)
- ✅ No playwright-stealth (terlalu agresif, cause errors)
- ✅ No extra HTTP headers (cause ERR_INVALID_ARGUMENT)
- ✅ Human-like typing (char-by-char dengan delay random)
- ✅ Random delays antar action (2-4.5s)
- ✅ Fresh browser per batch (no cookie carryover)

**Filosofi:** Less is more. Terlalu banyak stealth justru lebih mencurigakan!

## List Akun

Untuk melihat daftar akun yang sudah diproses:

```bash
python main.py --list
```

Output:
```
═══════════════════════════════════════════════════════
  DAFTAR AKUN KIRO
═══════════════════════════════════════════════════════

>  Total akun : 20
+  Berhasil   : 18
x  Gagal      : 2

┏━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
║ #  ║ Email                     ║ Status ║ Refresh Token   ║ Timestamp          ║
┡━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
│  1 │ user1@gmail.com           │ SUCCESS│ ...12345678     │ 2026-07-31 10:30:45│
│  2 │ user2@gmail.com           │ SUCCESS│ ...87654321     │ 2026-07-31 10:31:12│
...
```

## Arsitektur

```
KiroApiKey/
├── main.py                      # Bot utama (Kiro refresh token)
├── kiro.py                      # Original Kiro script (reference)
├── dashboard.py                 # TUI dashboard (Rich) - optional
├── account.txt                  # Input akun login (email:password)
├── registerakun.txt             # Input akun register (email:password)
├── kiro_tokens.txt              # Output refresh token (email:refresh_token)
├── account.json                 # Log akun sudah diproses
├── account.json.example         # Template account.json
├── requirements.txt             # Dependencies
├── README.md                    # Dokumentasi
└── backup/                      # Folder backup
    ├── main.py.cloudflare.backup    # Backup script Cloudflare lama
    ├── kiro.py.backup               # Backup Kiro versi lama
    └── kiro.py.original             # Backup Kiro original
```

## Workflow Detail

### 1. Login/Register Flow (Step by Step)

```
┌─────────────────────────────────────────────────────────┐
│ 1. Navigasi ke https://kiro.dev/ (Landing Page)         │
│    Bot membuka halaman utama Kiro                       │
│    Delay 2-4s (seperti user membaca)                    │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 2. Klik "Sign in" di Landing Page                       │
│    Bot mencari tombol Sign in dan klik                  │
│    Lebih natural daripada direct access                 │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 3. Redirect ke app.kiro.dev/signin                      │
│    Halaman signin dengan pilihan OAuth provider         │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 4. Klik "Continue with Google" / "Sign in with Google"  │
│    Bot otomatis mencari dan klik tombol Google          │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 5. Redirect ke Google OAuth (accounts.google.com)       │
│    - Input email (char-by-char, 50-100ms/char) → Next  │
│    - Input password (char-by-char, 40-100ms/char) → Next│
│    - Handle "I understand" (GSuite) jika ada            │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 6. Consent Page (Google → Cognito)                      │
│    "Google will allow kiro-prod-us-east-1...            │
│     to access this info about you"                      │
│    Bot otomatis klik "Allow" / "Continue"               │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 7. Redirect ke app.kiro.dev                             │
│    - Register mode: akun baru otomatis dibuat           │
│    - Login mode: login berhasil                         │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ 8. Capture Refresh Token                                │
│    Primary: Network interception (/oauth2/token)        │
│    Fallback: localStorage → URL hash → cookies          │
│    Save ke kiro_tokens.txt & account.json               │
└─────────────────────────────────────────────────────────┘
```

### 2. Token Capture Strategy

Bot menggunakan multi-strategy untuk capture refresh token:

1. **Network Interception** (Primary) ⭐
   - Monitor semua network request/response
   - Detect `/oauth2/token` endpoint dari Cognito
   - Extract `refresh_token` dari JSON response
   - Paling reliable dan cepat

2. **localStorage** (Fallback #1)
   - Polling localStorage setiap 2 detik
   - Cari key yang mengandung `refreshToken` atau `.refreshToken`
   - Cognito menyimpan token di localStorage dengan format tertentu

3. **URL Hash** (Fallback #2)
   - Parse URL fragment setelah `#`
   - Cari parameter `refresh_token=...`
   - Untuk implicit grant flow

4. **Cookies** (Fallback #3)
   - Scan semua cookies
   - Cari cookie name yang mengandung "refresh"

### 3. Batch Processing

- **Fresh Browser per Batch**: Setiap batch menggunakan browser baru (no cookie/session carryover)
- **Multi-Worker Paralel**: Proses beberapa akun sekaligus dalam satu batch
- **Auto-Save**: Hasil disimpan langsung setelah setiap batch selesai
- **Error Isolation**: Error di satu akun tidak mempengaruhi akun lain

### 4. 9Router Injection (Optional)

Jika `--inject-9router` diaktifkan:
1. Login ke 9router dengan password
2. Check koneksi existing (cegah duplicate)
3. POST refresh token ke `/api/providers` sebagai provider "kiro"
4. Auto-skip jika akun sudah ada di 9router

## Notes

- Script ini menggunakan **Playwright + playwright-stealth** untuk bypass anti-bot detection
- **Cognito OAuth flow**: app.kiro.dev → Cognito hosted UI → Google → consent → callback → refresh token
- **Token format**: JWT refresh token dari AWS Cognito (panjang ~1000+ chars)
- **9router integration**: inject refresh token sebagai API key untuk provider "kiro"

## License

MIT
