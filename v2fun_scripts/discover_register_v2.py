"""
V2Fun.ai Auto Register - Step by Step Discovery
================================================

Interactive script untuk discover registration flow.
"""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright

class V2FunRegisterDiscovery:
    def __init__(self):
        self.captured_requests = []
        self.captured_responses = []
        
    async def run_discovery(self):
        """Main discovery flow"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                ]
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            page = await context.new_page()
            
            # Setup network capture
            page.on('request', self.handle_request)
            page.on('response', self.handle_response)
            
            print("\n" + "="*70)
            print("V2Fun.ai Registration Discovery - Interactive Mode")
            print("="*70)
            
            # Step 1: Navigate to homepage
            print("\n[STEP 1] Navigating to v2fun.ai...")
            await page.goto('https://v2fun.ai/', wait_until='domcontentloaded')
            await asyncio.sleep(3)
            print("[OK] Homepage loaded")
            
            # Step 2: Look for auth buttons
            print("\n[STEP 2] Looking for authentication buttons...")
            
            # Try to find login/signup buttons
            try:
                # Check for common button selectors
                buttons = await page.query_selector_all('button, a[href*="login"], a[href*="sign"], a[href*="auth"]')
                print(f"[INFO] Found {len(buttons)} potential buttons")
                
                for i, button in enumerate(buttons[:10]):  # Check first 10
                    text = await button.inner_text()
                    if text and any(word in text.lower() for word in ['login', 'sign', 'register', 'auth', 'get started']):
                        print(f"[FOUND] Button: '{text.strip()}'")
                        
            except Exception as e:
                print(f"[ERROR] {e}")
            
            print("\n[ACTION REQUIRED]")
            print("Please manually:")
            print("1. Click on Sign Up / Register button")
            print("2. Complete the registration form")
            print("3. Press Enter in this terminal when done")
            print("="*70)
            
            # Wait for user input
            input("\nPress Enter when registration is complete...")
            
            print("\n[INFO] Closing browser...")
            await browser.close()
            
            # Save results
            self.save_results()
            self.analyze_results()
    
    def handle_request(self, request):
        """Capture API requests"""
        url = request.url
        
        # Only capture API calls
        if 'api.prod.v2fun.ai' in url or '/api/' in url:
            data = {
                'time': datetime.now().isoformat(),
                'method': request.method,
                'url': url,
                'headers': dict(request.headers),
                'post_data': request.post_data if request.method == 'POST' else None
            }
            self.captured_requests.append(data)
            print(f"\n[API REQUEST] {request.method} {url}")
            if request.method == 'POST' and request.post_data:
                try:
                    post_json = json.loads(request.post_data)
                    print(f"[POST DATA] {json.dumps(post_json, indent=2)}")
                except:
                    print(f"[POST DATA] {request.post_data[:200]}")
    
    async def handle_response(self, response):
        """Capture API responses"""
        url = response.url
        
        if 'api.prod.v2fun.ai' in url or '/api/' in url:
            try:
                body = await response.text()
                data = {
                    'time': datetime.now().isoformat(),
                    'url': url,
                    'status': response.status,
                    'headers': dict(response.headers),
                    'body': body[:1000]  # First 1KB
                }
                self.captured_responses.append(data)
                print(f"[API RESPONSE] {response.status} {url}")
                if body:
                    print(f"[BODY] {body[:200]}...")
            except Exception as e:
                print(f"[ERROR] Cannot read response: {e}")
    
    def save_results(self):
        """Save captured data"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'v2fun_data/v2fun_register_{timestamp}.json'
        
        data = {
            'timestamp': timestamp,
            'total_requests': len(self.captured_requests),
            'total_responses': len(self.captured_responses),
            'requests': self.captured_requests,
            'responses': self.captured_responses
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n[SAVED] {filename}")
        print(f"[STATS] Captured {len(self.captured_requests)} requests, {len(self.captured_responses)} responses")
    
    def analyze_results(self):
        """Analyze captured endpoints"""
        print("\n" + "="*70)
        print("ANALYSIS - Discovered Endpoints")
        print("="*70)
        
        if not self.captured_requests:
            print("[WARNING] No API requests captured!")
            print("\nPossible reasons:")
            print("1. Registration uses OAuth (Google, Discord, etc.)")
            print("2. Registration happens on different domain")
            print("3. Need to complete full registration flow")
            return
        
        # Group by method
        endpoints = {}
        for req in self.captured_requests:
            key = f"{req['method']} {req['url']}"
            if key not in endpoints:
                endpoints[key] = {
                    'count': 0,
                    'post_data': req.get('post_data')
                }
            endpoints[key]['count'] += 1
        
        print("\nDiscovered Endpoints:")
        for endpoint, info in sorted(endpoints.items()):
            print(f"\n  {endpoint}")
            print(f"    Called: {info['count']} times")
            if info['post_data']:
                print(f"    POST Data: {info['post_data'][:100]}...")
        
        print("\n" + "="*70)

async def main():
    discovery = V2FunRegisterDiscovery()
    await discovery.run_discovery()

if __name__ == '__main__':
    asyncio.run(main())
