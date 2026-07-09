# CF API Key Bot v3.0 — Stealth Edition

Bot otomatis untuk membuat Cloudflare Workers AI API Key massal menggunakan Playwright + playwright-stealth.

## Fitur

- Auto-login Google → Cloudflare → buat API Key
- **Mode registrasi: sign-up akun Cloudflare baru via Google** (`--register`)
- Bypass Cloudflare Turnstile/captcha dengan stealth mode
- Multi-worker paralel (configurable)
- Headless mode (default) atau visible browser
- Log akun sudah diproses (skip re-run)
- Inject akun ke 9router setelah API key berhasil

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

> **Mode login** (`account.txt`): akun harus sudah terdaftar di Cloudflare dan bisa login via Google.
> **Mode register** (`registerakun.txt`): akun Google bisa baru (belum terdaftar di Cloudflare).

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

### Semua Argumen

```
python main.py [jumlah] [workers] [options]

Positional:
  jumlah              Jumlah akun yang diproses (default: all)
  workers             Jumlah worker paralel (default: 2)

Options:
  -a, --accounts      Path file akun (default: account.txt)
  -o, --output        Path file output (default: cloudflare_api.txt)
  -d, --delay         Delay antar batch dalam detik (default: 3)
  --visible           Tampilkan browser (default: headless)
  --inject-9router    Inject akun ke 9router setelah API key berhasil
  --inject-from-file  Inject dari file cloudflare_api.txt ke 9router
  --router-url        URL 9router (default: http://localhost:20128)
  --router-password   Password 9router (opsional, auto-login)
  --register          Mode registrasi: sign-up akun Cloudflare baru via Google
```

### Contoh Lengkap

```bash
# 10 akun, 4 workers, visible browser
python main.py 10 5 --visible

# Semua akun, 4 workers, inject ke 9router
python main.py all 4 --inject-9router --router-password PutihAbu123!

# 5 akun, 2 workers, file akun custom
python main.py 5 2 -a my_accounts.txt

# 20 akun, 6 workers, output custom, inject ke 9router remote
python main.py 20 6 -o hasil.txt --inject-9router --router-url http://192.168.1.100:20128

# Inject dari file ke 9router (tanpa buat API key baru)
python main.py --inject-from-file cloudflare_api.txt --router-password PutihAbu123!
```

### Mode Registrasi

Mode `--register` untuk membuat akun Cloudflare **baru** via Google sign-up (bukan login akun yang sudah ada).

File akun default: `registerakun.txt` (bukan `account.txt`).

```bash
# Registrasi 10 akun baru, 4 workers, headless (baca dari registerakun.txt)
python main.py 10 4 --register

# Registrasi dengan browser visible (debug)
python main.py 10 2 --register --visible

# Registrasi + inject ke 9router
python main.py all 4 --register --inject-9router --router-password PutihAbu123!

# Override file akun manual
python main.py 10 4 --register -a akun_register_lain.txt
```

**Flow registrasi:**
1. Navigasi ke `dash.cloudflare.com/sign-up` (bukan `/login`)
2. Klik "Sign up with Google"
3. Login Google (email + password)
4. Klik "I understand" → "Allow" untuk consent Google OAuth
5. Redirect ke Cloudflare dashboard (akun baru otomatis dibuat)
6. Buat API Key via API (sama seperti mode login)

> **Catatan:** Akun Google baru kadang diminta verifikasi nomor HP saat OAuth pertama.
> Script akan pause dan menunggu solve manual (timeout 180s).

**Error handling register mode:**
- Akun **berhasil** → dicatat di `account.json` (skip saat re-run)
- Akun **gagal** → ditulis ke `account.txt` untuk diproses manual via mode login
  ```bash
  # Setelah register, proses akun yang gagal secara manual
  python main.py
  ```

## Output

### `cloudflare_api.txt`

Format: `account_id:apikey` (satu per baris)

