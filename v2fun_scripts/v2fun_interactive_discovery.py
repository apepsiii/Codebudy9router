"""
V2Fun.ai Interactive API Discovery
Guided manual exploration with automatic capture

Instruksi akan ditampilkan di terminal.
Ikuti setiap step, script akan capture semua API calls.
"""

import asyncio
import json
import sys
import io
from playwright.async_api import async_playwright
from datetime import datetime
import os

# Force UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Storage
captured_requests = []
captured_responses = []
important_data = {
    "registration": {},
    "login": {},
    "chat": {},
    "image_generation": {},
    "models": {},
    "endpoints": []
}

def save_progress():
    """Save captured data"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save raw capture
    with open(f"v2fun_capture_{timestamp}.json", "w", encoding="utf-8") as f:
        json.dump({
            "requests": captured_requests,
            "responses": captured_responses,
            "important_data": important_data
        }, f, indent=2, ensure_ascii=False)
    
    # Save summary
    with open("v2fun_endpoints.txt", "w", encoding="utf-8") as f:
        f.write("=== V2Fun.ai Discovered Endpoints ===\n\n")
        
        endpoints = set()
        for req in captured_requests:
            if "api.prod.v2fun.ai" in req.get("url", ""):
                method = req.get("method", "")
                url = req.get("url", "")
                path = url.split("api.prod.v2fun.ai")[1].split("?")[0] if "api.prod.v2fun.ai" in url else url
                endpoints.add(f"{method} {path}")
        
        for ep in sorted(endpoints):
            f.write(f"{ep}\n")
        
        f.write(f"\n\nTotal endpoints: {len(endpoints)}")
        f.write(f"\nTotal requests: {len(captured_requests)}")
        f.write(f"\nTotal responses: {len(captured_responses)}")

async def main():
    print("="*70)
    print("V2Fun.ai Interactive API Discovery")
    print("="*70)
    print()
    print("Script ini akan:")
    print("1. Buka browser untuk Anda")
    print("2. Monitor semua API calls")
    print("3. Berikan instruksi step-by-step")
    print("4. Capture data untuk automation")
    print()
    print("PENTING: Ikuti instruksi di terminal dengan teliti!")
    print("="*70)
    print()
    
    input("Press Enter untuk mulai...")
    print()
    
    async with async_playwright() as p:
        print("[*] Launching browser...")
        browser = await p.chromium.launch(
            headless=False,
            args=['--start-maximized']
        )
        
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        
        page = await context.new_page()
        
        # Request handler
        def on_request(request):
            url = request.url
            if "v2fun.ai" in url or "api.prod.v2fun" in url:
                try:
                    post_data = request.post_data if request.method == "POST" else None
                    
                    req_info = {
                        "time": datetime.now().isoformat(),
                        "method": request.method,
                        "url": url,
                        "headers": dict(request.headers),
                        "post_data": post_data
                    }
                    captured_requests.append(req_info)
                    
                    # Log to console
                    print(f"\n[REQ] {request.method} {url[:80]}")
                    if post_data and len(post_data) < 500:
                        print(f"      Body: {post_data[:200]}")
                except Exception as e:
                    print(f"[!] Error capturing request: {e}")
        
        # Response handler
        async def on_response(response):
            url = response.url
            if "v2fun.ai" in url or "api.prod.v2fun" in url:
                try:
                    body = await response.text()
                    
                    resp_info = {
                        "time": datetime.now().isoformat(),
                        "status": response.status,
                        "url": url,
                        "headers": dict(response.headers),
                        "body": body[:5000]  # First 5000 chars
                    }
                    captured_responses.append(resp_info)
                    
                    # Log to console
                    status_color = "OK" if response.status < 400 else "ERR"
                    print(f"[RES] {status_color} {response.status} {url[:80]}")
                    
                    # Try to parse JSON
                    if response.status < 400:
                        try:
                            json_body = json.loads(body)
                            
                            # Detect important responses
                            if "token" in body.lower() or "jwt" in body.lower():
                                print("      [!] TOKEN FOUND!")
                                important_data["login"]["response"] = json_body
                            
                            if "userid" in body.lower():
                                print("      [!] USER INFO FOUND!")
                                if not important_data["registration"].get("response"):
                                    important_data["registration"]["response"] = json_body
                            
                            if "model" in body.lower() and isinstance(json_body, list):
                                print("      [!] MODEL LIST FOUND!")
                                important_data["models"]["list"] = json_body
                            
                            if "image" in url.lower() or "generate" in url.lower():
                                print("      [!] IMAGE ENDPOINT FOUND!")
                                important_data["image_generation"]["endpoint"] = url
                                important_data["image_generation"]["response"] = json_body
                            
                            # Show snippet
                            snippet = json.dumps(json_body, indent=2, ensure_ascii=False)[:300]
                            print(f"      Data: {snippet}...")
                            
                        except:
                            if len(body) < 200:
                                print(f"      Body: {body[:200]}")
                
                except Exception as e:
                    print(f"[!] Error capturing response: {e}")
        
        # Attach handlers
        page.on("request", on_request)
        page.on("response", lambda r: asyncio.create_task(on_response(r)))
        
        print()
        print("="*70)
        print("INSTRUKSI - IKUTI STEP BY STEP")
        print("="*70)
        print()
        
        # STEP 1: Landing Page
        print("[STEP 1] LANDING PAGE")
        print("-" * 70)
        print("Script akan navigate ke v2fun.ai...")
        print()
        
        await page.goto("https://v2fun.ai/", wait_until="networkidle", timeout=60000)
        await asyncio.sleep(3)
        
        print("[OK] Halaman loaded!")
        print()
        input("Press Enter untuk lanjut ke STEP 2...")
        print()
        
        # STEP 2: Registration
        print("[STEP 2] REGISTRASI AKUN BARU")
        print("-" * 70)
        print("INSTRUKSI:")
        print("1. Cari tombol 'Sign Up' atau 'Register'")
        print("2. Klik dan isi form registrasi")
        print("3. Gunakan email: johnston7504@gezon.net (atau yang baru)")
        print("4. Submit form")
        print("5. Selesaikan verifikasi jika ada")
        print()
        print("Script akan capture semua API calls!")
        print()
        input("Press Enter SETELAH registrasi selesai...")
        print()
        
        # Save progress
        save_progress()
        print("[*] Progress saved!")
        print()
        
        # STEP 3: Dashboard/Profile
        print("[STEP 3] EXPLORE DASHBOARD")
        print("-" * 70)
        print("INSTRUKSI:")
        print("1. Buka halaman Dashboard/Home")
        print("2. Klik Profile/Settings jika ada")
        print("3. Lihat quota/usage information")
        print()
        input("Press Enter setelah explore dashboard...")
        print()
        save_progress()
        print()
        
        # STEP 4: Chat/Conversation
        print("[STEP 4] MULAI CHAT/CONVERSATION")
        print("-" * 70)
        print("INSTRUKSI:")
        print("1. Cari tombol 'New Chat' atau 'New Conversation'")
        print("2. Pilih model AI (jika ada pilihan)")
        print("3. Ketik pesan sederhana: 'Hello, how are you?'")
        print("4. Send message")
        print("5. Tunggu response")
        print()
        input("Press Enter setelah dapat response...")
        print()
        save_progress()
        print()
        
        # STEP 5: Image Generation
        print("[STEP 5] GENERATE GAMBAR")
        print("-" * 70)
        print("INSTRUKSI:")
        print("1. Cari fitur 'Image Generation' atau 'AI Art'")
        print("2. Ketik prompt: 'A beautiful sunset over mountains'")
        print("3. Klik Generate/Create")
        print("4. Tunggu sampai gambar selesai")
        print("5. JANGAN download dulu, tunggu instruksi")
        print()
        input("Press Enter setelah gambar ter-generate...")
        print()
        save_progress()
        print()
        
        # STEP 6: Download Image
        print("[STEP 6] DOWNLOAD GAMBAR")
        print("-" * 70)
        print("INSTRUKSI:")
        print("1. Klik tombol Download pada gambar yang baru dibuat")
        print("2. Save gambar ke folder Downloads")
        print()
        print("PENTING: Script akan capture download URL!")
        print()
        input("Press Enter setelah download selesai...")
        print()
        save_progress()
        print()
        
        # STEP 7: Additional Features
        print("[STEP 7] EXPLORE FITUR LAIN (OPTIONAL)")
        print("-" * 70)
        print("INSTRUKSI:")
        print("1. Explore fitur lain yang menarik:")
        print("   - Model list")
        print("   - Settings")
        print("   - History")
        print("   - Usage stats")
        print("2. Klik-klik berbagai menu")
        print()
        print("Semakin banyak yang di-explore, semakin banyak API ter-capture!")
        print()
        input("Press Enter jika sudah selesai explore...")
        print()
        
        # Final save
        save_progress()
        
        print()
        print("="*70)
        print("SUMMARY - DATA CAPTURE")
        print("="*70)
        print()
        print(f"Total Requests:  {len(captured_requests)}")
        print(f"Total Responses: {len(captured_responses)}")
        print()
        
        # Show discovered endpoints
        endpoints = set()
        for req in captured_requests:
            if "api.prod.v2fun.ai" in req.get("url", ""):
                method = req.get("method", "")
                url = req.get("url", "")
                path = url.split("api.prod.v2fun.ai")[1].split("?")[0] if "api.prod.v2fun.ai" in url else ""
                if path:
                    endpoints.add(f"{method} {path}")
        
        print("DISCOVERED ENDPOINTS:")
        print("-" * 70)
        for ep in sorted(endpoints):
            print(f"  {ep}")
        print()
        
        print("IMPORTANT DATA CAPTURED:")
        print("-" * 70)
        if important_data["registration"].get("response"):
            print("  [OK] Registration data")
        if important_data["login"].get("response"):
            print("  [OK] Login/Token data")
        if important_data["models"].get("list"):
            print("  [OK] Model list")
        if important_data["image_generation"].get("endpoint"):
            print("  [OK] Image generation endpoint")
        print()
        
        print("FILES SAVED:")
        print("-" * 70)
        print("  v2fun_capture_*.json    - Full capture data")
        print("  v2fun_endpoints.txt     - Endpoint summary")
        print()
        
        print("="*70)
        print("DONE! Anda boleh close browser.")
        print("="*70)
        print()
        input("Press Enter untuk close browser dan keluar...")
        
        await browser.close()
        
        print()
        print("[*] Analysis complete!")
        print("[*] Check files untuk detail lengkap")
        print()
        print("Next: Saya akan buat automation berdasarkan data ini!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[!] Interrupted! Saving progress...")
        save_progress()
        print("[*] Progress saved!")
    except Exception as e:
        print(f"\n\n[!] Error: {e}")
        save_progress()
        print("[*] Progress saved despite error!")
