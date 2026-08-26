"""
V2Fun.ai Network Request Capture
Capture all API calls made by v2fun.ai using Playwright
"""

import asyncio
import json
from playwright.async_api import async_playwright
from datetime import datetime

# Captured requests
captured_requests = []
captured_responses = []

async def capture_network():
    print("="*60)
    print("V2Fun.ai Network Request Capture")
    print("="*60)
    print()
    print("Starting browser...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        # Request handler
        def on_request(request):
            url = request.url
            # Only log API calls
            if "api.prod.v2fun.ai" in url or "v2fun.ai/api" in url:
                info = {
                    "time": datetime.now().isoformat(),
                    "method": request.method,
                    "url": url,
                    "headers": dict(request.headers),
                    "post_data": request.post_data if request.method == "POST" else None
                }
                captured_requests.append(info)
                
                print(f"\n→ {request.method} {url}")
                if request.method == "POST" and request.post_data:
                    try:
                        data = json.loads(request.post_data)
                        print(f"  Body: {json.dumps(data, indent=2)[:200]}")
                    except:
                        print(f"  Body: {request.post_data[:100]}")
        
        # Response handler
        async def on_response(response):
            url = response.url
            # Only log API responses
            if "api.prod.v2fun.ai" in url or "v2fun.ai/api" in url:
                try:
                    body = await response.text()
                    info = {
                        "time": datetime.now().isoformat(),
                        "status": response.status,
                        "url": url,
                        "headers": dict(response.headers),
                        "body": body[:1000]  # First 1000 chars
                    }
                    captured_responses.append(info)
                    
                    print(f"← {response.status} {url}")
                    if response.status < 400:
                        try:
                            json_body = json.loads(body)
                            print(f"  Response: {json.dumps(json_body, indent=2)[:300]}")
                        except:
                            print(f"  Response: {body[:200]}")
                except Exception as e:
                    print(f"  Error reading response: {e}")
        
        # Attach listeners
        page.on("request", on_request)
        page.on("response", lambda resp: asyncio.create_task(on_response(resp)))
        
        print("\nNavigating to https://v2fun.ai/ ...")
        await page.goto("https://v2fun.ai/", wait_until="networkidle", timeout=60000)
        await asyncio.sleep(3)
        
        print("\n" + "="*60)
        print("INSTRUCTIONS:")
        print("="*60)
        print("1. Browser is open")
        print("2. Navigate through v2fun.ai:")
        print("   - Login if needed")
        print("   - Go to chat/dashboard")
        print("   - Click around different features")
        print("   - Try to start a conversation")
        print("3. All API calls will be logged here")
        print("4. Press Enter in this terminal when done")
        print("="*60)
        print()
        
        # Wait for user input
        await asyncio.to_thread(input, "Press Enter when done exploring...")
        
        print("\n" + "="*60)
        print("CAPTURE SUMMARY")
        print("="*60)
        print(f"Total Requests Captured: {len(captured_requests)}")
        print(f"Total Responses Captured: {len(captured_responses)}")
        
        # Save to file
        with open("v2fun_api_capture.json", "w", encoding="utf-8") as f:
            json.dump({
                "requests": captured_requests,
                "responses": captured_responses
            }, f, indent=2, ensure_ascii=False)
        
        print("\nSaved to: v2fun_api_capture.json")
        
        # Print unique API endpoints
        print("\n" + "="*60)
        print("DISCOVERED API ENDPOINTS:")
        print("="*60)
        
        endpoints = set()
        for req in captured_requests:
            url = req['url']
            # Extract path from URL
            if "api.prod.v2fun.ai" in url:
                path = url.split("api.prod.v2fun.ai")[1].split("?")[0]
                endpoints.add(f"{req['method']} {path}")
        
        for endpoint in sorted(endpoints):
            print(f"  {endpoint}")
        
        print("\n" + "="*60)
        print("Done! Check v2fun_api_capture.json for details")
        print("="*60)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(capture_network())
