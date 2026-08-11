# Kiro Token Generator

Bot otomatis untuk mendapatkan refresh token dari Kiro.dev via Google OAuth.  
Tersedia dalam 2 mode: **Web Dashboard** (recommended) dan **CLI**.

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements-web.txt
playwright install chromium

# Start web dashboard
python kiro.py start

# Buka browser
# http://localhost:8000
```

---

## Web Dashboard

```bash
python kiro.py start                    # default port 8000
python kiro.py start --port 3000        # custom port
python kiro.py start --host 0.0.0.0     # allow external access
python kiro.py start --reload           # dev mode (auto-restart)
python kiro.py init                     # inisialisasi database
python kiro.py version                  # cek versi
```

---

## CLI (main.py)

### Login Mode

```bash
python main.py                          # semua akun, 2 workers
python main.py 10                       # 10 akun, 2 workers
python main.py 10 4                     # 10 akun, 4 workers
python main.py 10 4 --visible           # browser visible
python main.py 10 4 -a my_accounts.txt  # custom file akun
```

### Register Mode

```bash
python main.py 10 4 --register
python main.py 10 4 --register --visible
python main.py 10 4 --register -a registerakun_lain.txt
```

### Manual Mode

```bash
python main.py --manual --visible       # login manual, bot capture token
python main.py 1 1 --manual --visible
```

### List & Info

```bash
python main.py --list                   # lihat akun yang sudah diproses
```

**Format `account.txt` / `registerakun.txt`:**
```
email1@gmail.com:password1
email2@gmail.com:password2
```

---

## Inject ke 9Router

### Via Web Dashboard

1. Klik **"Inject to 9Router"**
2. Isi URL: `http://localhost:20128` atau domain VPS
3. Isi password (jika ada)
4. Klik **"Start Injection"**

### Via Terminal (inject_vps.py)

Edit `inject_vps.py` lalu jalankan:

```bash
# Edit ROUTER_URL dan ROUTER_PASSWORD di inject_vps.py
python inject_vps.py
```

Script ini inject semua token dari database yang belum diinjected, lalu update status di database otomatis.

### Via CLI (main.py)

```bash
# Inject dari file kiro_tokens.txt
python main.py --inject-from-file kiro_tokens.txt --router-password YOUR_PASS

# Inject sambil generate token
python main.py 10 4 --inject-9router --router-password YOUR_PASS

# Custom URL 9router
python main.py --inject-from-file kiro_tokens.txt \
  --router-url https://9router.gxa.my.id \
  --router-password YOUR_PASS
```

---

## Export

```bash
# Export token ke kiro_tokens.txt (via web dashboard)
# Klik "Export Tokens (.txt)"

# Export ke Excel
# Klik "Export Excel - All / Success / Failed"
```

---

## Troubleshooting

| Problem | Solusi |
|---------|--------|
| Port sudah dipakai | `python kiro.py start --port 3000` |
| Database error | `del kiro.db` lalu `python kiro.py init` |
| Playwright browser tidak ditemukan | `venv\Scripts\playwright.exe install chromium` |
| Token simulated (bukan asli) | Pastikan playwright terinstall di venv |
| Inject gagal 403/Cloudflare | Matikan VPN, gunakan `inject_vps.py` (pakai requests) |
| Inject gagal 401 Unauthorized | Cek password 9router |

---

## Dokumentasi Lengkap

Lihat [PROJECT.md](PROJECT.md) untuk dokumentasi lengkap termasuk API endpoints, struktur database, dan changelog.
