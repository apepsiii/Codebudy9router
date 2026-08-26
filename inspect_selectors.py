"""
CodeBuddy Selector Inspector
Inspect selectors di CodeBuddy.ai untuk update main_codebuddy.py
"""

import asyncio
import sys
import io
from playwright.async_api import async_playwright

# Force UTF-8 encoding for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

CODEBUDDY_HOME = "https://www.codebuddy.ai/home"

async def inspect_selectors():
    print("Inspecting CodeBuddy.ai selectors...")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        # 1. Navigate to home page
        print(f"\n1. Navigating to {CODEBUDDY_HOME}...")
        await page.goto(CODEBUDDY_HOME, wait_until="load", timeout=60000)
        await asyncio.sleep(3)
        
        # 2. Check for Login button
        print("\n2. Looking for Login button...")
        login_selectors = [
            'button:has-text("Login")',
            'a:has-text("Login")',
            'button:has-text("Log in")',
            'a:has-text("Log in")',
            'button:has-text("Sign in")',
            'a:has-text("Sign in")',
            '[data-testid="login-button"]',
            'a[href*="login"]',
            '.login-button',
        ]
        
        found_login = False
        for sel in login_selectors:
            try:
                btn = page.locator(sel).first
                if await btn.count() > 0:
                    is_visible = await btn.is_visible()
                    if is_visible:
                        text = await btn.inner_text()
                        print(f"   ✅ FOUND: {sel}")
                        print(f"      Text: {text}")
                        found_login = True
                        
                        # Try to click
                        print(f"      Clicking...")
                        await btn.click()
                        await asyncio.sleep(3)
                        break
            except Exception as e:
                continue
        
        if not found_login:
            print("   X Login button NOT FOUND!")
            print("   Manual inspection needed.")
            input("   Press Enter after you manually click login button...")
        
        # 3. Check for "I confirm" checkbox
        print("\n3. Looking for 'I confirm' checkbox...")
        checkbox_selectors = [
            'input[type="checkbox"]',
            '[data-testid="confirm-checkbox"]',
            'input[name="confirm"]',
            '.checkbox input',
        ]
        
        found_checkbox = False
        for sel in checkbox_selectors:
            try:
                cb = page.locator(sel).first
                if await cb.count() > 0:
                    is_visible = await cb.is_visible()
                    if is_visible:
                        print(f"   OK FOUND: {sel}")
                        found_checkbox = True
                        break
            except Exception:
                continue
        
        if not found_checkbox:
            print("   ! Checkbox not found or not visible yet")
        
        # 4. Check for "Sign up with Google" button
        print("\n4. Looking for 'Sign up with Google' button...")
        google_selectors = [
            'button:has-text("Sign up with Google")',
            'button:has-text("Continue with Google")',
            'button:has-text("Sign in with Google")',
            'a:has-text("Sign up with Google")',
            '[data-testid="google-signup"]',
        ]
        
        found_google = False
        for sel in google_selectors:
            try:
                btn = page.locator(sel).first
                if await btn.count() > 0:
                    is_visible = await btn.is_visible()
                    if is_visible:
                        text = await btn.inner_text()
                        print(f"   OK FOUND: {sel}")
                        print(f"      Text: {text}")
                        found_google = True
                        break
            except Exception:
                continue
        
        if not found_google:
            print("   ! Google button not found or not visible")
        
        # 5. Get page HTML for manual inspection
        print("\n5. Saving page HTML for manual inspection...")
        html_content = await page.content()
        with open("codebuddy_page.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("   OK Saved to codebuddy_page.html")
        
        # 6. Wait for manual inspection
        print("\n" + "=" * 60)
        print("MANUAL INSPECTION MODE")
        print("=" * 60)
        print("Browser will stay open for manual inspection.")
        print("You can:")
        print("  1. Use DevTools (F12) to inspect elements")
        print("  2. Test the flow manually")
        print("  3. Note down correct selectors")
        print("\nPress Enter when done...")
        input()
        
        await browser.close()
        
    print("\nOK Inspection complete!")
    print("Update main_codebuddy.py with correct selectors.")

if __name__ == "__main__":
    asyncio.run(inspect_selectors())
