"""
V2Fun.ai Registration Flow Capture
===================================

Capture registration flow dengan timer otomatis.
"""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright

async def capture_registration_flow():
    """
    Capture V2Fun.ai registration flow
    """
    print("\n" + "="*70)
    print("V2Fun.ai Registration Flow Capture")
    print("="*70)
    print("\nScript will:")
    print("1. Open V2Fun.ai in browser")
    print("2. Wait 120 seconds (2 minutes) for you to register")
    print("3. Capture all API calls")
    print("4. Save results automatically")
    print("\n" + "="*70 + "\n")
    
    captured_requests = []
    captured_responses = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=50,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        
        # Capture requests
        def log_request(request):
            url = request.url
            if 'api' in url.lower() or 'auth' in url.lower():
                data = {
                    'type': 'request',
                    'time': datetime.now().isoformat(),
                    'method': request.method,
                    'url': url,
                    'headers': {k: v for k, v in request.headers.items() if k.lower() not in ['cookie', 'authorization']},
                }
                
                # Get POST data if available
                if request.method == 'POST':
                    try:
                        post_data = request.post_data
                        if post_data:
                            # Try to parse as JSON
                            try:
                                data['post_data'] = json.loads(post_data)
                            except:
                                data['post_data'] = post_data[:500]
                    except:
                        pass
                
                captured_requests.append(data)
                print(f"\n[{request.method}] {url}")
                if 'post_data' in data:
                    print(f"  POST: {str(data['post_data'])[:100]}...")
        
        # Capture responses
        async def log_response(response):
            url = response.url
            if 'api' in url.lower() or 'auth' in url.lower():
                try:
                    body = await response.text()
                    data = {
                        'type': 'response',
                        'time': datetime.now().isoformat(),
                        'url': url,
                        'status': response.status,
                        'body': body[:500] if body else None
                    }
                    captured_responses.append(data)
                    print(f"  [{response.status}] Response: {body[:100] if body else 'empty'}...")
                except:
                    pass
        
        page.on('request', log_request)
        page.on('response', log_response)
        
        print("[STEP 1/4] Opening V2Fun.ai...")
        await page.goto('https://v2fun.ai/', wait_until='domcontentloaded')
        await asyncio.sleep(3)
        print("[OK] Page loaded\n")
        
        print("="*70)
        print("MANUAL REGISTRATION INSTRUCTIONS:")
        print("="*70)
        print("1. Look for 'Sign Up' / 'Register' / 'Get Started' button")
        print("2. Click it")
        print("3. Complete registration (email, Google, Discord, etc.)")
        print("4. Script will capture all API calls automatically")
        print("5. Wait until timer expires (120 seconds)")
        print("="*70 + "\n")
        
        # Wait with countdown
        wait_time = 120
        print(f"[STEP 2/4] Waiting {wait_time} seconds for registration...")
        
        for remaining in range(wait_time, 0, -10):
            print(f"  Time remaining: {remaining} seconds...")
            await asyncio.sleep(10)
        
        print("\n[STEP 3/4] Time's up! Closing browser...")
        await browser.close()
    
    # Save results
    print("[STEP 4/4] Saving captured data...")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'v2fun_data/register_flow_{timestamp}.json'
    
    result = {
        'timestamp': timestamp,
        'total_requests': len(captured_requests),
        'total_responses': len(captured_responses),
        'requests': captured_requests,
        'responses': captured_responses
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n[SAVED] {filename}")
    print(f"[STATS] Captured {len(captured_requests)} requests, {len(captured_responses)} responses")
    
    # Analysis
    print("\n" + "="*70)
    print("ANALYSIS - Discovered Endpoints:")
    print("="*70)
    
    if not captured_requests:
        print("\n[WARNING] No API requests captured!")
        print("\nPossible reasons:")
        print("  • Registration uses OAuth redirect (Google, Discord)")
        print("  • Need to check browser DevTools manually")
        print("  • Registration on different domain")
    else:
        # Group endpoints
        endpoints = {}
        for req in captured_requests:
            key = f"{req['method']} {req['url']}"
            if key not in endpoints:
                endpoints[key] = {'count': 0, 'sample': req}
            endpoints[key]['count'] += 1
        
        print(f"\nFound {len(endpoints)} unique endpoints:\n")
        for endpoint, info in sorted(endpoints.items()):
            print(f"  {endpoint}")
            print(f"    Called: {info['count']} times")
            if 'post_data' in info['sample']:
                print(f"    Sample POST: {str(info['sample']['post_data'])[:80]}...")
            print()
    
    print("="*70)
    print("\nNext steps:")
    print("1. Review the saved JSON file")
    print("2. If OAuth is used, check redirect URLs")
    print("3. Look for /auth, /login, /register endpoints")
    print("4. Identify token storage (cookies, localStorage)")
    print("="*70 + "\n")

if __name__ == '__main__':
    asyncio.run(capture_registration_flow())