```
d30fffe39bd9f2a743fcad6197385719:cfut_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6:cfut_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

### `account.json`

Log semua akun yang sudah diproses. Format:

```json
{
  "user@gmail.com": {
    "success": true,
    "account_id": "d30fffe39bd9f2a743fcad6197385719",
    "api_key": "cfut_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "error": "",
    "timestamp": "2026-07-06 10:30:45"
  },
  "user2@gmail.com": {
    "success": false,
    "account_id": "",
    "api_key": "",
    "error": "Turnstile timeout",
    "timestamp": "2026-07-06 10:31:02"
  }
}
```

> Akun yang sudah ada di `account.json` akan dilewati saat re-run.

## Inject ke 9router

Setelah API key berhasil dibuat, bot bisa langsung inject ke 9router.

### Cara Kerja

1. Login ke 9router (`POST /api/auth/login`) → dapat `auth_token`
2. POST ke `/api/providers` dengan data:
   ```json
   {
     "provider": "cloudflare-ai",
     "apiKey": "cfut_xxx",
     "name": "user@gmail.com",
     "priority": 1,
     "testStatus": "active",
     "providerSpecificData": {
       "accountId": "d30fffe39bd9f2a743fcad6197385719"
     }
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
```

### Output di Terminal

```
>  Batch 1/5 — Memproses 2 akun...
+  API Key diambil: cfut_ROdt03yF0...
+  Injected ke 9router: user1@gmail.com
+  API Key diambil: cfut_XXXXXXXX...
+  Injected ke 9router: user2@gmail.com
>  Batch 1/5 selesai — Tersimpan ke cloudflare_api.txt
```

### Inject dari File

Jika sudah punya `cloudflare_api.txt` dan ingin inject ke 9router tanpa buat API key baru:

```bash
python main.py --inject-from-file cloudflare_api.txt --router-password MyPassword123
```

**Multi-Worker Inject:**

Gunakan argumen `workers` (posisi ke-2) untuk mengatur jumlah worker paralel:

```bash
# 4 workers paralel untuk inject
python main.py --inject-from-file cloudflare_api.txt 4 --router-password MyPassword123

# 8 workers untuk inject cepat
python main.py --inject-from-file cloudflare_api.txt 8 --router-password MyPassword123

# 8 workers untuk inject cepat via url
python main.py --inject-from-file cloudflare_api.txt 8 --router-password MyPassword123 --router-url http://192.168.1.250:20128 
```

**Validasi Duplikat:**
- Sebelum inject, bot cek koneksi yang sudah ada di 9router
- Jika `account_id` sudah ada, entry akan dilewati (skip)
- Tidak ada duplikat yang masuk ke 9router

**Output:**
```
───────────────────────────────
  INJECT KE 9ROUTER DARI FILE
───────────────────────────────

>  File: D:\AI\CloudflareAPI\FlowCf\cloudflare_api.txt
>  9router: http://localhost:20128

+  Total entry: 50
+  Berhasil inject: 45
>  Duplicate skip: 5
───────────────────────────────
  SELESAI
───────────────────────────────
```

## Troubleshooting

| Masalah | Solusi |
|---------|--------|
| Turnstile timeout | Coba `--visible` untuk debug, atau kurangi workers |
| Login Google gagal | Pastikan akun valid dan tidak kena 2FA |
| Verifikasi HP (mode register) | Akun Google baru sering diminta nomor HP — solve manual di browser |
| Akun gagal saat register | Otomatis dipindahkan ke `account.txt`, proses manual: `python main.py` |
| Gagal inject 9router | Cek9router jalan di `--router-url`, cek password |
| `account.txt tidak ditemukan` | Buat file `account.txt` (mode login) atau `registerakun.txt` (mode register) di folder yang sama dengan `main.py` |
| Browser tidak muncul | Hapus `--visible` (default headless) |
| Inject dari file gagal | Pastikan format file benar: `account_id:apikey` (satu per baris) |
| Duplikat di 9router | Normal — bot skip akun yang sudah ada, tidak perlu hapus manual |

## Arsitektur

```
FlowCf/
├── main.py              # Bot utama (Playwright + stealth)
├── dashboard.py         # TUI dashboard (Rich)
├── account.txt          # Input akun login (email:password)
├── registerakun.txt     # Input akun register (email:password)
├── cloudflare_api.txt   # Output API key (account_id:apikey)
├── account.json         # Log akun sudah diproses
├── requirements.txt     # Dependencies
└── WORKFLOW.md          # Reverse-engineered flow reference
```
