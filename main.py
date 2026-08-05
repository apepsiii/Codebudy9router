"""
===========================================
  Kiro Refresh Token Bot v1.0
===========================================

Menggunakan Playwright + playwright-stealth
untuk login/register via Google OAuth di Kiro
(kiro-prod-us-east-1.auth.us-east-1.amazoncognito.com)
dan mengambil refresh token.

SETUP:
  1. pip install playwright playwright-stealth rich
  2. playwright install chromium
  3. Buat file account.txt (format: email:password)
  4. python kiro.py [jumlah] [workers]

Output: account.json (log semua akun + refresh token)
        kiro_tokens.txt (format: email:refresh_token)

MODE:
  (default)  Mode login (akun Kiro yang sudah terdaftar)
  --register Mode register (akun Kiro baru via Google)
  --list     List akun dari account.json
  --inject-9router  Inject refresh token ke 9router
  --inject-from-file  Inject dari file kiro_tokens.txt ke 9router

Contoh:
  python kiro.py                        # Semua akun, login mode
  python kiro.py 10 4                   # 10 akun, 4 workers
  python kiro.py 10 4 --register        # 10 akun, register mode
  python kiro.py --list                # List akun di account.json
  python kiro.py 10 4 --inject-9router --router-password MyPass123
  python kiro.py --inject-from-file kiro_tokens.txt --router-password MyPass123
"""

import asyncio
import os
import sys
import io
import time
import json
import argparse
import urllib.request
import urllib.error
from typing import Optional
from datetime import datetime
from collections import deque

from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# Rich
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.live import Live
    from rich.table import Table
    from rich.text import Text as RichText
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    RichText = None

console = Console(highlight=False, force_terminal=True) if HAS_RICH else None

# Force UTF-8 for Windows terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Log buffer
_log_buffer: deque = deque(maxlen=10)
_live_mode: bool = False

# Config
WORKSPACE = os.path.dirname(os.path.abspath(__file__))

KIRO_LANDING_URL = "https://kiro.dev/"
KIRO_SIGNIN_URL = "https://app.kiro.dev/signin"
KIRO_AUTH_DOMAIN = "kiro-prod-us-east-1.auth.us-east-1.amazoncognito.com"
KIRO_APP_DOMAIN = "app.kiro.dev"

BROWSER_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-extensions",
    "--disable-background-networking",
    "--disable-sync",
    "--no-first-run",
    "--autoplay-policy=no-user-gesture-required",
    "--disable-infobars",
    "--disable-component-update",
    "--disable-default-apps",
    "--no-default-browser-check",
    "--disable-gpu",
    "--disable-datasaver",
    "--disable-ipc-flooding-protection",
    "--lang=en-US,en",
    "--disable-background-timer-throttling",
    "--disable-backgrounding-occluded-windows",
    "--disable-renderer-backgrounding",
    "--disable-features=IsolateOrigins,site-per-process",
    "--disable-site-isolation-trials",
    "--disable-features=ImprovedCookieControls,LazyFrameLoading,GlobalMediaControls,DestroyProfileOnBrowserClose,MediaRouter,DialMediaRouteProvider,AcceptCHFrame,AutoExpandDetailsElement,CertificateTransparencyComponentUpdater,AvoidUnnecessaryBeforeUnloadCheckSync",
    # Extra stealth flags
    "--window-size=1920,1080",
    "--start-maximized",
    "--disable-blink-features=AutomationControlled",
    "--excludeSwitches=enable-automation",
    "--disable-logging",
    "--log-level=3",
    "--silent",
]

BANNER = "[bold bright_magenta]Kiro Refresh Token Bot v1.0[/] [dim]| Playwright + Stealth | Cognito OAuth[/]"


# ── Print helpers ───────────────────────────────────────
def fast_print(text, style=None):
    if _live_mode:
        _log_buffer.append((text, style))
    elif console:
        console.print(text, style=style)
    else:
        print(text)


def step(icon, text, detail=""):
    msg = f"  {icon}  {text}"
    if detail:
        msg += f"  ({detail})"
    fast_print(msg)


def ok(text):
    fast_print(f"  [bold green]+[/]  {text}", style="bold green")


def fail(text):
    fast_print(f"  [bold red]x[/]  {text}", style="bold red")


def info(text):
    fast_print(f"  [dim]>[/]  {text}", style="bright_blue")


def rule(char="─", width=60):
    if not _live_mode:
        fast_print(f"  {char * width}", style="dim")


def print_banner():
    if console:
        console.print(Panel(BANNER, border_style="bright_magenta", padding=(0, 0)))
    else:
        print(BANNER)


def get_public_ip():
    services = [
        ("https://api.ipify.org?format=json", lambda d: d.get("ip", "Unknown")),
        ("https://httpbin.org/ip", lambda d: d.get("origin", "Unknown")),
        ("https://ipinfo.io/json", lambda d: d.get("ip", "Unknown")),
    ]
    for url, parser in services:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read())
                return parser(data)
        except Exception:
            continue
    return "Unknown"


