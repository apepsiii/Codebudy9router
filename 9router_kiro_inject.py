# ══════════════════════════════════════════════════════════════════════
# 9ROUTER KIRO IMPORT - TEMPLATE UNTUK REVERSE ENGINEERING
# ══════════════════════════════════════════════════════════════════════
"""
Template function untuk inject Kiro refresh token ke 9router.
Setelah reverse engineer API endpoint, update function ini.

INSTRUKSI REVERSE ENGINEERING:
1. Buka: http://localhost:20128/dashboard/providers/kiro
2. F12 → Network tab
3. Import token manual (paste refresh token)
4. Lihat request yang muncul di Network tab
5. Copy info berikut:

YANG DIBUTUHKAN:
- Request URL: /api/...
- Method: POST/PUT/PATCH
- Headers: Content-Type, Cookie, dll
- Body: {JSON payload}

CONTOH REQUEST:
===============
URL: POST http://localhost:20128/api/providers/kiro/import
Headers:
  Content-Type: application/json
  Cookie: auth_token=xxx
Body:
{
  "refreshToken": "aorAAAAAGrkq4w...",
  "email": "user@example.com",
  "name": "Display Name"
}

Response: 200 OK
{
  "success": true,
  "data": {...}
}
"""

import urllib.request
import urllib.error
import json
from typing import Optional


# ── Function untuk inject Kiro token ke 9router ──
def inject_kiro_to_9router_import(
    router_url: str,
    password: Optional[str],
    email: str,
    refresh_token: str,
    auth_token: Optional[str] = None,
) -> dict:
    """
    Inject Kiro refresh token ke 9router menggunakan import endpoint.
    
    Args:
        router_url: URL 9router (e.g., http://localhost:20128)
        password: Password 9router untuk login
        email: Email akun Kiro
        refresh_token: Refresh token dari Kiro
        auth_token: Auth token 9router (optional, akan auto login jika None)
    
    Returns:
        dict: {"success": bool, "data": dict, "error": str}
    """
    
    # Step 1: Login jika belum ada auth_token
    if not auth_token and password:
        try:
            login_url = f"{router_url.rstrip('/')}/api/auth/login"
            login_body = json.dumps({"password": password}).encode("utf-8")
            login_req = urllib.request.Request(
                login_url,
                data=login_body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(login_req, timeout=10) as resp:
                for header in resp.headers.get_all("Set-Cookie") or []:
                    if header.startswith("auth_token="):
                        auth_token = header.split(";")[0].split("=", 1)[1]
                        break
            if not auth_token:
                return {"success": False, "error": "Login gagal: auth_token tidak ditemukan"}
        except Exception as e:
            return {"success": False, "error": f"Login gagal: {e}"}
    
    # ═══════════════════════════════════════════════════════════════
    # TODO: UPDATE ENDPOINT DAN PAYLOAD SESUAI HASIL REVERSE ENGINEERING
    # ═══════════════════════════════════════════════════════════════
    
    # TEMPLATE 1: Jika endpoint adalah /api/providers/kiro/import
    import_url = f"{router_url.rstrip('/')}/api/providers/kiro/import"
    
    # TEMPLATE 2: Payload - sesuaikan dengan format yang diminta 9router
    payload = {
        "refreshToken": refresh_token,
        "email": email,
        "name": email,  # atau display name lain
        # Tambahkan field lain jika diperlukan
    }
    
    # TEMPLATE 3: Headers
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "KiroBot/1.0",
    }
    if auth_token:
        headers["Cookie"] = f"auth_token={auth_token}"
    
    # Step 2: Send request
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(import_url, data=body, headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            response_data = json.loads(resp.read())
            return {"success": True, "data": response_data}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        try:
            error_data = json.loads(error_body)
            error_msg = error_data.get("error", error_body)
        except Exception:
            error_msg = error_body
        return {"success": False, "error": f"HTTP {e.code}: {error_msg}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Batch inject dari file ──
def inject_kiro_from_file(
    file_path: str,
    router_url: str,
    password: Optional[str],
    workers: int = 2,
) -> dict:
    """
    Inject multiple Kiro tokens dari file ke 9router.
    Format file: email:refresh_token (satu per baris)
    """
    import os
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import threading
    
    if not os.path.exists(file_path):
        return {"success": False, "error": f"File tidak ditemukan: {file_path}"}
    
    # Read tokens from file
    entries = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    email, refresh_token = parts[0].strip(), parts[1].strip()
                    if email and refresh_token:
                        entries.append((email, refresh_token))
    
    if not entries:
        return {"success": False, "error": "Tidak ada entry valid di file"}
    
    # Login once and get auth_token
    auth_token = None
    if password:
        try:
            login_url = f"{router_url.rstrip('/')}/api/auth/login"
            login_body = json.dumps({"password": password}).encode("utf-8")
            login_req = urllib.request.Request(
                login_url,
                data=login_body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(login_req, timeout=10) as resp:
                for header in resp.headers.get_all("Set-Cookie") or []:
                    if header.startswith("auth_token="):
                        auth_token = header.split(";")[0].split("=", 1)[1]
                        break
        except Exception as e:
            return {"success": False, "error": f"Login gagal: {e}"}
    
    # Multi-threaded inject
    results = {
        "total": len(entries),
        "injected": 0,
        "failed": 0,
        "errors": [],
    }
    lock = threading.Lock()
    
    def inject_one(entry):
        email, refresh_token = entry
        result = inject_kiro_to_9router_import(
            router_url=router_url,
            password=None,  # Already logged in
            email=email,
            refresh_token=refresh_token,
            auth_token=auth_token,
        )
        return (email, result)
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(inject_one, entry): entry for entry in entries}
        for future in as_completed(futures):
            email, result = future.result()
            with lock:
                if result["success"]:
                    results["injected"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append(f"{email}: {result.get('error', 'unknown')}")
    
    results["success"] = True
    return results


# ── Testing ──
if __name__ == "__main__":
    import sys
    
    print("="*70)
    print("9ROUTER KIRO IMPORT - REVERSE ENGINEERING TEMPLATE")
    print("="*70)
    print()
    print("LANGKAH SELANJUTNYA:")
    print("1. Buka: http://localhost:20128/dashboard/providers/kiro")
    print("2. F12 → Network tab")
    print("3. Import token manual")
    print("4. Copy info request dari Network tab")
    print("5. Update function inject_kiro_to_9router_import() di file ini")
    print()
    print("INFO YANG DIBUTUHKAN:")
    print("- Request URL (endpoint)")
    print("- Request Method (POST/PUT/PATCH)")
    print("- Request Headers")
    print("- Request Body (JSON payload)")
    print()
    print("File: C:\\laragon\\www\\KiroApiKey\\9router_kiro_inject.py")
    print("="*70)
