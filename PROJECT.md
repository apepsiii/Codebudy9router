# Kiro Token Generator

> Bot otomatis untuk mendapatkan refresh token dari Kiro.dev via Google OAuth, dengan Web Dashboard dan CLI.

---

## Daftar Isi

- [Quick Start](#quick-start)
- [Instalasi](#instalasi)
- [Web Dashboard](#web-dashboard)
- [CLI Commands](#cli-commands)
- [Inject ke 9Router](#inject-ke-9router)
- [API Endpoints](#api-endpoints)
- [Struktur File](#struktur-file)
- [Troubleshooting](#troubleshooting)
- [Changelog](#changelog)

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements-web.txt
playwright install chromium

# 2. Start server
python kiro.py start

# 3. Buka browser
# http://localhost:8000
```

---

## Instalasi

### Requirements

- Python 3.8+
- pip

### Install Dependencies

```bash
pip install -r requirements-web.txt
```

Paket yang diinstall:
- `fastapi` — web framework
- `uvicorn` — web server
- `sqlalchemy` — database ORM
- `pydantic` — data validation
- `aiosqlite` — async SQLite
- `playwright` — browser automation
- `playwright-stealth` — anti-detection
- `openpyxl` — export Excel

### Install Browser

```bash
playwright install chromium
```

### Inisialisasi Database

```bash
python kiro.py init
```

### Verifikasi

```
[ ] Python 3.8+ terinstall
[ ] pip install -r requirements-web.txt berhasil
[ ] playwright install chromium berhasil
[ ] python kiro.py init (database terbuat)
[ ] python kiro.py start (server jalan)
[ ] Browser bisa akses http://localhost:8000
```

---

## Web Dashboard

Server berjalan di **http://localhost:8000**

### Fitur

| Fitur | Keterangan |
|-------|-----------|
| Add Accounts | Single atau bulk import (format `email:password`) |
| Process Control | Start, retry failed, reset all ke pending |
| Live Log | Terminal-style log realtime saat processing |
| Export Tokens | Export ke `.txt` atau `.xlsx` (All/Success/Failed) |
| 9Router Inject | Auto inject via API atau toggle manual per akun |
| Statistics | Total, success, failed, injected, success rate |
| Filter | Filter akun by status |

### Workflow

```
1. Start server    → python kiro.py start
2. Buka browser   → http://localhost:8000
3. Add accounts   → Single atau bulk import
4. Configure      → Workers, delay, visible mode
5. Process        → Klik "Start Processing"
6. Monitor        → Live log + status realtime
7. Export         → .txt atau .xlsx
8. Inject         → Auto atau manual ke 9router
```

### Process Settings

| Setting | Default | Keterangan |
|---------|---------|-----------|
| Workers | 2 | Jumlah akun parallel (1–10) |
| Delay | 3.0s | Jeda antar akun |
| Show Browser | Off | Tampilkan browser saat processing |
| Manual Mode | Off | User login manual, bot capture token |

### Tombol Action

| Tombol | Fungsi |
|--------|--------|
| Start Processing | Proses semua akun pending |
| Retry Failed | Reset akun failed → pending, lalu bisa diproses ulang |
| Reset All | Reset semua akun → pending |
| Export Tokens (.txt) | Simpan token ke `kiro_tokens.txt` |
| Export Excel - All | Export semua akun ke `.xlsx` |
| Export Excel - Success | Export akun berhasil saja |
| Export Excel - Failed | Export akun gagal saja |
| Inject to 9Router | Bulk inject semua token ke 9router |

### Kolom 9Router

Di tabel akun, kolom **9Router** menampilkan tombol toggle:
- `☐ Not yet` → klik → `☑ Injected` (tandai sudah diinjected manual)
- Klik lagi untuk unmark

---

## CLI Commands

```bash
# Start web server
python kiro.py start
python kiro.py start --port 3000
python kiro.py start --host 0.0.0.0
python kiro.py start --reload          # dev mode

# Inisialisasi database
python kiro.py init

# Versi
python kiro.py version

# Help
python kiro.py help
```

### CLI Legacy (main.py)

```bash
# Login mode (akun Kiro yang sudah ada)
python main.py                          # semua akun, 2 workers
python main.py 10                       # 10 akun, 2 workers
python main.py 10 4                     # 10 akun, 4 workers
python main.py 10 4 --visible           # browser visible

# Register mode (buat akun baru)
python main.py 10 4 --register
python main.py 10 4 --register --visible

# Manual mode (login manual, bot capture token)
python main.py --manual --visible

# List akun yang sudah diproses
python main.py --list

# Custom file
python main.py 10 4 -a my_accounts.txt
```

**Format `account.txt`:**
```
email1@gmail.com:password1
email2@gmail.com:password2
```

---

## Inject ke 9Router

### Endpoint yang Digunakan

```
POST /api/oauth/kiro/import
```

```json
{
  "refreshToken": "aorAAAAAGrkq4w...:MGQCMDt/vSRO..."
}
```

**Response sukses:**
```json
{
  "success": true,
  "connection": {
    "id": "96d77fed-223b-4677-b45b-dbba78acaf1c",
    "provider": "kiro",
    "email": null
  }
}
```

### Via Web Dashboard

1. Klik tombol **"Inject to 9Router"**
2. Isi 9Router URL: `http://localhost:20128`
3. Isi password (jika ada)
4. Klik **"Start Injection"**

Atau inject satu per satu: klik icon **upload** di kolom Actions.

### Via CLI

```bash
# Inject dari file
python main.py --inject-from-file kiro_tokens.txt --router-password YOUR_PASS

# Inject sambil generate token
python main.py 10 4 --inject-9router --router-password YOUR_PASS

# Custom 9router URL
python main.py --inject-from-file kiro_tokens.txt \
  --router-url http://192.168.1.100:20128 \
  --router-password YOUR_PASS
```

### Verifikasi

```bash
# Via script
python verify_inject.py

# Via browser
http://localhost:20128/dashboard/providers/kiro
```

### Catatan Provider

| Provider | Status |
|----------|--------|
| `kiro` | ✅ Valid (endpoint khusus OAuth) |
| `anthropic` | ✅ Valid (alternatif) |
| `openai` | ✅ Valid |
| `kr` | ❌ Tidak valid |

---

## API Endpoints

| Method | Endpoint | Keterangan |
|--------|----------|-----------|
| GET | `/api/stats` | Statistik dashboard |
| GET | `/api/accounts` | List akun (filter by status) |
| POST | `/api/accounts` | Tambah satu akun |
| POST | `/api/accounts/bulk` | Bulk import akun |
| POST | `/api/accounts/reset` | Reset akun ke pending |
| PATCH | `/api/accounts/{id}/mark-injected` | Toggle status injected manual |
| DELETE | `/api/accounts/{id}` | Hapus akun |
| DELETE | `/api/accounts` | Hapus semua akun |
| POST | `/api/process/start` | Mulai processing |
| POST | `/api/export/tokens` | Export token ke .txt |
| GET | `/api/export/excel` | Export ke .xlsx |
| GET | `/api/logs/{id}` | Log per akun |
| GET | `/api/logs/recent` | Log realtime semua akun processing |
| POST | `/api/inject/9router` | Bulk inject ke 9router |
| POST | `/api/inject/9router/{id}` | Inject satu akun ke 9router |
| GET | `/api/9router/config` | Ambil config 9router |
| POST | `/api/9router/config` | Simpan config 9router |

---

## Struktur File

```
KiroApiKey/
├── kiro.py                  ← CLI entry point
├── kiro.bat                 ← Windows launcher
├── main.py                  ← Script automation Playwright
├── kiro.db                  ← SQLite database (auto-created)
├── kiro_tokens.txt          ← Output token (email:token)
├── account.txt              ← Input akun login (email:password)
├── registerakun.txt         ← Input akun register (email:password)
├── account.json             ← Log CLI (email → status/token)
├── requirements.txt         ← Requirements CLI
├── requirements-web.txt     ← Requirements web dashboard
├── web/
│   ├── __init__.py
│   ├── app.py               ← FastAPI backend
│   ├── database.py          ← SQLAlchemy models
│   └── static/
│       └── index.html       ← Web dashboard UI
├── docs/
│   └── kiro_import_inspect.md  ← Inspeksi endpoint 9router
└── PROJECT.md               ← File ini
```

### Database Tables

| Table | Keterangan |
|-------|-----------|
| `accounts` | Semua akun, status, token, injected |
| `config` | Konfigurasi (9router URL, dll) |
| `process_logs` | Log proses per akun |

---

## Troubleshooting

### Server tidak bisa start

```bash
# Cek port sudah dipakai
netstat -ano | findstr :8000

# Ganti port
python kiro.py start --port 3000
```

### Database error

```bash
# Reset database
del kiro.db
python kiro.py init
```

### Playwright browser tidak ditemukan

```bash
# Install browser untuk venv
venv\Scripts\playwright.exe install chromium
```

### Processing tidak jalan / token simulated

Pastikan Playwright browser sudah terinstall di venv yang digunakan:
```bash
venv\Scripts\playwright.exe install chromium
```

### Inject ke 9router gagal "Unauthorized"

- Pastikan 9router running di `http://localhost:20128`
- Pastikan password 9router benar

### Inject gagal "Import failed"

- Cek format token: harus `part1:part2` (dua bagian dipisah colon)
- Cek token belum expired

---

## Changelog

### v1.2.0 — 2026-08-05

- Fitur export Excel (`.xlsx`) dengan styling warna per status
- Sheet Summary di file Excel (statistik ringkas)
- Toggle manual inject per akun di tabel
- Live log panel realtime saat processing
- Tombol Retry Failed dan Reset All
- Optimasi log polling (1 request vs N request per interval)
- Fix: kolom `router_connection_id` ditambahkan ke database

### v1.1.0 — 2026-08-02

- Web Dashboard (FastAPI + Alpine.js + Tailwind)
- SQLite database untuk persistent storage
- Background processing dengan Playwright asli
- Visible mode dari web (browser muncul saat processing)
- Manual mode support dari web
- Auto-inject ke 9router via endpoint `/api/oauth/kiro/import`
- Export token ke `.txt`

### v1.0.1 — 2026-08-01

- Fix: provider default diubah ke `"anthropic"` untuk kompatibilitas 9router
- Cleanup format `kiro_tokens.txt` (hapus prefix `(done)`)
- Ditemukan endpoint resmi 9router untuk inject Kiro: `/api/oauth/kiro/import`

### v1.0.0 — 2026-07-31

- Login/Register Kiro via Google OAuth otomatis
- Capture refresh token dari Cognito (network interception + localStorage + cookies)
- Multi-worker parallel processing
- Manual mode (user login, bot capture token)
- Resume support (skip akun yang sudah sukses)
- Inject ke 9router via CLI
