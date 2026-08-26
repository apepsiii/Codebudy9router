"""
V2Fun.ai Token Manager
Auto-refresh JWT tokens without full browser interaction

Strategy:
1. Check token expiry before use
2. If expired (< 12h remaining), trigger headless re-login via Playwright
3. Update database with new token
4. If re-login fails, mark account for retry

Note: V2Fun.ai does NOT have a refresh token endpoint.
The JWT expires every ~3 days and must be renewed via Google OAuth.
"""

import json
import base64
import asyncio
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple


# Token is considered "expiring soon" if less than this remains
WARNING_THRESHOLD = timedelta(hours=24)
CRITICAL_THRESHOLD = timedelta(hours=6)


def decode_jwt(token: str) -> dict:
    """Decode JWT payload without verification"""
    try:
        parts = token.split('.')
        if len(parts) < 2:
            return {}
        
        payload = parts[1]
        # Add padding
        payload += '=' * (4 - len(payload) % 4)
        decoded = base64.b64decode(payload)
        return json.loads(decoded)
    except Exception:
        return {}


def get_token_expiry(token: str) -> Optional[datetime]:
    """Get expiry datetime from JWT token"""
    payload = decode_jwt(token)
    exp = payload.get('exp')
    if exp:
        return datetime.fromtimestamp(exp)
    return None


def get_time_remaining(token: str) -> timedelta:
    """Get time remaining before token expires"""
    expiry = get_token_expiry(token)
    if not expiry:
        return timedelta(0)
    
    remaining = expiry - datetime.now()
    if remaining.total_seconds() < 0:
        return timedelta(0)
    return remaining


def is_token_valid(token: str) -> bool:
    """Check if token is still valid"""
    remaining = get_time_remaining(token)
    return remaining > timedelta(minutes=5)


def is_token_expiring_soon(token: str) -> bool:
    """Check if token will expire within 24 hours"""
    remaining = get_time_remaining(token)
    return remaining < WARNING_THRESHOLD


def is_token_critical(token: str) -> bool:
    """Check if token will expire within 6 hours"""
    remaining = get_time_remaining(token)
    return remaining < CRITICAL_THRESHOLD


def get_token_status(token: str) -> str:
    """Get token status: valid, warning, critical, expired"""
    if not token:
        return "missing"
    
    remaining = get_time_remaining(token)
    
    if remaining <= timedelta(0):
        return "expired"
    elif remaining < CRITICAL_THRESHOLD:
        return "critical"
    elif remaining < WARNING_THRESHOLD:
        return "warning"
    else:
        return "valid"


async def refresh_token_headless(email: str, password: str) -> Tuple[bool, Optional[str]]:
    """
    Refresh token by running headless Google OAuth login.
    Returns (success, new_token)
    """
    from playwright.async_api import async_playwright
    from playwright_stealth import Stealth
    
    stealth = Stealth()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,  # Headless - no visible browser
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        page = await context.new_page()
        await stealth.apply_stealth_async(page)
        
        try:
            # Navigate to V2Fun
            await page.goto("https://v2fun.ai", wait_until="domcontentloaded")
            await asyncio.sleep(3)
            
            # Click login
            await page.click('button:has-text("Login"), a:has-text("Login")', timeout=5000)
            await asyncio.sleep(2)
            
            # Click Google OAuth
            await page.click('button:has-text("Continue with Google"), button:has-text("Google")', timeout=5000)
            
            # Wait for popup
            async with context.expect_page(timeout=15000) as popup_info:
                pass
            
            popup = await popup_info.value
            await popup.wait_for_load_state("domcontentloaded")
            
            # Enter email
            await asyncio.sleep(2)
            await popup.wait_for_selector('input[type="email"]', timeout=10000)
            await popup.fill('input[type="email"]', email)
            await asyncio.sleep(1)
            await popup.keyboard.press("Enter")
            
            # Enter password
            await asyncio.sleep(4)
            await popup.wait_for_selector('input[type="password"]', timeout=10000)
            await popup.fill('input[type="password"]', password)
            await asyncio.sleep(1)
            await popup.keyboard.press("Enter")
            
            # Wait for consent and redirect
            await asyncio.sleep(5)
            
            # Try consent button
            try:
                await popup.click('button:has-text("Continue"), button:has-text("Allow")', timeout=5000)
            except:
                pass
            
            # Wait for popup to close
            try:
                await popup.wait_for_event("close", timeout=20000)
            except:
                pass
            
            await asyncio.sleep(3)
            
            # Extract new token
            cookies = await context.cookies()
            for cookie in cookies:
                if cookie['name'] == 'token':
                    return True, cookie['value']
            
            return False, None
            
        except Exception as e:
            print(f"Refresh failed for {email}: {e}")
            return False, None
        finally:
            await browser.close()


def refresh_token_sync(email: str, password: str) -> Tuple[bool, Optional[str]]:
    """Sync wrapper for refresh_token_headless"""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(refresh_token_headless(email, password))
    finally:
        loop.close()


def check_and_refresh_if_needed(token: str, email: str, password: str = None) -> Tuple[str, Optional[str]]:
    """
    Check token status and refresh if needed.
    Returns (status, new_token_or_None)
    """
    status = get_token_status(token)
    
    if status in ("expired", "critical"):
        if password:
            print(f"[TOKEN] {email}: {status} - attempting headless refresh...")
            success, new_token = refresh_token_sync(email, password)
            if success and new_token:
                print(f"[TOKEN] {email}: refreshed successfully")
                return "refreshed", new_token
            else:
                print(f"[TOKEN] {email}: refresh failed")
                return "refresh_failed", None
        else:
            print(f"[TOKEN] {email}: {status} - no password for refresh")
            return status, None
    
    return status, None


def get_all_tokens_status() -> list:
    """Get status of all saved V2Fun tokens"""
    v2fun_data = Path("v2fun_data")
    session_files = list(v2fun_data.glob("v2fun_session_*_latest.json"))
    
    results = []
    for file in session_files:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        email = data.get("email")
        token = data.get("tokens", {}).get("cookie_token", "")
        
        status = get_token_status(token)
        remaining = get_time_remaining(token)
        
        results.append({
            "email": email,
            "status": status,
            "remaining": str(remaining),
            "expiry": get_token_expiry(token).isoformat() if get_token_expiry(token) else None
        })
    
    return results


if __name__ == "__main__":
    # Check all tokens
    print("="*80)
    print("V2Fun.ai Token Status Check")
    print("="*80)
    
    statuses = get_all_tokens_status()
    
    for s in statuses:
        emoji = {
            "valid": "[OK]",
            "warning": "[!]",
            "critical": "[!!]",
            "expired": "[X]",
            "missing": "[?]"
        }.get(s["status"], "[?]")
        
        print(f"{emoji} {s['email']:40} {s['status']:10} Remaining: {s['remaining']}")
