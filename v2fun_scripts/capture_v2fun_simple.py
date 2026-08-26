"""
V2Fun.ai Network Request Capture (Simplified)
"""

import asyncio
import json
import sys
import io
from playwright.async_api import async_playwright
from datetime import datetime

# Force UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

captured = []

async def capture_network():
    print("Starting V2Fun.ai network capture...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Capture requests
        def on_request(request):
            url = request.url
            if "api.prod.v2fun.ai" in url:
                captured.append({
                    "type": "request",
                    "time": datetime.now().isoformat(),
                    "method": request.method,
                    "url": url,
                    "headers": dict(request.headers)
                })
                print(f"REQ: {request.method} {url}")
        
        # Capture responses
        async def on_response(response):
            url = response.url
            if "api.prod.v2fun.ai" in url:
                try:
                    body = await response.text()
                    captured.append({
                        "type": "response",
                        "time": datetime.now().isoformat(),
                        "status": response.status,
                        "url": url,
                        "body": body[:2000]
                    })
                    print(f"RES: {response.status} {url}")
                except:
                    pass
        
        page.on("request", on_request)
        page.on("response", lambda r: asyncio.create_task(on_response(r)))
        
        print("\nGoing to v2fun.ai...")
        await page.goto("https://v2fun.ai/", wait_until="networkidle")
        await asyncio.sleep(5)
        
        print("\nBrowser open. Explore the site, then close the browser window.")
        print("Waiting for browser to close...")
        
        # Wait for browser to close
        await page.wait_for_timeout(300000)  # 5 min max
        
        await browser.close()
    
    # Save results
    with open("v2fun_capture.json", "w", encoding="utf-8") as f:
        json.dump(captured, f, indent=2, ensure_ascii=False)
    
    print(f"\nCaptured {len(captured)} events")
    print("Saved to: v2fun_capture.json")
    
    # Print unique endpoints
    endpoints = set()
    for item in captured:
        if item["type"] == "request":
            url = item["url"]
            if "api.prod.v2fun.ai" in url:
                path = url.split("api.prod.v2fun.ai")[1].split("?")[0]
                endpoints.add(f"{item['method']} {path}")
    
    print("\nDiscovered endpoints:")
    for ep in sorted(endpoints):
        print(f"  {ep}")

asyncio.run(capture_network())
