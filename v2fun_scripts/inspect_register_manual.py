"""
V2Fun.ai Manual Registration Inspector
=======================================

Simple script untuk inspect registration flow secara manual.
Lebih mudah dikontrol dan capture hasil.
"""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright

async def inspect_v2fun_registration():
    """
    Open V2Fun.ai dan inspect registration manually
    """
    print("\n" + "="*70)
    print("V2Fun.ai Registration Manual Inspector")
    print("="*70)
    print("\nThis will:")
    print("1. Open V2Fun.ai in browser (visible)")
    print("2. Capture all network traffic")
    print("3. You manually complete registration")
    print("4. Save captured data when you're done")
    print("\n" + "="*70 + "\n")
    
    captured_data = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=100,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        
        # Capture network
        def log_request(request):
            if 'v2fun.ai' in request.url:
                info = {
                    'type': 'request',
                    'time': datetime.now().isoformat(),
                    'method': request.method,
                    'url': request.url,
                }
                
                # Only capture API calls
                if 'api' in request.url.lower():
                    captured_data.append(info)
                    print(f"\n[REQUEST] {request.method} {request.url}")
                    
                    if request.method == 'POST':
                        try:
                            post = request.post_data
                            if post:
                                print(f"[POST] {post[:200]}")
                        except:
                            pass
        
        page.on('request', log_request)
        
        print("[1/3] Opening V2Fun.ai...")
        await page.goto('https://v2fun.ai/', wait_until='domcontentloaded')
        await asyncio.sleep(2)
        
        print("[2/3] Page loaded. Browser is open.")
        print("\n" + "="*70)
        print("MANUAL ACTIONS NEEDED:")
        print("="*70)
        print("1. Look for 'Sign Up' or 'Register' or 'Get Started' button")
        print("2. Click it and observe what happens")
        print("3. Check if it's:")
        print("   - Email/password form")
        print("   - Google OAuth")
        print("   - Discord OAuth")
        print("   - Other social login")
        print("4. Complete registration process")
        print("5. Come back here and press Enter when done")
        print("="*70 + "\n")
        
        # Wait for user
        input("Press Enter when you're done with registration...")
        
        print("\n[3/3] Closing browser and saving data...")
        await browser.close()
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'v2fun_data/register_capture_{timestamp}.json'
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': timestamp,
            'total_captured': len(captured_data),
            'data': captured_data
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n[SAVED] {filename}")
    print(f"[CAPTURED] {len(captured_data)} API requests")
    
    # Summary
    if captured_data:
        print("\n" + "="*70)
        print("CAPTURED ENDPOINTS:")
        print("="*70)
        unique_urls = set()
        for item in captured_data:
            if 'url' in item:
                unique_urls.add(f"{item['method']} {item['url']}")
        
        for url in sorted(unique_urls):
            print(f"  • {url}")
    else:
        print("\n[WARNING] No API requests captured!")
        print("This might mean:")
        print("  - Registration uses OAuth (redirects to Google/Discord)")
        print("  - Registration is on different subdomain")
        print("  - Need to inspect browser DevTools manually")
    
    print("\n" + "="*70)
    print("Next steps:")
    print("1. Check the saved JSON file")
    print("2. If no API calls, open browser DevTools manually:")
    print("   - Press F12 in browser")
    print("   - Go to Network tab")
    print("   - Filter: XHR/Fetch")
    print("   - Repeat registration process")
    print("   - Look for API calls to api.prod.v2fun.ai")
    print("="*70 + "\n")

if __name__ == '__main__':
    asyncio.run(inspect_v2fun_registration())
