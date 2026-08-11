import sqlite3
import sys
import requests

ROUTER_URL = "https://9router.gxa.my.id"
ROUTER_PASSWORD = "PutihAbu123!"

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": ROUTER_URL,
    "Referer": f"{ROUTER_URL}/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
})

def login_9router(password):
    url = f"{ROUTER_URL}/api/auth/login"
    try:
        resp = SESSION.post(url, json={"password": password}, timeout=15)
        if resp.status_code == 200:
            token = SESSION.cookies.get("auth_token")
            return token
        print(f"[!] Login HTTP {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        print(f"[!] Login error: {e}")
    return None

def inject_token(refresh_token):
    url = f"{ROUTER_URL}/api/oauth/kiro/import"
    try:
        resp = SESSION.post(url, json={"refreshToken": refresh_token}, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("success"), data.get("connection", {}).get("id")
        return False, f"HTTP {resp.status_code}: {resp.text[:100]}"
    except Exception as e:
        return False, str(e)

# Load tokens
conn = sqlite3.connect(r'C:\laragon\www\KiroApiKey\kiro.db')
rows = conn.execute("SELECT id, email, refresh_token FROM accounts WHERE status = 'success' AND refresh_token IS NOT NULL AND refresh_token != '' AND injected_to_9router = 0").fetchall()
conn.close()

print(f"[*] Token belum diinjected: {len(rows)}")
print(f"[*] Target: {ROUTER_URL}")
print()

if not rows:
    print("[!] Semua token sudah diinjected.")
    sys.exit(0)

# Login
auth_token = login_9router(ROUTER_PASSWORD)
if auth_token:
    print(f"[+] Login berhasil")
else:
    print(f"[!] Login gagal, stop.")
    sys.exit(1)

# Inject
success_count = 0
fail_count = 0
success_ids = []

for i, (acc_id, email, refresh_token) in enumerate(rows, 1):
    ok, result = inject_token(refresh_token)
    if ok:
        success_count += 1
        success_ids.append(acc_id)
        print(f"[{i}/{len(rows)}] OK   {email}  (id: {result})")
    else:
        fail_count += 1
        print(f"[{i}/{len(rows)}] FAIL {email}  ({result})")

# Update database
if success_ids:
    conn = sqlite3.connect(r'C:\laragon\www\KiroApiKey\kiro.db')
    placeholders = ",".join("?" * len(success_ids))
    conn.execute(f"UPDATE accounts SET injected_to_9router = 1 WHERE id IN ({placeholders})", success_ids)
    conn.commit()
    conn.close()

print()
print(f"[+] Berhasil : {success_count}")
print(f"[x] Gagal    : {fail_count}")
print(f"[*] Database updated")
