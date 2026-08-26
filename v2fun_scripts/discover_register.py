"""
V2Fun.ai Auto Register Script
===============================

Manual discovery untuk capture registration flow.

Step:
1. Buka v2fun.ai dengan Playwright
2. Klik button Sign Up / Register
3. Capture semua network requests
4. Identifikasi endpoint dan payload
5. Implement automation
"""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright

try:
    from playwright_stealth import stealth_async
    HAS_STEALTH = True
except ImportError:
    HAS_STEALTH = False
    print("[WARNING] playwright_stealth not available, running without stealth mode")

async def discover_registration_flow():
    """
    Discover registration flow V2Fun.ai
    """
    captured_requests = []
    
    async with async_playwright() as p:
        # Launch browser (visible untuk observasi)
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage',
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        if HAS_STEALTH:
            await stealth_async(page)
        
        # Capture network requests
        def handle_request(request):
            if 'api.prod.v2fun.ai' in request.url or 'v2fun.ai/api' in request.url:
                captured_requests.append({
                    'time': datetime.now().isoformat(),
                    'method': request.method,
                    'url': request.url,
                    'headers': dict(request.headers),
                    'post_data': request.post_data if request.method == 'POST' else None
                })
                print(f"[{request.method}] {request.url}")
        
        page.on('request', handle_request)
        
        print("\n[INFO] Navigating to v2fun.ai...")
        await page.goto('https://v2fun.ai/', wait_until='networkidle')
        await asyncio.sleep(3)
        
        print("\n[INFO] Looking for Sign Up / Login button...")
        print("[INFO] Please manually click on Sign Up/Register button in the browser")
        print("[INFO] Then go through the registration process")
        print("[INFO] Press Ctrl+C when done to save captured requests")
        
        try:
            # Wait for user to complete registration manually
            await asyncio.sleep(300)  # 5 minutes timeout
        except KeyboardInterrupt:
            print("\n[INFO] User interrupted. Saving captured requests...")
        
        await browser.close()
    
    # Save captured requests
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'v2fun_data/v2fun_register_capture_{timestamp}.json'
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({'requests': captured_requests}, f, indent=2, ensure_ascii=False)
    
    print(f"\n[SUCCESS] Captured {len(captured_requests)} requests")
    print(f"[SUCCESS] Saved to: {filename}")
    
    # Analyze captured requests
    print("\n[ANALYSIS] API Endpoints Found:")
    api_endpoints = set()
    for req in captured_requests:
        if req['method'] in ['POST', 'PUT', 'PATCH']:
            api_endpoints.add(f"{req['method']} {req['url']}")
    
    for endpoint in sorted(api_endpoints):
        print(f"  - {endpoint}")
    
    return captured_requests

if __name__ == '__main__':
    print("="*70)
    print("V2Fun.ai Registration Flow Discovery")
    print("="*70)
    print("\nThis script will:")
    print("1. Open V2Fun.ai in a visible browser")
    print("2. Wait for you to manually complete registration")
    print("3. Capture all API requests during the process")
    print("4. Save the data for analysis")
    print("\nPress Ctrl+C when registration is complete")
    print("="*70 + "\n")
    
    asyncio.run(discover_registration_flow())
