# Inject Kiro Tokens ke 9Router - Documentation

## ✅ SUCCESS - Auto-Inject Working!

Setelah testing dan inspect element, kami menemukan endpoint yang benar untuk inject Kiro tokens ke 9router.

---

## 🎯 Endpoint yang Benar

**URL:** `POST /api/oauth/kiro/import`

**Payload:**
```json
{
  "refreshToken": "aorAAAAAGrkq4w...:MGQCMDt/vSRO..."
}
```

**Response (Success):**
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

**Provider:** `kiro` (SUPPORTED oleh 9router!)

---

## 🚀 Cara Inject - CLI

### 1. Inject dari File

```bash
python main.py --inject-from-file kiro_tokens.txt --router-password PutihAbu123!
```

**Output:**
```
════════════════════════════════════════════════════════════
INJECT KIRO REFRESH TOKEN KE 9ROUTER DARI FILE
════════════════════════════════════════════════════════════

>  File: kiro_tokens.txt
>  9router: http://localhost:20128
>  Provider: kiro
>  Workers: 2

+  Total entry: 26
+  Berhasil inject: 26

════════════════════════════════════════════════════════════
SELESAI
════════════════════════════════════════════════════════════
```

### 2. Inject Sambil Generate

```bash
# Generate dan auto-inject
python main.py 10 4 --inject-9router --router-password PutihAbu123!
```

### 3. Custom 9Router URL

```bash
python main.py --inject-from-file kiro_tokens.txt \
  --router-url http://192.168.1.100:20128 \
  --router-password YOUR_PASSWORD
```

---

## 🌐 Cara Inject - Web Dashboard

### 1. Bulk Inject (Semua Tokens)

1. Start web dashboard:
   ```bash
   kiro start
   ```

2. Open browser: `http://localhost:8000`

3. Generate tokens (add accounts → start processing)

4. Click button **"Inject to 9Router"**

5. Configure:
   - **9Router URL:** `http://localhost:20128` (default)
   - **Password:** Isi jika 9router pakai password
   
6. Click **"Start Injection"**

7. Monitor progress:
   - Real-time status updates
   - Injected count di statistics
   - "9Router" column di table

### 2. Single Inject (Per Account)

1. Di accounts table, cari account dengan token

2. Click icon **upload** (purple) di kolom Actions

3. Confirm injection

4. Status akan update otomatis

---

## 📊 Verification

### Via CLI Script

```bash
python verify_inject.py
```

**Output:**
```
Kiro tokens di 9router:
============================================================
1. (no email) - Status: active
2. (no email) - Status: active
...
77. (no email) - Status: active
============================================================
Total: 77 akun Kiro di 9router
```

### Via Browser

Buka 9router dashboard:
```
http://localhost:20128/dashboard/providers/kiro
```

### Via Web Dashboard

Check statistics card:
- **Injected to 9Router:** Shows count of injected tokens
- **9Router column:** Shows Yes/No per account

---

## 🎯 Features

### CLI Features:
- ✅ Bulk inject dari file
- ✅ Auto-inject saat processing
- ✅ Multi-threaded (workers)
- ✅ Custom 9router URL
- ✅ Password authentication

### Web Dashboard Features:
- ✅ Bulk inject all tokens
- ✅ Single inject per account
- ✅ Real-time status tracking
- ✅ Connection ID saved
- ✅ Skip already injected
- ✅ Background processing
- ✅ Progress monitoring
- ✅ Config persistence

---

## 📝 Format Token

Token Kiro format (dalam kiro_tokens.txt):
```
email@example.com:aorAAAAAGrkq4w...:MGQCMDt/vSRO...
```

**Format:** `email:part1:part2`

Saat inject ke 9router, kedua bagian digabung:
```json
{
  "refreshToken": "aorAAAAAGrkq4w...:MGQCMDt/vSRO..."
}
```

---

## 🔧 Technical Details

### Implementation (main.py)

```python
def inject_to_9router(router_url, password, email, refresh_token):
    # Use correct Kiro OAuth import endpoint
    kiro_import_url = f"{router_url}/api/oauth/kiro/import"
    
    payload = {"refreshToken": refresh_token}
    
    # POST request
    response = requests.post(
        kiro_import_url,
        json=payload,
        headers={"Content-Type": "application/json"},
        cookies={"auth_token": auth_token}
    )
    
    return response.json()
```

### Implementation (Web Dashboard)

Backend (web/app.py):
```python
@app.post("/api/inject/9router")
async def inject_to_9router(config: RouterConfig):
    # Bulk inject all tokens
    accounts = get_accounts_with_tokens()
    for account in accounts:
        result = inject_single_token(account.refresh_token)
        if result["success"]:
            account.injected_to_9router = True
            account.router_connection_id = result["connection_id"]
```

Frontend (index.html):
- Modal untuk config 9router
- Button untuk bulk inject
- Icon per row untuk single inject
- Real-time status updates

---

## 🎉 Testing Results

**Date:** 2026-08-01

**CLI Test:**
- Input: 26 tokens dari kiro_tokens.txt
- Result: 26/26 berhasil inject (100%)
- Time: ~5 seconds

**Total di 9Router:**
- 77 akun Kiro provider
- 74 status: active (96%)
- 3 status: unavailable (4%)

**Dashboard:** http://localhost:20128/dashboard/providers/kiro

---

## ❓ FAQ

**Q: Kenapa endpoint `/api/providers` tidak work?**  
A: Endpoint `/api/providers` untuk provider generic. Kiro punya endpoint khusus OAuth: `/api/oauth/kiro/import`

**Q: Apakah perlu email saat inject?**  
A: Tidak. Endpoint Kiro hanya perlu `refreshToken`. Email otomatis null di 9router.

**Q: Bisa inject duplicate?**  
A: Bisa, tapi 9router akan create connection baru dengan ID berbeda.

**Q: Bagaimana cara skip duplicate?**  
A: Web dashboard auto-track `injected_to_9router` status. Hanya inject yang belum di-inject.

**Q: Token format salah?**  
A: Token harus format: `part1:part2` (kedua bagian dengan colon di tengah).

**Q: Inject gagal "Unauthorized"?**  
A: Pastikan 9router running dan password benar (jika diset).

---

## 🔗 References

- Endpoint discovery: `docs/kiro_import_inspect.md`
- Verification script: `verify_inject.py`
- Main implementation: `main.py` (line 864-920)
- Web implementation: `web/app.py` (line 180-250)

---

## 📞 Support

Jika ada issue:
1. Check 9router running: `http://localhost:20128`
2. Check token format di kiro_tokens.txt
3. Test manual via browser inspector
4. Check logs di terminal

---

**Version:** 1.0.0  
**Status:** ✅ WORKING  
**Last Updated:** 2026-08-01  
**Success Rate:** 100% injection, 96% active
