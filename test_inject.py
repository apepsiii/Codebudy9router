"""
Test Script untuk Inject Kiro Tokens ke 9Router
================================================

Script ini untuk testing inject tokens ke 9router
dan verifikasi hasilnya.

Usage:
    python test_inject.py --password YOUR_PASSWORD
"""

import urllib.request
import json
import argparse
import sys


def login_9router(router_url, password):
    """Login ke 9router dan return auth token"""
    login_url = f"{router_url}/api/auth/login"
    body = json.dumps({"password": password}).encode("utf-8")
    req = urllib.request.Request(
        login_url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        for cookie in resp.headers.get_all("Set-Cookie"):
            if cookie.startswith("auth_token="):
                return cookie.split(";")[0].split("=", 1)[1]
    except Exception as e:
        print(f"[x] Login gagal: {e}")
        return None
    
    return None


def get_kiro_connections(router_url, auth_token):
    """Get semua connection dengan provider anthropic (Kiro)"""
    providers_url = f"{router_url}/api/providers"
    req = urllib.request.Request(
        providers_url,
        headers={"Cookie": f"auth_token={auth_token}"},
    )
    
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        
        # Filter hanya Kiro tokens (@geusil.com)
        kiro_connections = []
        for conn in data.get("connections", []):
            if conn.get("provider") == "anthropic" and "@geusil.com" in conn.get("name", ""):
                kiro_connections.append(conn)
        
        return kiro_connections
    except Exception as e:
        print(f"[x] Gagal get connections: {e}")
        return []


def inject_one_token(router_url, auth_token, email, refresh_token, priority=999):
    """Inject satu token ke 9router"""
    providers_url = f"{router_url}/api/providers"
    payload = {
        "provider": "anthropic",
        "apiKey": refresh_token,
        "name": email,
        "priority": priority,
        "testStatus": "active",
        "providerSpecificData": {},
    }
    
    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Cookie": f"auth_token={auth_token}",
    }
    req = urllib.request.Request(providers_url, data=body, headers=headers, method="POST")
    
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        return {"success": True, "data": data}
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


def delete_connection(router_url, auth_token, connection_id):
    """Delete connection dari 9router"""
    delete_url = f"{router_url}/api/providers/{connection_id}"
    req = urllib.request.Request(
        delete_url,
        headers={"Cookie": f"auth_token={auth_token}"},
        method="DELETE",
    )
    
    try:
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser(description="Test Inject Kiro Tokens ke 9Router")
    parser.add_argument("--password", required=True, help="9router password")
    parser.add_argument("--router-url", default="http://localhost:20128", help="9router URL")
    parser.add_argument("--action", default="status", choices=["status", "test", "cleanup"], 
                       help="Action: status (lihat saja), test (inject test token), cleanup (hapus test tokens)")
    args = parser.parse_args()
    
    print("\n" + "=" * 70)
    print("TEST INJECT KIRO TOKENS KE 9ROUTER")
    print("=" * 70 + "\n")
    
    # Login
    print("[*] Login ke 9router...")
    auth_token = login_9router(args.router_url, args.password)
    if not auth_token:
        print("[x] Login gagal! Periksa password atau 9router status.")
        sys.exit(1)
    print("[+] Login berhasil\n")
    
    # Get existing connections
    print("[*] Mengambil daftar Kiro connections...")
    connections = get_kiro_connections(args.router_url, auth_token)
    print(f"[+] Ditemukan {len(connections)} Kiro connections\n")
    
    if args.action == "status":
        # Show status
        if connections:
            print("Daftar Kiro Tokens di 9Router:")
            print("-" * 70)
            for idx, conn in enumerate(connections, 1):
                name = conn.get("name", "unknown")
                status = conn.get("testStatus", "unknown")
                priority = conn.get("priority", 0)
                conn_id = conn.get("id", "")[:8]
                print(f"{idx:2d}. {name:30s} | Status: {status:12s} | Priority: {priority:3d} | ID: {conn_id}")
            print("-" * 70)
        else:
            print("[!] Tidak ada Kiro tokens di 9router")
        
        print(f"\n[*] Total: {len(connections)} akun Kiro")
        print(f"[*] Dashboard: {args.router_url}/dashboard/providers/anthropic")
    
    elif args.action == "test":
        # Test inject
        print("[*] Testing inject token...")
        test_email = "test-kiro@geusil.com"
        test_token = "test_refresh_token_12345:test_part2:test_part3"
        
        # Check if test token already exists
        existing = [c for c in connections if c.get("name") == test_email]
        if existing:
            print(f"[!] Test token sudah ada: {test_email}")
            print("   Gunakan --action cleanup untuk hapus test tokens\n")
        else:
            result = inject_one_token(args.router_url, auth_token, test_email, test_token, priority=9999)
            
            if result["success"]:
                print(f"[+] Test token berhasil di-inject: {test_email}")
                print(f"   Provider: anthropic")
                print(f"   Priority: 9999")
                print(f"\n   Gunakan --action cleanup untuk hapus test token\n")
            else:
                print(f"[x] Test token gagal: {result.get('error')}\n")
    
    elif args.action == "cleanup":
        # Cleanup test tokens
        print("[*] Cleanup test tokens...")
        test_connections = [c for c in connections if "test-" in c.get("name", "").lower()]
        
        if not test_connections:
            print("[+] Tidak ada test tokens untuk dihapus\n")
        else:
            deleted = 0
            for conn in test_connections:
                conn_id = conn.get("id")
                name = conn.get("name")
                if delete_connection(args.router_url, auth_token, conn_id):
                    print(f"[+] Deleted: {name}")
                    deleted += 1
                else:
                    print(f"[x] Gagal delete: {name}")
            
            print(f"\n[*] Cleanup selesai: {deleted}/{len(test_connections)} test tokens dihapus\n")
    
    print("=" * 70)
    print("SELESAI")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