# ── Token Capture (Network Interception) ─────────────────
class TokenCapture:
    """
    Intercept Cognito /oauth2/token responses dan simpan refresh token.
    Juga menyediakan fallback via localStorage, URL hash, dan cookies.
    """

    def __init__(self):
        self.refresh_token: Optional[str] = None
        self.access_token: Optional[str] = None
        self.id_token: Optional[str] = None
        self._found = asyncio.Event()

    async def on_response(self, response):
        url = response.url
        try:
            if "/oauth2/token" in url and response.status == 200:
                try:
                    body = await response.json()
                except Exception:
                    return
                if not isinstance(body, dict):
                    return
                rt = body.get("refresh_token")
                if rt:
                    self.refresh_token = rt
                    self.access_token = body.get("access_token")
                    self.id_token = body.get("id_token")
                    self._found.set()
        except Exception:
            pass

    def attach(self, context):
        def _on_response(resp):
            if "/oauth2/token" not in resp.url or resp.status != 200:
                return
            asyncio.ensure_future(self.on_response(resp))
        context.on("response", _on_response)

    async def wait(self, timeout: float = 120) -> bool:
        try:
            await asyncio.wait_for(self._found.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False


async def get_tokens_from_localstorage(page) -> dict:
    """Ambil Cognito tokens dari localStorage - optimized version."""
    try:
        return await page.evaluate("""() => {
            const tokens = {};
            const keys = Object.keys(localStorage);
            
            // Single pass through all keys with early exit when all tokens found
            for (const key of keys) {
                const lower = key.toLowerCase();
                
                // Check both lowercase and dot notation in one pass
                if (!tokens.refresh_token && (lower.includes('refreshtoken') || key.includes('.refreshToken'))) {
                    tokens.refresh_token = localStorage.getItem(key);
                }
                if (!tokens.access_token && (lower.includes('accesstoken') || key.includes('.accessToken')) && !lower.includes('refresh')) {
                    tokens.access_token = localStorage.getItem(key);
                }
                if (!tokens.id_token && (lower.includes('idtoken') || key.includes('.idToken')) && !lower.includes('refresh')) {
                    tokens.id_token = localStorage.getItem(key);
                }
                
                // Early exit if all tokens found
                if (tokens.refresh_token && tokens.access_token && tokens.id_token) {
                    break;
                }
            }
            return tokens;
        }""")
    except Exception:
        return {}


async def get_token_from_url_hash(page) -> Optional[str]:
    """Cek URL hash untuk refresh_token (implicit grant flow)."""
    try:
        url = page.url
        if "#" in url:
            fragment = url.split("#", 1)[1]
            params = {}
            for pair in fragment.split("&"):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    params[k] = v
            return params.get("refresh_token")
    except Exception:
        pass
    return None


async def get_token_from_cookies(context) -> Optional[str]:
    """Cek cookies untuk refresh token."""
    try:
        cookies = await context.cookies()
        for cookie in cookies:
            name = cookie.get("name", "").lower()
            if "refresh" in name and cookie.get("value"):
                return cookie["value"]
    except Exception:
        pass
    return None


async def capture_refresh_token(page, context, token_capture: TokenCapture, timeout: float = 120) -> Optional[str]:
    """
    Coba berbagai strategi untuk mendapatkan refresh token.
    1. localStorage (default - paling cepat)
    2. Network interception (fallback)
    3. URL hash
    4. Cookies
    """
    # Strategy 1: localStorage (default - lebih cepat daripada network interception)
    step("> ", "Mengambil refresh token dari localStorage...")
    deadline = time.time() + 30  # 30 detik untuk localStorage
    while time.time() < deadline:
        tokens = await get_tokens_from_localstorage(page)
        if tokens.get("refresh_token"):
            step("[green]>[/]", "Refresh token via localStorage!", "ok")
            # Simpan juga token lainnya
            if tokens.get("access_token"):
                token_capture.access_token = tokens["access_token"]
            if tokens.get("id_token"):
                token_capture.id_token = tokens["id_token"]
            return tokens["refresh_token"]
        await asyncio.sleep(1)  # Polling lebih cepat: 1 detik

    # Strategy 2: Network interception (fallback jika localStorage gagal)
    step("> ", "Fallback: menunggu refresh token via network interception...")
    found = await token_capture.wait(timeout=min(timeout - 30, 30))
    if found and token_capture.refresh_token:
        step("[green]>[/]", "Refresh token via network interception!", "ok")
        return token_capture.refresh_token

    # Strategy 3: URL hash
    step("> ", "Coba ambil dari URL hash...")
    rt = await get_token_from_url_hash(page)
    if rt:
        step("[green]>[/]", "Refresh token via URL hash!", "ok")
        return rt

    # Strategy 4: Cookies
    step("> ", "Coba ambil dari cookies...")
    rt = await get_token_from_cookies(context)
    if rt:
        step("[green]>[/]", "Refresh token via cookies!", "ok")
        return rt

    return None


# ── Account Reader ──────────────────────────────────────
def read_accounts(file_path):
    accounts = []
    if not os.path.exists(file_path):
        return accounts
    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" not in line:
                step("!", f"Line {line_num}: format salah, skip")
                continue
            email, password = line.split(":", 1)
            email, password = email.strip(), password.strip()
            if email and password:
                accounts.append((email, password))
    return accounts


# ── Robust Page Load Helpers ─────────────────────────────
async def goto_robust(page, url, desc="halaman", max_retries=3, timeout=120000):
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            step("> ", f"Navigasi ke {desc}...", f"attempt {attempt}/{max_retries}")
            # Gunakan 'load' untuk SPA yang butuh JS execution
            await page.goto(url, wait_until="load", timeout=timeout)
            
            # Tunggu networkidle untuk memastikan semua resource loaded
            try:
                await page.wait_for_load_state("networkidle", timeout=30000)
            except Exception:
                step("!", f"{desc} networkidle timeout, tunggu manual...")
                await asyncio.sleep(5)
            
            # Tunggu DOM ready
            try:
                await page.wait_for_load_state("domcontentloaded", timeout=10000)
            except Exception:
                pass
            
            # Extra wait untuk SPA render
            await asyncio.sleep(3)
            
            # Validasi halaman tidak blank
            try:
                body_text = await page.evaluate("document.body ? document.body.innerText.trim().length : 0")
                if body_text < 20:
                    step("!", f"{desc} blank ({body_text} chars), retry...")
                    if attempt < max_retries:
                        await asyncio.sleep(5)
                        continue
                step("> ", f"{desc} loaded ({body_text} chars)", "ok")
            except Exception:
                pass
            
            return True
        except Exception as e:
            step("!", f"{desc} gagal: {e}", f"retry {attempt}/{max_retries}")
            last_error = e
            if attempt < max_retries:
                await asyncio.sleep(5)
    raise last_error or Exception(f"Gagal load {desc} setelah {max_retries}x retry")


async def wait_for_page_ready(page, desc="halaman", timeout=60000):
    try:
        await page.wait_for_load_state("networkidle", timeout=timeout)
        step("> ", f"{desc} network idle ok")
    except Exception:
        step("!", f"{desc} network idle timeout, lanjut...")
    blank_count = 0
    for attempt in range(1, 6):
        try:
            body_text = await page.evaluate(
                "document.body ? document.body.innerText.trim().length : 0"
            )
        except Exception:
            body_text = 0
        if body_text > 20:
            step("> ", f"{desc} konten siap ({body_text} chars)", f"attempt {attempt}")
            return True
        blank_count += 1
        if blank_count >= 2:
            step("!", f"{desc} blank 2x, reload...", f"attempt {attempt}/5")
            try:
                await page.reload(wait_until="load", timeout=60000)
                await asyncio.sleep(2)
            except Exception:
                pass
            blank_count = 0
        else:
            await asyncio.sleep(3)
    try:
        body_text = await page.evaluate(
            "document.body ? document.body.innerText.trim().length : 0"
        )
    except Exception:
        body_text = 0
    if body_text < 20:
        raise Exception(f"{desc} blank setelah 5x retry! ({body_text} chars)")
    return True


# ── Captcha Detection ───────────────────────────────────
async def detect_captcha(page):
    try:
        return await page.evaluate("""() => {
        const turnstileFrame = document.querySelector(
            'iframe[src*="turnstile"], iframe[src*="challenges.cloudflare"], iframe[src*="captcha"]'
        );
        if (turnstileFrame) return true;
        const widget = document.querySelector(
            '[id*="turnstile"], [class*="turnstile"], .cf-turnstile'
        );
        if (widget) return true;
        const challenge = document.querySelector(
            '#challenge-stage, #challenge-running, #challenge-form, .cf-challenge'
        );
        if (challenge) return true;
        const input = document.querySelector('input[name="cf-turnstile-response"]');
        if (input) return true;
        const bodyText = document.body ? document.body.innerText : '';
        if (bodyText.includes('Verify you are human') ||
            bodyText.includes('Checking your browser') ||
            bodyText.includes('Just a moment') ||
            bodyText.includes('Verif')) {
            return true;
        }
        return false;
    }""")
    except Exception:
        return False


async def wait_for_captcha_or_continue(page, timeout=180):
    has_captcha = await detect_captcha(page)
    if not has_captcha:
        return True
    fast_print(
        "\n  [bold yellow]![/]  CAPTCHA / TURNSTILE TERDETEKSI!\n"
        "  [bold yellow]![/]  Silakan solve captcha secara MANUAL di browser.\n"
        "  [bold yellow]![/]  Script otomatis melanjutkan setelah captcha selesai.\n",
        style="bold bright_yellow",
    )
    start = time.time()
    last_check = 0
    while (time.time() - start) < timeout:
        elapsed = int(time.time() - start)
        if elapsed - last_check >= 2:
            last_check = elapsed
            still_captcha = await detect_captcha(page)
            if not still_captcha:
                fast_print(f"  [bold green]+[/]  Captcha selesai! ({elapsed}s)\n", style="bold green")
                await asyncio.sleep(3)
                return True
            if elapsed > 0 and elapsed % 15 == 0:
                remaining = timeout - elapsed
                fast_print(f"  [yellow]...[/]  Menunggu captcha... ({elapsed}s, {remaining}s tersisa)", style="bright_yellow")
        await asyncio.sleep(1)
    fast_print("\n  [bold red]![/]  Timeout captcha! Mencoba melanjutkan...\n", style="bold red")
    return False


# ── Google Login Handler ────────────────────────────────
async def handle_google_login(page, email, password):
    """Handle seluruh flow login Google OAuth (adaptasi dari main.py)."""

    step("> ", "Menunggu halaman Google...")
    await page.wait_for_url("**/accounts.google.com/**", timeout=60000)
    await asyncio.sleep(2)

    # Email input
    email_input = page.locator('#identifierId')
    has_email_input = await email_input.count() > 0 and await email_input.first.is_visible()

    if not has_email_input:
        email_input = page.locator('input[type="email"]')
        has_email_input = await email_input.count() > 0 and await email_input.first.is_visible()

    if not has_email_input:
        # Account Chooser
        step("> ", "Account chooser, klik 'Use another account'...")
        use_other = None
        for text in ["Use another account", "Gunakan akun lain"]:
            el = page.locator(f'div[role="link"]:has-text("{text}"), li:has-text("{text}")').first
            if await el.count() > 0:
                use_other = el
                break
        if use_other:
            await use_other.click()
            step("> ", "Klik 'Use another account'", "check")
        else:
            items = page.locator('li, div[role="link"]')
            if await items.count() > 0:
                await items.last.click()
        await asyncio.sleep(1.5)
        email_input = page.locator('#identifierId')
        try:
            await email_input.first.wait_for(state="visible", timeout=10000)
        except Exception:
            email_input = page.locator('input[type="email"]')
            if await email_input.count() == 0 or not await email_input.first.is_visible():
                password_input = page.locator('input[name="Passwd"]')
                if await password_input.count() > 0 and await password_input.first.is_visible():
                    step("[yellow]...[/]", "Langsung ke password...")
                else:
                    raise Exception("Email input dan password input tidak ditemukan")

    # Isi Email dengan human-like typing
    step("> ", f"Memasukkan email: {email}")
    email_input = page.locator('#identifierId')
    if await email_input.count() == 0:
        email_input = page.locator('input[type="email"]')
    if await email_input.count() > 0 and await email_input.first.is_visible():
        await email_input.first.click()
        await asyncio.sleep(0.3 + (0.1 * (hash(email) % 5)))  # Random delay 0.3-0.8s
        # Type char by char untuk lebih human-like
        await email_input.first.type(email, delay=50 + (hash(email) % 50))  # 50-100ms per char
        await asyncio.sleep(0.4 + (0.1 * (hash(email) % 3)))

        step("> ", "Klik Next (email)...")
        next_btn = page.locator('#identifierNext')
        if await next_btn.count() > 0:
            await next_btn.click()
        else:
            await page.locator('span:text-is("Next")').first.click()
        await asyncio.sleep(3 + (0.5 * (hash(email) % 3)))  # Random delay 3-4.5s

        error_el = page.locator('.o6cuMc, .dEOOab, [data-error="true"]')
        if await error_el.count() > 0:
            err_text = await error_el.first.inner_text()
            if "find" in err_text.lower() or "tidak dapat menemukan" in err_text.lower():
                raise Exception(f"Google error: {err_text}")

    # Isi Password dengan human-like typing
    step("> ", "Memasukkan password...")
    password_input = page.locator('input[name="Passwd"]')
    if await password_input.count() == 0:
        password_input = page.locator('input[type="password"]')

    try:
        await password_input.first.wait_for(state="visible", timeout=15000)
    except Exception:
        err = await page.text_content(".o6cuMc, .dEOOab") or "Password field tidak muncul"
        raise Exception(f"Google error: {err}")

    await password_input.first.click()
    await asyncio.sleep(0.3 + (0.1 * (hash(password) % 4)))  # Random delay
    # Type char by char untuk lebih human-like
    await password_input.first.type(password, delay=40 + (hash(password) % 60))  # 40-100ms per char
    await asyncio.sleep(0.4 + (0.1 * (hash(password) % 3)))

    step("> ", "Klik Next (password)...")
    next_btn = page.locator('#passwordNext')
    if await next_btn.count() > 0:
        await next_btn.click()
    else:
        await page.locator('span:text-is("Next")').first.click()
    await asyncio.sleep(2 + (0.5 * (hash(password) % 4)))  # Random delay 2-4s

    # Handle "I understand" + "Continue" untuk akun GSuite baru
    step("> ", "Mengecek halaman interstitial GSuite...")
    await asyncio.sleep(1)
    i_understand_btn = page.locator('span:text-is("I understand")')
    if await i_understand_btn.count() > 0 and await i_understand_btn.first.is_visible():
        step("[cyan]>[/]", "Klik 'I understand'...")
        try:
            await i_understand_btn.first.click(force=True, timeout=5000)
        except Exception:
            try:
                await i_understand_btn.first.evaluate("el => el.click()")
            except Exception:
                pass
        await asyncio.sleep(1.5)
        continue_btn = page.locator('span:text-is("Continue")')
        if await continue_btn.count() > 0 and await continue_btn.first.is_visible():
            step("[cyan]>[/]", "Klik 'Continue'...")
            try:
                await continue_btn.first.click(force=True, timeout=5000)
            except Exception:
                try:
                    await continue_btn.first.evaluate("el => el.click()")
                except Exception:
                    pass
            await asyncio.sleep(2)

    # Handle phone verification
    await asyncio.sleep(1)
    current_url = page.url
    if "challenge" in current_url or "signin/v2" in current_url:
        await wait_for_page_ready(page, desc="Google challenge", timeout=30000)
        body_text = ""
        try:
            body_text = await page.evaluate("document.body ? document.body.innerText : ''")
        except Exception:
            body_text = ""
        phone_keywords = [
            "phone number", "nomor telepon", "verify your phone",
            "add a recovery phone", "verifikasi nomor", "telepon",
            "text message", "sms", "verification code",
        ]
        if any(kw in body_text.lower() for kw in phone_keywords):
            step("!", "Halaman verifikasi nomor HP terdeteksi!")
            fast_print(
                "  [bold yellow]![/]  Akun Google meminta verifikasi nomor HP.\n"
                "  [bold yellow]![/]  Solve MANUAL di browser (timeout 180s).\n",
                style="bold bright_yellow",
            )
            start_pv = time.time()
            while (time.time() - start_pv) < 180:
                await asyncio.sleep(3)
                try:
                    cur = page.url
                except Exception:
                    break
                if "challenge" not in cur and "signin/v2" not in cur:
                    step("[green]>[/]", "Verifikasi HP selesai, lanjut...")
                    break
                elapsed_pv = int(time.time() - start_pv)
                if elapsed_pv > 0 and elapsed_pv % 15 == 0:
                    fast_print(f"  [yellow]...[/]  Menunggu verifikasi HP... ({elapsed_pv}s)", style="bright_yellow")

    # Handle Google Workspace Terms
    await asyncio.sleep(1)
    current_url = page.url
    if "speedbump" in current_url or "workspacetermsofservice" in current_url:
        step("[cyan]>[/]", "Halaman Google Workspace Terms...")
        await wait_for_page_ready(page, desc="Google Workspace Terms", timeout=30000)
        for _ in range(10):
            if "speedbump" not in page.url and "workspacetermsofservice" not in page.url:
                break
            for sel in [
                'button:has-text("Accept")', 'span:text-is("Accept")',
                'button:has-text("I agree")', 'span:text-is("I agree")',
                'button:has-text("Agree")', 'span:text-is("Agree")',
                'button:has-text("Continue")', 'span:text-is("Continue")',
                '[type="submit"]',
            ]:
                btn = page.locator(sel)
                if await btn.count() > 0 and await btn.first.is_visible():
                    try:
                        await btn.first.click(force=True, timeout=10000)
                    except Exception:
                        try:
                            await btn.first.evaluate("el => el.click()")
                        except Exception:
                            pass
                    await asyncio.sleep(3)
                    break
            else:
                await asyncio.sleep(3)

    # Handle 2FA
    await wait_for_page_ready(page, desc="Google 2FA/verification", timeout=30000)
    current_url = page.url
    if "challenge" in current_url or "signin/v2" in current_url:
        step("!", "Halaman verifikasi/2FA, tunggu 10 detik...")
        await asyncio.sleep(10)


# ── Cognito / Google Consent Handler ────────────────────
async def handle_consent_page(page, timeout=120):
    """
    Handle halaman consent Google untuk Cognito:
    'Google will allow kiro-prod-us-east-1.auth.us-east-1.amazoncognito.com
     to access this info about you'
    Klik Continue.
    """
    step("[cyan]>[/]", "Mencari tombol Continue/Allow di halaman consent...")
    start = time.time()
    while (time.time() - start) < timeout:
        try:
            cur = page.url
        except Exception:
            break

        # Jika sudah redirect ke app.kiro.dev atau Cognito callback, selesai
        if KIRO_APP_DOMAIN in cur or "/oauth2/token" in cur or "code=" in cur:
            step("[cyan]>[/]", "Sudah redirect dari consent, lanjut...")
            break

        clicked = False
        try:
            for sel in [
                'span:text-is("Continue")',
                'button:has-text("Continue")',
                'span:text-is("Izinkan")',
                'button:has-text("Izinkan")',
                "#submit_approve_access",
                'button:has-text("Allow")',
                'span:text-is("Allow")',
                'button:has-text("Agree")',
                'span:text-is("Agree")',
                '[type="submit"]',
            ]:
                btn = page.locator(sel)
                if await btn.count() > 0 and await btn.first.is_visible():
                    step("[cyan]>[/]", f"Klik consent button: {sel}")
                    try:
                        await btn.first.click()
                    except Exception:
                        try:
                            await btn.first.evaluate("el => el.click()")
                        except Exception:
                            pass
                    clicked = True
                    await asyncio.sleep(3)
                    break
        except Exception:
            pass

        if not clicked:
            # Cek body text untuk konfirmasi consent page
            try:
                body_text = await page.evaluate("document.body ? document.body.innerText : ''")
                if KIRO_AUTH_DOMAIN in body_text:
                    step("[yellow]...[/]", "Halaman consent Cognito terdeteksi, cari tombol...")
            except Exception:
                pass

        await asyncio.sleep(2)

    return True


# ── Popup Handler ───────────────────────────────────────
async def close_popups(context, main_page):
    """
    Tutup popup window yang muncul setelah Google OAuth.
    Hanya tutup popup yang BUKAN main page.
    """
    try:
        pages = context.pages
        for p in pages:
            if p != main_page:
                try:
                    url = p.url
                    step("[cyan]>[/]", f"Menutup popup: {url[:60]}...")
                    await p.close()
                except Exception:
                    pass
    except Exception:
        pass


# ── Wait for Kiro Redirect ──────────────────────────────
async def wait_for_kiro_redirect(page, timeout=120):
    """
    Tunggu sampai redirect ke app.kiro.dev (auth selesai).
    """
    step("> ", "Menunggu redirect ke Kiro app...")
    start = time.time()
    while (time.time() - start) < timeout:
        try:
            cur = page.url
        except Exception:
            await asyncio.sleep(2)
            continue

        if KIRO_APP_DOMAIN in cur and "signin" not in cur:
            step("[green]>[/]", f"Redirect ke Kiro app: {cur[:60]}")
            return True

        if KIRO_APP_DOMAIN in cur and "signin" in cur:
            # Mungkin masih loading
            pass

        await asyncio.sleep(2)

    # Cek apakah sudah di Kiro app walau URL masih signin
    try:
        cur = page.url
        if KIRO_APP_DOMAIN in cur:
            step("[yellow]...[/]", f"Di Kiro domain: {cur[:60]}")
            return True
    except Exception:
        pass

    return False


# ── 9Router Injection ───────────────────────────────────

_9router_auth_token = None


def _9router_login(router_url: str, password: str) -> str:
    global _9router_auth_token
    if _9router_auth_token:
        return _9router_auth_token
    login_url = f"{router_url.rstrip('/')}/api/auth/login"
    body = json.dumps({"password": password}).encode("utf-8")
    req = urllib.request.Request(
        login_url, data=body,
        headers={"Content-Type": "application/json", "User-Agent": "KiroBot/1.0"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            for header in resp.headers.get_all("Set-Cookie") or []:
                if header.startswith("auth_token="):
                    token = header.split(";")[0].split("=", 1)[1]
                    _9router_auth_token = token
                    return token
    except Exception as e:
        raise RuntimeError(f"Login 9router gagal: {e}")
    raise RuntimeError("Login 9router gagal: auth_token tidak ditemukan")


def get_9router_connections(router_url: str, password: Optional[str] = None) -> list:
    global _9router_auth_token
    if password and not _9router_auth_token:
        _9router_login(router_url, password)
    providers_url = f"{router_url.rstrip('/')}/api/providers"
    headers = {"User-Agent": "KiroBot/1.0"}
    if _9router_auth_token:
        headers["Cookie"] = f"auth_token={_9router_auth_token}"
    req = urllib.request.Request(providers_url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data.get("connections", [])
    except Exception as e:
        raise RuntimeError(f"Gagal ambil koneksi 9router: {e}")


def inject_to_9router(
    router_url: str,
    password: Optional[str],
    email: str,
    refresh_token: str,
    provider_name: str = "kiro",
    check_duplicate: bool = True,
) -> dict:
    global _9router_auth_token
    if password and not _9router_auth_token:
        try:
            _9router_login(router_url, password)
        except RuntimeError as e:
            return {"success": False, "error": str(e)}

    # Use the correct Kiro OAuth import endpoint
    kiro_import_url = f"{router_url.rstrip('/')}/api/oauth/kiro/import"
    payload = {
        "refreshToken": refresh_token
    }
    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "KiroBot/1.0",
    }
    if _9router_auth_token:
        headers["Cookie"] = f"auth_token={_9router_auth_token}"

    req = urllib.request.Request(kiro_import_url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            if data.get("success"):
                return {"success": True, "data": data}
            else:
                return {"success": False, "error": "Import failed"}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        try:
            error_data = json.loads(error_body)
            error_msg = error_data.get("error", error_body)
        except Exception:
            error_msg = error_body
        return {"success": False, "error": f"HTTP {e.code}: {error_msg}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def inject_from_file(
    file_path: str,
    router_url: str,
    password: Optional[str],
    provider_name: str = "kiro",
    workers: int = 2,
) -> dict:
    if not os.path.exists(file_path):
        return {"success": False, "error": f"File tidak ditemukan: {file_path}"}

    entries = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" not in line:
                continue
            parts = line.split(":", 1)
            if len(parts) == 2:
                email, refresh_token = parts[0].strip(), parts[1].strip()
                if email and refresh_token:
                    entries.append((email, refresh_token))

    if not entries:
        return {"success": False, "error": "Tidak ada entry valid di file"}

    if password:
        try:
            _9router_login(router_url, password)
        except RuntimeError as e:
            return {"success": False, "error": str(e)}

    from concurrent.futures import ThreadPoolExecutor, as_completed
    import threading

    results = {"total": len(entries), "injected": 0, "skipped": 0, "failed": 0, "errors": []}
    lock = threading.Lock()

    def inject_one(entry):
        email, refresh_token = entry
        result = inject_to_9router(
            router_url=router_url, password=None,
            email=email, refresh_token=refresh_token,
            provider_name=provider_name, check_duplicate=False,
        )
        return (email, result)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(inject_one, entry): entry for entry in entries}
        for future in as_completed(futures):
            email, result = future.result()
            with lock:
                if result["success"]:
                    results["injected"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append(f"{email}: {result.get('error', 'unknown')}")

    results["success"] = True
    return results


# ── List Accounts ───────────────────────────────────────
def list_accounts(log_file):
    """Tampilkan daftar akun dari account.json."""
    if not os.path.exists(log_file):
        fail(f"File tidak ditemukan: {log_file}")
        return

    try:
        with open(log_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        fail(f"Gagal baca account.json: {e}")
        return

    if not data:
        info("account.json kosong")
        return

    total = len(data)
    success_count = sum(1 for v in data.values() if v.get("success"))
    fail_count = total - success_count

    print()
    rule("═")
    fast_print("  DAFTAR AKUN KIRO", style="bold bright_magenta")
    rule("═")
    print()
    info(f"Total akun : {total}")
    ok(f"Berhasil   : {success_count}")
    if fail_count > 0:
        fail(f"Gagal      : {fail_count}")
    print()

    if HAS_RICH:
        table = Table(
            show_header=True,
            header_style="bold bright_white on grey11",
            border_style="bright_magenta",
            padding=(0, 1),
        )
        table.add_column("#", width=4, justify="right", style="dim")
        table.add_column("Email", min_width=25, max_width=40, no_wrap=True, overflow="ellipsis")
        table.add_column("Status", width=8)
        table.add_column("Refresh Token (last 8)", min_width=15, max_width=20, no_wrap=True, overflow="ellipsis")
        table.add_column("Timestamp", width=20)

        for idx, (email, info_data) in enumerate(data.items(), 1):
            status = "SUCCESS" if info_data.get("success") else "FAILED"
            status_style = "bold green" if info_data.get("success") else "bold red"
            rt = info_data.get("refresh_token", "")
            rt_display = f"...{rt[-8:]}" if len(rt) > 8 else rt
            ts = info_data.get("timestamp", "")
            table.add_row(
                str(idx),
                email[:37] + "..." if len(email) > 40 else email,
                RichText(status, style=status_style) if RichText else status,
                rt_display or "---",
                ts,
            )
        console.print(table)
    else:
        print(f"  {'#':<4} {'Email':<35} {'Status':<8} {'Refresh Token':<20} {'Timestamp'}")
        print(f"  {'─'*4} {'─'*35} {'─'*8} {'─'*20} {'─'*20}")
        for idx, (email, info_data) in enumerate(data.items(), 1):
            status = "OK" if info_data.get("success") else "FAIL"
            rt = info_data.get("refresh_token", "")
            rt_display = f"...{rt[-8:]}" if len(rt) > 8 else rt
            ts = info_data.get("timestamp", "")
            email_disp = email[:32] + "..." if len(email) > 35 else email
            print(f"  {idx:<4} {email_disp:<35} {status:<8} {rt_display:<45} {ts}")

    print()
    rule("═")
    fast_print("  SELESAI", style="bold bright_green")
    rule("═")
    print()


# ── Manual Mode Processing ──────────────────────────────────────
async def process_account_manual(context, email, index, total, worker_id=1):
    """
    Mode semi-auto: User login manual, bot capture token otomatis.
    """
    fast_print(f"  [bold bright_cyan]>[/]  Akun {index}/{total} — {email} [Worker {worker_id}] [MANUAL MODE]", style="bold bright_cyan")
    
    page = await context.new_page()
    result = {"email": email, "password": "manual", "refresh_token": "", "success": False}
    
    # Setup token capture via network interception
    token_capture = TokenCapture()
    token_capture.attach(context)
    
    try:
        # 1. Navigasi ke Kiro landing page
        step("> ", "Navigasi ke Kiro landing page...")
        await page.goto(KIRO_LANDING_URL, wait_until="load", timeout=60000)
        await asyncio.sleep(2)
        
        # 2. Instruksi untuk user
        fast_print("\n" + "="*70, style="bold yellow")
        fast_print("  🔔 MODE MANUAL AKTIF", style="bold yellow")
        fast_print("="*70, style="bold yellow")
        fast_print("  📌 INSTRUKSI:", style="bold bright_white")
        fast_print("     1. Klik tombol 'Sign in' di browser", style="bright_white")
        fast_print("     2. Login dengan Google (manual)", style="bright_white")
        fast_print("     3. Handle captcha/verification jika ada", style="bright_white")
        fast_print("     4. Klik 'Allow/Izinkan' untuk consent", style="bright_white")
        fast_print("     5. Tunggu sampai redirect ke app.kiro.dev", style="bright_white")
        fast_print("     6. Bot akan AUTO CAPTURE refresh token!", style="bold bright_green")
        fast_print("", style="")
        fast_print(f"  ⏱️  Timeout: 5 menit (300 detik)", style="bright_yellow")
        fast_print("="*70 + "\n", style="bold yellow")
        
        # 3. Tunggu user login manual (max 5 menit)
        step("> ", "Menunggu Anda login manual...")
        start_time = time.time()
        timeout = 300  # 5 menit
        check_interval = 2  # Check setiap 2 detik
        
        logged_in = False
        while (time.time() - start_time) < timeout:
            elapsed = int(time.time() - start_time)
            
            # Check URL apakah sudah di app.kiro.dev (dan bukan signin page)
            try:
                current_url = page.url
                if KIRO_APP_DOMAIN in current_url and "/signin" not in current_url:
                    step("[green]>[/]", f"Login berhasil terdeteksi! URL: {current_url[:60]}")
                    logged_in = True
                    break
            except Exception:
                pass
            
            # Log progress setiap 15 detik
            if elapsed > 0 and elapsed % 15 == 0:
                remaining = timeout - elapsed
                step("[yellow]...[/]", f"Menunggu login... ({elapsed}s berlalu, {remaining}s tersisa)")
            
            await asyncio.sleep(check_interval)
        
        if not logged_in:
            raise Exception("Timeout! Login manual tidak selesai dalam 5 menit")
        
        # 4. Tunggu page stabil
        step("> ", "Login berhasil! Tunggu page stabil...")
        await asyncio.sleep(5)
        
        try:
            await page.wait_for_load_state("networkidle", timeout=30000)
        except Exception:
            step("!", "Networkidle timeout, lanjut capture token...")
        
        # 5. Capture refresh token
        step("> ", "Mengambil refresh token...")
        refresh_token = await capture_refresh_token(page, context, token_capture, timeout=120)
        
        if not refresh_token:
            raise Exception("Refresh token tidak ditemukan (network, localStorage, URL, cookies semua gagal)")
        
        result["refresh_token"] = refresh_token
        result["success"] = True
        
        step("[green]>[/]", f"Refresh token captured (...{refresh_token[-8:]})")
        ok(f"AKUN #{index} BERHASIL! [Worker {worker_id}]")
        fast_print(f"    Email : {email}")
        fast_print(f"    Token : ...{refresh_token[-8:]} (disimpan ke file)")
        
    except Exception as e:
        fail(f"AKUN #{index} GAGAL: {e} [Worker {worker_id}]")
        result["success"] = False
        result["error"] = str(e)
    finally:
        try:
            await page.close()
        except Exception:
            pass
    
    return result


# ── Main Processing ──────────────────────────────────────
async def process_account(context, email, password, index, total, worker_id=1, register_mode=False, manual_mode=False):
    """Proses satu akun: Kiro signin → Google login → consent → capture refresh token."""

    if manual_mode:
        return await process_account_manual(context, email, index, total, worker_id)

    mode_label = "REGISTER" if register_mode else "LOGIN"
    fast_print(f"  [bold bright_magenta]>[/]  Akun {index}/{total} — {email} [Worker {worker_id}] [{mode_label}]", style="bold bright_magenta")

    page = await context.new_page()
    result = {"email": email, "password": password, "refresh_token": "", "success": False}

    # Setup token capture via network interception
    token_capture = TokenCapture()
    token_capture.attach(context)

    try:
        # 1. Navigasi ke Kiro landing page (kiro.dev)
        step("> ", "Navigasi ke Kiro landing page...")
        await goto_robust(page, KIRO_LANDING_URL, desc="Kiro Landing Page")
        
        # Random delay seperti user membaca halaman
        await asyncio.sleep(2 + (0.5 * (hash(email) % 4)))  # 2-4s
        
        # 2. Cari dan klik tombol "Sign in" di landing page
        step("> ", "Mencari tombol 'Sign in' di landing page...")
        signin_btn = None
        signin_selectors = [
            'a[href*="signin"]:has-text("Sign in")',
            'a[href*="/signin"]:has-text("Sign in")',
            'button:has-text("Sign in")',
            'a:has-text("Sign In")',
            'button:has-text("Sign In")',
            'a[href*="signin"]',
            'a[href*="/signin"]',
            'a[href*="login"]',
            'a:has-text("LOGIN")',
            'button:has-text("LOGIN")',
            'a:has-text("Log in")',
            'button:has-text("Log in")',
        ]
        
        for sel in signin_selectors:
            btn = page.locator(sel).first
            try:
                if await btn.count() > 0 and await btn.is_visible():
                    # Validasi href jika element adalah <a>
                    href = None
                    try:
                        href = await btn.get_attribute("href")
                    except Exception:
                        pass
                    
                    text = await btn.inner_text(timeout=1000) if await btn.is_visible() else ""
                    
                    # Pastikan ini bukan link ke Google Search
                    if href and ("google.com" in href or "search" in href):
                        continue
                    
                    if any(kw in text.lower() for kw in ["sign in", "log in", "signin", "login"]):
                        signin_btn = btn
                        step("> ", f"Tombol 'Sign in' ditemukan: {sel} (href={href})")
                        break
            except Exception:
                continue
        
        if signin_btn:
            try:
                await signin_btn.click(timeout=10000)
            except Exception:
                try:
                    await signin_btn.evaluate("el => el.click()")
                except Exception:
                    pass
            step("> ", "Klik 'Sign in'", "ok")
            
            # Tunggu redirect - LEBIH LAMA untuk SPA
            await asyncio.sleep(8)  # Tunggu redirect (increase dari 5s ke 8s)
            
            # Tunggu sampai halaman signin fully loaded dengan retry
            for retry in range(3):
                try:
                    await page.wait_for_load_state("load", timeout=30000)
                    await page.wait_for_load_state("networkidle", timeout=20000)
                    break
                except Exception:
                    step("!", f"Timeout waiting for load state, retry {retry+1}/3...")
                    await asyncio.sleep(5)
            
            # Validasi halaman signin tidak blank dengan multiple checks
            for check in range(5):
                try:
                    body_text = await page.evaluate("document.body ? document.body.innerText.trim().length : 0")
                    current_url = page.url
                    step("> ", f"Check #{check+1}: URL={current_url[:60]}, chars={body_text}")
                    
                    if body_text > 100:
                        step("> ", f"Signin page loaded OK ({body_text} chars)")
                        break
                    
                    if body_text < 20:
                        step("!", f"Signin page blank ({body_text} chars), tunggu lagi...")
                        await asyncio.sleep(3)
                        
                        # Reload hanya jika benar-benar blank dan bukan di Google Search
                        if check >= 2 and "google.com/search" not in current_url:
                            try:
                                step("> ", "Reload page karena blank...")
                                await page.reload(wait_until="load", timeout=30000)
                                await asyncio.sleep(5)
                            except Exception:
                                pass
                except Exception as e:
                    step("!", f"Error checking page: {e}")
                    await asyncio.sleep(2)
                    
        else:
            # Fallback: langsung ke signin URL
            step("[yellow]...[/]", "Tombol Sign in tidak ditemukan, navigasi langsung ke signin...")
            await goto_robust(page, KIRO_SIGNIN_URL, desc="Kiro Signin")

        # 3. Klik Google pada "Choose a way to sign in/sign up"
        step("> ", "Mencari tombol Google...")
        
        # Cek URL dulu sebelum mencari tombol
        current_url = page.url
        step("> ", f"Current URL: {current_url}")
        
        # Jika redirect ke Google Search, ada masalah - langsung ke signin URL
        if "google.com/search" in current_url:
            step("!", "Terdeteksi redirect ke Google Search, navigasi ulang ke signin...")
            await goto_robust(page, KIRO_SIGNIN_URL, desc="Kiro Signin (direct)")
            await asyncio.sleep(5)
        
        # Jika masih di landing page atau bukan di signin page, navigasi ulang
        if "app.kiro.dev" not in current_url or current_url == "https://app.kiro.dev/":
            step("!", f"URL tidak sesuai ({current_url}), navigasi ke signin...")
            await goto_robust(page, KIRO_SIGNIN_URL, desc="Kiro Signin (fallback)")
            await asyncio.sleep(5)
        
        await asyncio.sleep(3)

        # Tunggu halaman SPA load — bisa redirect ke Cognito hosted UI
        google_btn = None
        google_selectors = [
            'button:has-text("Google")',
            'a:has-text("Google")',
            'div:has-text("Continue with Google")',
            'button:has-text("Continue with Google")',
            'a:has-text("Continue with Google")',
            'button:has-text("Sign in with Google")',
            'a:has-text("Sign in with Google")',
            'button:has-text("Sign in with Google")',
            'button[title*="Google"]',
            'a[title*="Google"]',
            'button img[alt*="Google"]',
            'a img[alt*="Google"]',
            'button svg',
            'a svg',
            '[data-provider="Google"]',
            '.providerButton:has-text("Google")',
            'button[role="button"]',
            'div[role="button"]',
        ]

        for sel in google_selectors:
            btn = page.locator(sel).first
            try:
                if await btn.count() > 0 and await btn.is_visible():
                    text = await btn.inner_text(timeout=1000) if await btn.is_visible() else ""
                    if "google" in text.lower() or "continue" in text.lower() or "sign in" in text.lower():
                        google_btn = btn
                        step("> ", f"Tombol Google ditemukan: {sel}")
                        break
            except Exception:
                continue

        if not google_btn:
            # Mungkin sudah redirect ke Cognito — tunggu dan coba lagi
            step("[yellow]...[/]", "Tombol Google belum muncul, tunggu redirect...")
            await asyncio.sleep(5)
            for sel in google_selectors:
                btn = page.locator(sel).first
                try:
                    if await btn.count() > 0 and await btn.is_visible():
                        text = await btn.inner_text(timeout=1000) if await btn.is_visible() else ""
                        if "google" in text.lower() or "continue" in text.lower() or "sign in" in text.lower():
                            google_btn = btn
                            step("> ", f"Tombol Google ditemukan: {sel}")
                            break
                except Exception:
                    continue

        if not google_btn:
            # Coba sembarang button/link yang mengandung icon Google atau teks Google
            for sel in ['button', 'a', 'div[role="button"]']:
                try:
                    elements = await page.locator(sel).all()
                except Exception:
                    continue
                for el in elements:
                    try:
                        if not await el.is_visible():
                            continue
                        text = await el.inner_text(timeout=1000)
                        if any(kw in text.lower() for kw in ["google", "continue with", "sign in with"]):
                            google_btn = el
                            step("> ", f"Tombol Google ditemukan via text: {text[:40]}")
                            break
                    except Exception:
                        continue
                if google_btn:
                    break

        if not google_btn:
            # Screenshot debug
            try:
                screenshot_path = os.path.join(WORKSPACE, f"debug_kiro_signin_{int(time.time())}.png")
                await page.screenshot(path=screenshot_path, full_page=True)
                step("!", f"Screenshot debug: {screenshot_path}")
            except Exception:
                pass
            # Coba klik sembarang tombol submit
            for sel in ['button[type="submit"]', 'button']:
                btn = page.locator(sel).first
                try:
                    if await btn.count() > 0 and await btn.is_visible():
                        google_btn = btn
                        step("[yellow]...[/]", f"Fallback klik tombol: {sel}")
                        break
                except Exception:
                    continue

        if google_btn:
            try:
                await google_btn.click(force=True, timeout=10000)
            except Exception:
                try:
                    await google_btn.evaluate("el => el.click()")
                except Exception:
                    pass
            step("> ", "Klik Google", "ok")
        else:
            # Mungkin halaman sudah di Google atau Cognito langsung
            step("[yellow]...[/]", "Tombol Google tidak ditemukan, cek URL...")
            cur = page.url
            if "accounts.google.com" in cur:
                step("> ", "Sudah di halaman Google, lanjut...")
            elif KIRO_AUTH_DOMAIN in cur:
                step("> ", "Sudah di Cognito hosted UI, tunggu redirect ke Google...")
                await asyncio.sleep(5)
            else:
                step("!", f"URL tidak dikenali: {cur}")
                # Tunggu mungkin page masih loading
                await asyncio.sleep(5)

        # 3. Google Login
        step("> ", "Login Google...")
        await handle_google_login(page, email, password)

        # 4. Handle consent page (Google → Cognito)
        step("> ", "Handle consent page...")
        await handle_consent_page(page, timeout=120)

        # 5. Cek captcha
        await asyncio.sleep(1)
        await wait_for_captcha_or_continue(page, timeout=90)

        # 6. Tunggu redirect ke Kiro app
        await wait_for_kiro_redirect(page, timeout=120)

        # 7. Tutup popup jika ada
        step("> ", "Cek dan tutup popup...")
        await close_popups(context, page)
        await asyncio.sleep(2)

        # Tunggu page stabil di app.kiro.dev
        try:
            await wait_for_page_ready(page, desc="Kiro App", timeout=60000)
        except Exception:
            step("!", "Kiro App belum fully loaded, lanjut capture token...")

        # 8. Capture refresh token
        step("> ", "Mengambil refresh token...")
        refresh_token = await capture_refresh_token(page, context, token_capture, timeout=120)

        if not refresh_token:
            raise Exception("Refresh token tidak ditemukan (network, localStorage, URL, cookies semua gagal)")

        result["refresh_token"] = refresh_token
        result["success"] = True

        step("[green]>[/]", f"Refresh token captured (...{refresh_token[-8:]})")
        ok(f"AKUN #{index} BERHASIL! [Worker {worker_id}]")
        fast_print(f"    Email : {email}")
        fast_print(f"    Token : ...{refresh_token[-8:]} (disimpan ke file)")

    except Exception as e:
        fail(f"AKUN #{index} GAGAL: {e} [Worker {worker_id}]")
        result["success"] = False
        result["error"] = str(e)
    finally:
        try:
            await page.close()
        except Exception:
            pass

    return result


# ── Worker Function ──────────────────────────────────────
async def worker_task(account_index, email, password, browser, stealth, worker_id, total_accounts, register_mode=False, manual_mode=False, ctx=None):
    if ctx is None:
        # Simplified context - minimal stealth untuk avoid property override errors
        ctx = await browser.new_context(
            permissions=["clipboard-read", "clipboard-write"],
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            java_script_enabled=True,
            locale="en-US",
        )
        # DISABLE playwright-stealth untuk avoid readonly property errors
        # await stealth.apply_stealth_async(ctx)
        
        # Minimal stealth - HANYA override webdriver (yang paling penting)
        await ctx.add_init_script("""
            // Only override webdriver - don't touch other properties
            try {
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                    configurable: true
                });
            } catch(e) {}
            
            // Add chrome object minimally
            if (!window.chrome) {
                window.chrome = { runtime: {} };
            }
        """)
    else:
        ctx = await ctx.new_context(
            permissions=["clipboard-read", "clipboard-write"],
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            java_script_enabled=True,
            locale="en-US",
        )

    r = await process_account(
        ctx, email, password, account_index,
        total=total_accounts, worker_id=worker_id, register_mode=register_mode, manual_mode=manual_mode,
    )
    await ctx.close()
    return r
    if ctx is None:
        # Randomize user agent untuk setiap worker - gunakan versi Chrome yang lebih update
        chrome_versions = ["131.0.0.0", "130.0.0.0", "129.0.0.0"]
        chrome_ver = chrome_versions[account_index % len(chrome_versions)]
        
        # Platform variations untuk lebih realistis
        platforms = [
            "Windows NT 10.0; Win64; x64",
            "Windows NT 10.0; WOW64",
            "Windows NT 10.0",
        ]
        platform = platforms[account_index % len(platforms)]
        
        ctx = await browser.new_context(
            permissions=["clipboard-read", "clipboard-write"],
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                f"Mozilla/5.0 ({platform}) "
                f"AppleWebKit/537.36 (KHTML, like Gecko) "
                f"Chrome/{chrome_ver} Safari/537.36"
            ),
            java_script_enabled=True,
            locale="en-US",
            timezone_id="America/New_York",  # Add timezone
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Cache-Control": "max-age=0",
            },
        )
        await stealth.apply_stealth_async(ctx)
        
        # Inject extra stealth scripts - enhanced
        await ctx.add_init_script("""
            // Override navigator properties
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format'},
                    {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: ''},
                    {name: 'Native Client', filename: 'internal-nacl-plugin', description: ''}
                ]
            });
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});
            Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
            Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
            Object.defineProperty(navigator, 'maxTouchPoints', {get: () => 0});
            
            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({state: Notification.permission}) :
                    originalQuery(parameters)
            );
            
            // Chrome runtime
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
            
            // Add missing properties
            if (!window.chrome.app) {
                window.chrome.app = {
                    isInstalled: false,
                    InstallState: {DISABLED: 'disabled', INSTALLED: 'installed', NOT_INSTALLED: 'not_installed'},
                    RunningState: {CANNOT_RUN: 'cannot_run', READY_TO_RUN: 'ready_to_run', RUNNING: 'running'}
                };
            }
        """)
    else:
        ctx = await ctx.new_context(
            permissions=["clipboard-read", "clipboard-write"],
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            java_script_enabled=True,
            locale="en-US",
        )
        await stealth.apply_stealth_async(ctx)

    r = await process_account(
        ctx, email, password, account_index,
        total=total_accounts, worker_id=worker_id, register_mode=register_mode,
    )
    await ctx.close()
    return r


# ── CLI Argument Parsing ────────────────────────────────
def parse_args():
    parser = argparse.ArgumentParser(
        description="Kiro Refresh Token Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python kiro.py                        # Semua akun, login mode, 2 workers
  python kiro.py 10                    # 10 akun pertama
  python kiro.py 10 4                  # 10 akun, 4 workers
  python kiro.py 10 4 --register       # 10 akun, register mode
  python kiro.py 10 4 --visible        # Tampilkan browser
  python kiro.py --list                # List akun di account.json
  python kiro.py 10 4 --inject-9router --router-password MyPass123
  python kiro.py --inject-from-file kiro_tokens.txt --router-password MyPass123

  # Provider name custom untuk 9router
  python kiro.py 10 4 --inject-9router --router-password MyPass123 --provider kiro
        """,
    )
    parser.add_argument("jumlah", nargs="?", default="all", help="Jumlah akun yang diproses (default: all)")
    parser.add_argument("workers", nargs="?", type=int, default=2, help="Jumlah worker paralel (default: 2)")
    parser.add_argument("-a", "--accounts", type=str, default=None, help="Path file akun (default: account.txt)")
    parser.add_argument("-o", "--output", type=str, default=None, help="Path output token file (default: kiro_tokens.txt)")
    parser.add_argument("-d", "--delay", type=float, default=3.0, help="Delay antar batch (default: 3)")
    parser.add_argument("--visible", action="store_true", help="Tampilkan browser (default: headless)")
    parser.add_argument("--register", action="store_true", help="Mode register (akun Kiro baru via Google)")
    parser.add_argument("--list", action="store_true", help="List akun dari account.json")
    parser.add_argument("--inject-9router", action="store_true", help="Inject refresh token ke 9router")
    parser.add_argument("--router-url", type=str, default="http://localhost:20128", help="URL 9router (default: http://localhost:20128)")
    parser.add_argument("--router-password", type=str, default=None, help="Password 9router")
    parser.add_argument("--inject-from-file", type=str, default=None, metavar="FILE", help="Inject dari file kiro_tokens.txt ke 9router")
    parser.add_argument("--provider", type=str, default="kiro", help="Provider name untuk 9router (default: kiro)")
    parser.add_argument("--chrome", action="store_true", help="Gunakan system Chrome/Chromium (bukan Playwright Chromium)")
    parser.add_argument("--manual", action="store_true", help="Mode semi-auto: Anda login manual, bot capture token otomatis")
    return parser.parse_args()


# ── Entry Point ─────────────────────────────────────────
async def main():
    args = parse_args()

    NUM_WORKERS = args.workers
    DELAY_BETWEEN_ACCOUNTS = args.delay
    default_accounts_file = "registerakun.txt" if args.register else "account.txt"
    accounts_file = args.accounts or os.path.join(WORKSPACE, default_accounts_file)
    output_file = args.output or os.path.join(WORKSPACE, "kiro_tokens.txt")
    log_file = os.path.join(WORKSPACE, "account.json")
    log_example = os.path.join(WORKSPACE, "account.json.example")

    # Auto-init account.json
    if not os.path.exists(log_file):
        if os.path.exists(log_example):
            import shutil
            try:
                shutil.copy2(log_example, log_file)
                info(f"account.json dibuat dari template: {log_example}")
            except Exception as e:
                fail(f"Gagal menyalin account.json.example: {e}")
        else:
            try:
                with open(log_file, "w", encoding="utf-8") as f:
                    json.dump({}, f)
                info("account.json dibuat (kosong)")
            except Exception as e:
                fail(f"Gagal membuat account.json: {e}")

    headless = not args.visible

    async with async_playwright() as p:
        # Simplified launch args - remove aggressive flags yang cause ERR_INVALID_ARGUMENT
        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--no-first-run",
            "--disable-infobars",
            "--no-default-browser-check",
            "--window-size=1920,1080",
            "--start-maximized",
            "--lang=en-US,en",
        ]
        
        # Launch browser dengan channel (gunakan system Chrome jika ada)
        try:
            # Try chrome channel first (lebih natural)
            browser = await p.chromium.launch(
                headless=headless,
                channel="chrome",  # Use system Chrome
                args=launch_args
            )
            step("> ", "Menggunakan system Chrome")
        except Exception:
            # Fallback ke chromium biasa
            browser = await p.chromium.launch(
                headless=headless,
                args=launch_args
            )
            step("> ", "Menggunakan Playwright Chromium")
        
        # Simplified context - remove extra headers yang cause ERR_INVALID_ARGUMENT
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            java_script_enabled=True,
            locale="en-US",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            # Remove extra_http_headers yang conflict
        )

        stealth = Stealth()

        # ── Mode: List ──
        if args.list:
            list_accounts(log_file)
            await browser.close()
            return

        # ── Mode: Inject from file ──
        if args.inject_from_file:
            file_path = args.inject_from_file
            if not os.path.isabs(file_path):
                file_path = os.path.join(WORKSPACE, file_path)

            inject_workers = args.workers
            if args.jumlah != "all":
                try:
                    inject_workers = int(args.jumlah)
                except ValueError:
                    pass

            print()
            rule("═")
            fast_print("  INJECT KIRO REFRESH TOKEN KE 9ROUTER DARI FILE", style="bold bright_magenta")
            rule("═")
            print()
            info(f"File: {file_path}")
            info(f"9router: {args.router_url}")
            info(f"Provider: {args.provider}")
            info(f"Workers: {inject_workers}")
            print()

            result = inject_from_file(
                file_path=file_path,
                router_url=args.router_url,
                password=args.router_password,
                provider_name=args.provider,
                workers=inject_workers,
            )

            if not result["success"]:
                fail(result["error"])
                await browser.close()
                return

            print()
            ok(f"Total entry: {result['total']}")
            ok(f"Berhasil inject: {result['injected']}")
            if result["skipped"] > 0:
                info(f"Duplicate skip: {result['skipped']}")
            if result["failed"] > 0:
                fail(f"Gagal: {result['failed']}")
                for err in result["errors"][:5]:
                    print(f"    - {err}")
                if len(result["errors"]) > 5:
                    print(f"    ... dan {len(result['errors']) - 5} error lainnya")
            print()
            rule("═")
            fast_print("  SELESAI", style="bold bright_green")
            rule("═")
            print()
            await browser.close()
            return

# ── Mode: Login / Register ──
        public_ip = await asyncio.to_thread(get_public_ip)

        if args.manual:
            info("MODE: MANUAL (Anda login manual, bot capture token)")
        elif args.register:
            info("MODE: REGISTER (akun Kiro baru via Google)")
        else:
            info("MODE: LOGIN (akun Kiro yang sudah terdaftar)")

        info(f"IP Publik: {public_ip}")

        # Baca akun
        if not os.path.exists(accounts_file):
            fail(f"File akun tidak ditemukan: {accounts_file}")
            return

        accounts = read_accounts(accounts_file)
        if not accounts:
            fail("Tidak ada akun valid di file akun")
            return

        # Load processed emails dari account.json
        processed_emails = {}
        if os.path.exists(log_file):
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    processed_emails = json.load(f)
            except Exception:
                processed_emails = {}
        info(f"{len(processed_emails)} akun sudah diproses sebelumnya")

        # Filter akun yang sudah diproses (hanya yang sukses)
        original_count = len(accounts)
        accounts = [(e, p) for e, p in accounts if e not in processed_emails or not processed_emails[e].get("success")]
        skipped = original_count - len(accounts)
        if skipped > 0:
            info(f"{skipped} akun dilewati (sudah sukses)")
        if not accounts:
            ok("Semua akun sudah diproses sebelumnya!")
            return

        # Limit jumlah akun
    if args.jumlah != "all":
        try:
            limit = int(args.jumlah)
            accounts = accounts[:limit]
        except ValueError:
            fail(f"Jumlah tidak valid: {args.jumlah}. Gunakan angka atau 'all'.")
            return

    total_accounts = len(accounts)
    start_time = time.time()

    batch_tasks = []

    # Buka output file
    if not os.path.exists(output_file):
        with open(output_file, "w", encoding="utf-8") as f:
            pass

    success_count = 0
    fail_count = 0

    print()
    rule("═")
    fast_print(f"  MEMPROSES {total_accounts} AKUN DENGAN {NUM_WORKERS} WORKERS", style="bold bright_magenta")
    rule("═")
    print()

    async with async_playwright() as p:
        # Bagi akun menjadi batch
        batches = []
        for i in range(0, len(accounts), NUM_WORKERS):
            batch = [(i + j + 1, accounts[i + j][0], accounts[i + j][1])
                     for j in range(min(NUM_WORKERS, len(accounts) - i))]
            batches.append(batch)

        total_batches = len(batches)

        for batch_idx, batch in enumerate(batches):
            batch_num = batch_idx + 1
            fast_print(f"  [bold bright_magenta]>[/]  Batch {batch_num}/{total_batches} — {len(batch)} akun...",
                       style="bold bright_magenta")

            # Launch browser dengan channel chrome (lebih natural)
            try:
                fresh_browser = await p.chromium.launch(
                    headless=headless, 
                    channel="chrome",  # Use system Chrome
                    args=launch_args
                )
            except Exception:
                # Fallback ke chromium
                fresh_browser = await p.chromium.launch(
                    headless=headless, 
                    args=launch_args
                )

            batch_tasks = []
            for idx, email, pwd in batch:
                wid = (idx - 1) % NUM_WORKERS + 1
                task = asyncio.create_task(
                    worker_task(idx, email, pwd, fresh_browser, stealth, wid, total_accounts, register_mode=args.register, manual_mode=args.manual)
                )
                batch_tasks.append(task)

            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            await fresh_browser.close()

            # Simpan hasil ke kiro_tokens.txt
            def _append_tokens():
                with open(output_file, "a", encoding="utf-8") as f:
                    for r in batch_results:
                        if isinstance(r, Exception):
                            continue
                        if isinstance(r, dict) and r.get("success", False) and r.get("refresh_token"):
                            f.write(f"{r['email']}:{r['refresh_token']}\n")
            await asyncio.to_thread(_append_tokens)

            # Inject ke 9router
            if args.inject_9router:
                for r in batch_results:
                    if isinstance(r, Exception):
                        continue
                    if isinstance(r, dict) and r.get("success", False) and r.get("refresh_token"):
                        result = await asyncio.to_thread(
                            inject_to_9router,
                            router_url=args.router_url,
                            password=args.router_password,
                            email=r["email"],
                            refresh_token=r["refresh_token"],
                            provider_name=args.provider,
                        )
                        if result["success"]:
                            fast_print(f"  [bold green]>[/]  Injected ke 9router: {r['email']}", style="bold green")
                        else:
                            fast_print(f"  [bold red]x[/]  Gagal inject 9router: {result['error']}", style="bold red")

            # Update account.json
            for r in batch_results:
                if isinstance(r, Exception):
                    continue
                if not isinstance(r, dict):
                    continue
                email = r.get("email", "")
                if not email:
                    continue
                is_success = r.get("success", False)
                processed_emails[email] = {
                    "success": is_success,
                    "refresh_token": r.get("refresh_token", ""),
                    "error": r.get("error", ""),
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
                if is_success:
                    success_count += 1
                else:
                    fail_count += 1

            def _save_account_json():
                tmp = log_file + ".tmp"
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(processed_emails, f, indent=2, ensure_ascii=False)
                os.replace(tmp, log_file)

            try:
                await asyncio.to_thread(_save_account_json)
            except Exception as e:
                fail(f"Gagal simpan account.json: {e}")

            fast_print(f"  [bold green]>[/]  Batch {batch_num}/{total_batches} selesai",
                       style="bold green")

            if batch_idx < total_batches - 1:
                fast_print(f"  [yellow]>[/]  Menunggu {DELAY_BETWEEN_ACCOUNTS}s...",
                           style="bright_yellow")
                await asyncio.sleep(DELAY_BETWEEN_ACCOUNTS)

    total_time = time.time() - start_time

    # Ringkasan
    print()
    rule("═")
    fast_print("  RINGKASAN HASIL", style="bold bright_white")
    rule("═")
    print()
    print(f"  Total Akun  : {total_accounts}")
    print(f"  Total Batch : {total_batches}")
    print(f"  + Berhasil  : {success_count}")
    print(f"  x Gagal     : {fail_count}")
    if total_accounts > 0:
        rate = (success_count / total_accounts) * 100
        print(f"  Rate        : {rate:.1f}%")
    print()

    if success_count > 0:
        fast_print("  AKUN BERHASIL:", style="bold green")
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            for email, info_data in data.items():
                if info_data.get("success"):
                    rt = info_data.get("refresh_token", "")
                    print(f"    + {email}  (...{rt[-8:]})")
        except Exception:
            pass
        print()

    if fail_count > 0:
        fast_print("  AKUN GAGAL:", style="bold red")
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            for email, info_data in data.items():
                if not info_data.get("success"):
                    print(f"    x {email}")
                    print(f"         Error: {info_data.get('error', 'Unknown')}")
        except Exception:
            pass
        print()

    print(f"  Token file : {output_file}")
    print(f"  Log akun   : {log_file}")
    if args.inject_9router:
        print(f"  9router    : {args.router_url} (injected)")
    print()
    fast_print(f"  Total waktu: {total_time:.1f}s (rata-rata {total_time / max(total_accounts, 1):.1f}s/akun)",
               style="bright_cyan")
    print()
    rule("═")
    fast_print("  SELESAI", style="bold bright_green")
    rule("═")
    print()


if __name__ == "__main__":
    asyncio.run(main())
