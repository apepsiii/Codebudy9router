"""
V2Fun.ai 3D Generation API Discovery
=====================================

Script untuk discover API endpoints 3D generation.
User perlu login manual, lalu trigger generation.
"""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright

async def discover_generation_api():
    """
    Discover 3D generation API endpoints
    """
    print("\n" + "="*70)
    print("V2Fun.ai 3D Generation API Discovery")
    print("="*70)
    print("\nThis script will:")
    print("1. Open V2Fun.ai (you login manually)")
    print("2. You trigger 3D model generation")
    print("3. Script captures all API calls")
    print("4. Save generation endpoints")
    print("\n" + "="*70 + "\n")
    
    captured_data = []
    
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
        
        # Capture network
        def log_request(request):
            url = request.url
            
            # Capture V2Fun API calls only
            if 'api.prod.v2fun.ai' in url or 'v2fun.ai/api' in url:
                data = {
                    'type': 'request',
                    'time': datetime.now().isoformat(),
                    'method': request.method,
                    'url': url,
                    'headers': {k: v for k, v in request.headers.items() 
                               if k.lower() not in ['cookie']},
                }
                
                # Capture POST data
                if request.method in ['POST', 'PUT', 'PATCH']:
                    try:
                        post_data = request.post_data
                        if post_data:
                            try:
                                data['post_data'] = json.loads(post_data)
                            except:
                                data['post_data'] = post_data[:500]
                    except:
                        pass
                
                captured_data.append(data)
                print(f"\n[{request.method}] {url}")
                if 'post_data' in data:
                    print(f"  POST: {json.dumps(data['post_data'], indent=2)[:200]}...")
        
        # Capture responses
        async def log_response(response):
            url = response.url
            if 'api.prod.v2fun.ai' in url or 'v2fun.ai/api' in url:
                try:
                    body = await response.text()
                    data = {
                        'type': 'response',
                        'time': datetime.now().isoformat(),
                        'url': url,
                        'status': response.status,
                        'headers': dict(response.headers),
                        'body': body[:1000] if body else None
                    }
                    captured_data.append(data)
                    print(f"  [{response.status}] {body[:150] if body else 'empty'}...")
                except:
                    pass
        
        page.on('request', log_request)
        page.on('response', log_response)
        
        print("[STEP 1/5] Opening V2Fun.ai...")
        await page.goto('https://v2fun.ai/', wait_until='domcontentloaded')
        await asyncio.sleep(3)
        print("[OK] Page loaded\n")
        
        print("="*70)
        print("MANUAL ACTIONS REQUIRED:")
        print("="*70)
        print("\n1. LOGIN (if not already logged in)")
        print("   - Click 'Sign In' button")
        print("   - Complete Google OAuth")
        print("   - Wait for redirect back to V2Fun\n")
        
        print("2. GENERATE 3D MODEL")
        print("   - Find 'Generate' or 'Create' button")
        print("   - Enter prompt (e.g., 'a red sports car')")
        print("   - Click Generate/Create")
        print("   - Wait for generation to start\n")
        
        print("3. OBSERVE GENERATION")
        print("   - Watch progress bar/status")
        print("   - Wait for completion (or close early)")
        print("   - Script captures all API calls\n")
        
        print("="*70)
        print("Script will run for 5 minutes (300 seconds)")
        print("You can close browser when done capturing")
        print("="*70 + "\n")
        
        # Wait 5 minutes
        wait_time = 300
        print(f"[STEP 2/5] Monitoring for {wait_time} seconds...")
        
        for remaining in range(wait_time, 0, -30):
            print(f"  Time remaining: {remaining} seconds... ({len(captured_data)} API calls captured)")
            await asyncio.sleep(30)
        
        print("\n[STEP 3/5] Time's up! Closing browser...")
        await browser.close()
    
    # Save results
    print("[STEP 4/5] Saving captured data...")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'v2fun_data/generation_api_{timestamp}.json'
    
    result = {
        'timestamp': timestamp,
        'total_captured': len(captured_data),
        'data': captured_data
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n[SAVED] {filename}")
    print(f"[STATS] Captured {len(captured_data)} API calls")
    
    # Analysis
    print("\n[STEP 5/5] Analyzing captured endpoints...")
    print("="*70)
    print("DISCOVERED ENDPOINTS:")
    print("="*70)
    
    if not captured_data:
        print("\n[WARNING] No API calls captured!")
        print("\nPossible reasons:")
        print("  • Didn't login/generate during monitoring")
        print("  • API uses WebSocket (not HTTP)")
        print("  • Need to check browser console for errors")
    else:
        # Group by URL
        endpoints = {}
        for item in captured_data:
            if 'url' in item and 'method' in item:
                key = f"{item['method']} {item['url']}"
                if key not in endpoints:
                    endpoints[key] = {'count': 0, 'sample': item}
                endpoints[key]['count'] += 1
        
        print(f"\nFound {len(endpoints)} unique endpoints:\n")
        
        # Categorize endpoints
        auth_endpoints = []
        generation_endpoints = []
        user_endpoints = []
        other_endpoints = []
        
        for endpoint, info in endpoints.items():
            if 'auth' in endpoint.lower() or 'login' in endpoint.lower():
                auth_endpoints.append((endpoint, info))
            elif 'generat' in endpoint.lower() or 'create' in endpoint.lower() or 'job' in endpoint.lower():
                generation_endpoints.append((endpoint, info))
            elif 'user' in endpoint.lower() or 'profile' in endpoint.lower():
                user_endpoints.append((endpoint, info))
            else:
                other_endpoints.append((endpoint, info))
        
        # Print by category
        if generation_endpoints:
            print("\n🎨 GENERATION ENDPOINTS (MOST IMPORTANT):")
            print("-" * 70)
            for endpoint, info in generation_endpoints:
                print(f"\n  {endpoint}")
                print(f"    Called: {info['count']} times")
                if 'post_data' in info['sample']:
                    print(f"    POST Data: {json.dumps(info['sample']['post_data'], indent=6)[:150]}...")
        
        if auth_endpoints:
            print("\n🔐 AUTHENTICATION ENDPOINTS:")
            print("-" * 70)
            for endpoint, info in auth_endpoints:
                print(f"  {endpoint} (called {info['count']}x)")
        
        if user_endpoints:
            print("\n👤 USER ENDPOINTS:")
            print("-" * 70)
            for endpoint, info in user_endpoints:
                print(f"  {endpoint} (called {info['count']}x)")
        
        if other_endpoints:
            print("\n📋 OTHER ENDPOINTS:")
            print("-" * 70)
            for endpoint, info in other_endpoints:
                print(f"  {endpoint} (called {info['count']}x)")
    
    print("\n" + "="*70)
    print("Next steps:")
    print("1. Review saved JSON file for full details")
    print("2. Look for POST endpoints with 'prompt' in body")
    print("3. Find polling endpoints (GET with job_id)")
    print("4. Check response for model download URLs")
    print("="*70 + "\n")

if __name__ == '__main__':
    asyncio.run(discover_generation_api())
