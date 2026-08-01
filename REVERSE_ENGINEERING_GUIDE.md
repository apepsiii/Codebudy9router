# 9ROUTER KIRO IMPORT - REVERSE ENGINEERING GUIDE

## 📋 LANGKAH-LANGKAH:

### 1. Buka Browser dengan Developer Tools
```
Browser: Chrome/Edge
URL: http://localhost:20128/dashboard/providers/kiro
Tekan: F12 (buka Developer Tools)
Tab: Network
```

### 2. Clear Network Log
```
Klik ikon 🚫 (Clear) di Network tab
Atau tekan Ctrl+E untuk clear
```

### 3. Import Token Manual
```
1. Klik "Import token" button
2. Pilih "Paste refresh token from Kiro IDE"
3. Paste salah satu token dari kiro_tokens.txt
4. Klik Submit/Save/Import
```

### 4. Inspect Network Request
Di Network tab, cari request dengan:
```
✅ Method: POST atau PUT
✅ Status: 200 atau 201 (success)
✅ Type: fetch atau xhr
✅ Name: import, token, kiro, providers, dll
```

### 5. Copy Request Info
Klik request tersebut, lalu copy info berikut:

#### a) General Tab
```
Request URL: http://localhost:20128/api/...
Request Method: POST
Status Code: 200 OK
```

#### b) Headers Tab → Request Headers
```
Content-Type: application/json
Cookie: auth_token=...
```

#### c) Payload/Request Tab → Request Payload
```json
{
  "refreshToken": "aorAAAAA...",
  "email": "user@example.com",
  ...
}
```

## 📝 TEMPLATE INFO YANG SAYA BUTUHKAN:

```
REQUEST URL:
_______________________________________________

METHOD:
_______________________________________________

HEADERS:
Content-Type: _________________________________
Cookie: _______________________________________
(tambahkan header lain jika ada)

BODY/PAYLOAD:
{
  "_____": "_____",
  "_____": "_____"
}

RESPONSE (jika berhasil):
{
  "_____": "_____"
}
```

## 🎯 CONTOH LENGKAP:

```
REQUEST URL:
http://localhost:20128/api/providers/kiro/import

METHOD:
POST

HEADERS:
Content-Type: application/json
Cookie: auth_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

BODY:
{
  "refreshToken": "aorAAAAAGrkq4wgiZVqt6o5t1GR78D9w...",
  "email": "user@example.com",
  "name": "My Kiro Account"
}

RESPONSE:
{
  "success": true,
  "id": "conn_123456"
}
```

## ⚡ QUICK TEST:

Setelah dapat info, test dengan curl:
```bash
curl -X POST http://localhost:20128/api/providers/kiro/import \
  -H "Content-Type: application/json" \
  -H "Cookie: auth_token=YOUR_TOKEN" \
  -d '{
    "refreshToken": "aorAAAAAGrkq4w...",
    "email": "test@example.com"
  }'
```

## 📂 FILES:

- Template function: `9router_kiro_inject.py`
- Tokens ready: `kiro_tokens.txt` (5 tokens)
- Main script: `main.py` (akan diupdate setelah dapat info)

---

**Setelah dapat info dari Network tab, kirim ke saya dan saya akan update script untuk full automation! 🚀**
