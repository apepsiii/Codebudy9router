"""
===========================================
  Cloudflare API Key Bot (Stealth Edition)
===========================================


Menggunakan Playwright + playwright-stealth
untuk anti-detection yang kuat terhadap
Cloudflare Turnstile / captcha.


SETUP:
  1. pip install playwright playwright-stealth rich
  2. playwright install chromium
  3. Buat file account.txt (format: email:password)
  4. python main.py [jumlah] [workers]


Output: cloudflare_api.txt (format: account_id:apikey)
Log:    account.json (log semua akun yang sudah diproses)


9ROUTER INJECTION:
  Inject akun ke 9router setelah API key berhasil dibuat.
  Gunakan flag --inject-9router untuk mengaktifkan.

  Contoh:
    python main.py 10 4 --inject-9router
    python main.py all 2 --inject-9router --router-password MyPassword123
    python main.py 5 2 --inject-9router --router-url http://192.168.1.100:20128

  Inject dari file (tanpa buat API key baru):
    python main.py --inject-from-file cloudflare_api.txt --router-password MyPassword123

  Flag:
    --inject-9router      Aktifkan inject ke 9router setelah buat API key
    --inject-from-file    Inject dari file cloudflare_api.txt ke 9router
    --router-url          URL 9router (default: http://localhost:20128)
    --router-password     Password 9router (opsional, auto-login jika diisi)
"""


import asyncio
import os
import re
import sys
import io
import time
import argparse
import httpx
from typing import Optional


from playwright.async_api import async_playwright
from playwright_stealth import Stealth

from dashboard import Stage, Status, ErrorCategory, DashboardState, generate_layout


# Force UTF-8 output for Windows terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


# Rich — lightweight imports
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.live import Live
    from datetime import datetime
    import urllib.request
    import json
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


console = Console(highlight=False, force_terminal=True) if HAS_RICH else None


# ── Log Buffer (for Live dashboard) ──────────────────────
import collections
_log_buffer: collections.deque = collections.deque(maxlen=10)
_live_mode: bool = False



# ── Config ──────────────────────────────────────────────
WORKSPACE = os.path.dirname(os.path.abspath(__file__))
# DELAY_BETWEEN_ACCOUNTS is now configurable via --delay argument


# Browser args — aggressive stealth
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
    # "--disable-features=site-per-process",  # Removed: may break Turnstile iframe
    "--incognito",
    "--disable-gpu",
    "--disable-datasaver",
    "--disable-ipc-flooding-protection",
    "--lang=en-US,en",
]


# ── Banner ──────────────────────────────────────────────
BANNER = "[bold orange1]CF API Key Bot v3.0[/] [dim]| Stealth Edition | Playwright[/]"


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
        console.print(Panel(BANNER, border_style="bright_cyan", padding=(0, 0)))
    else:
        print(BANNER)



# ── Dashboard Infrastructure ────────────────────────────
def get_public_ip():
    """Mengambil IP publik yang sedang digunakan."""
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


# ── 9Router Injection ────────────────────────────────────

_9router_auth_token = None  # Cached auth token for9router


def _9router_login(router_url: str, password: str) -> str:
    """Login ke 9router dashboard, return auth_token cookie."""
    global _9router_auth_token
    if _9router_auth_token:
        return _9router_auth_token

    login_url = f"{router_url.rstrip('/')}/api/auth/login"
    body = json.dumps({"password": password}).encode("utf-8")
    req = urllib.request.Request(
        login_url,
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "FlowCf/3.0"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            # Extract auth_token from Set-Cookie header
            for header in resp.headers.get_all("Set-Cookie") or []:
                if header.startswith("auth_token="):
                    token = header.split(";")[0].split("=", 1)[1]
                    _9router_auth_token = token
                    return token
    except Exception as e:
        raise RuntimeError(f"Login 9router gagal: {e}")
    raise RuntimeError("Login 9router gagal: auth_token tidak ditemukan di response")


def get_9router_connections(router_url: str, password: Optional[str] = None) -> list:
    """
    Ambil daftar koneksi yang ada di 9router.
    Returns: list of dict dengan field 'name', 'provider', 'id', dll.
    """
    global _9router_auth_token

    # Login jika password disediakan dan belum ada token
    if password and not _9router_auth_token:
        _9router_login(router_url, password)

    providers_url = f"{router_url.rstrip('/')}/api/providers"
    headers = {"User-Agent": "FlowCf/3.0"}
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
    account_id: str,
    api_key: str,
    email: str,
    check_duplicate: bool = True,
) -> dict:
    """
    Inject akun Cloudflare AI ke 9router.
    POST /api/providers dengan auth_token cookie.
    Returns: dict dengan status dan pesan.
    """
    global _9router_auth_token

    # Login jika password disediakan dan belum ada token
    if password and not _9router_auth_token:
        try:
            _9router_login(router_url, password)
        except RuntimeError as e:
            return {"success": False, "error": str(e)}

    # Cek duplikat jika diminta
    if check_duplicate:
        try:
            existing = get_9router_connections(router_url)
            for conn in existing:
                if conn.get("provider") == "cloudflare-ai" and conn.get("name") == email:
                    return {"success": False, "error": "duplicate", "message": f"Akun {email} sudah ada di 9router"}
        except Exception:
            pass  # Lanjutkan meskipun gagal cek duplikat

    # Prepare request
    providers_url = f"{router_url.rstrip('/')}/api/providers"
    payload = {
        "provider": "cloudflare-ai",
        "apiKey": api_key,
        "name": email,
        "priority": 1,
        "testStatus": "active",
        "providerSpecificData": {
            "accountId": account_id,
            "connectionProxyEnabled": False,
            "connectionProxyUrl": "",
            "connectionNoProxy": "",
        },
    }
    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "FlowCf/3.0",
    }
    if _9router_auth_token:
        headers["Cookie"] = f"auth_token={_9router_auth_token}"

    req = urllib.request.Request(
        providers_url,
        data=body,
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            return {"success": True, "data": data}
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
    workers: int = 2,
) -> dict:
    """
    Inject akun dari file cloudflare_api.txt ke 9router.
    Format file: account_id:apikey (satu per baris)
    Returns: dict dengan statistik inject.
    """
    if not os.path.exists(file_path):
        return {"success": False, "error": f"File tidak ditemukan: {file_path}"}

    # Baca file
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
                account_id, api_key = parts[0].strip(), parts[1].strip()
                if account_id and api_key:
                    entries.append((account_id, api_key))

    if not entries:
        return {"success": False, "error": "Tidak ada entry valid di file"}

    # Login ke 9router
    if password:
        try:
            _9router_login(router_url, password)
        except RuntimeError as e:
            return {"success": False, "error": str(e)}

    # Ambil koneksi yang ada untuk cek duplikat
    existing_names = set()
    try:
        existing = get_9router_connections(router_url)
        for conn in existing:
            if conn.get("provider") == "cloudflare-ai":
                existing_names.add(conn.get("name", ""))
    except Exception:
        pass

    # Filter entries yang belum ada di 9router
    entries_to_inject = []
    skipped = 0
    for account_id, api_key in entries:
        name = f"cf-{account_id[:8]}"
        if name in existing_names:
            skipped += 1
        else:
            entries_to_inject.append((account_id, api_key, name))

    if not entries_to_inject:
        return {
            "success": True,
            "total": len(entries),
            "injected": 0,
            "skipped": skipped,
            "failed": 0,
            "errors": [],
        }

    # Inject dengan multi-worker
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import threading

    results = {
        "total": len(entries),
        "injected": 0,
        "skipped": skipped,
        "failed": 0,
        "errors": [],
    }
    lock = threading.Lock()

    def inject_one(entry):
        account_id, api_key, name = entry
        result = inject_to_9router(
            router_url=router_url,
            password=None,  # Sudah login di atas
            account_id=account_id,
            api_key=api_key,
            email=name,
            check_duplicate=False,  # Sudah cek di atas
        )
        return (account_id, name, result)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(inject_one, entry): entry for entry in entries_to_inject}
        for future in as_completed(futures):
            account_id, name, result = future.result()
            with lock:
                if result["success"]:
                    results["injected"] += 1
                    existing_names.add(name)
                else:
                    results["failed"] += 1
                    results["errors"].append(f"{account_id}: {result.get('error', 'unknown')}")

    results["success"] = True
    return results


# ── Account Reader ──────────────────────────────────────

def read_accounts(file_path):
    """Baca akun dari account.txt (format: email:password)"""
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


# ── Clipboard Helpers ───────────────────────────────────
async def setup_clipboard_hook(page):
    """Intercept clipboard untuk capture teks"""
    try:
        await page.evaluate("""() => {
        window.__copiedText = '';
        if (navigator.clipboard) {
            const _wt = navigator.clipboard.writeText.bind(navigator.clipboard);
            navigator.clipboard.writeText = async (t) => { window.__copiedText = t; return _wt(t); };
        }
        const _ec = document.execCommand.bind(document);
        document.execCommand = (cmd, ...args) => {
            if (cmd === 'copy') {
                const s = window.getSelection();
                if (s) window.__copiedText = s.toString();
            }
            return _ec(cmd, ...args);
        };
    }""")
    except Exception:
        pass


async def get_copied_text(page):
    """Ambil teks terakhir yang di-copy"""
    try:
        return await page.evaluate("window.__copiedText || ''")
    except Exception:
        return ""


# ── Captcha Detection ───────────────────────────────────
async def detect_captcha(page):
    """Deteksi Cloudflare Turnstile / captcha"""
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
    """
    Deteksi captcha → pause & tunggu user solve manual.
    Maksimal tunggu timeout detik (default 3 menit).
    """
    has_captcha = await detect_captcha(page)


    if not has_captcha:
        return True


    fast_print(
        "\n  [bold yellow]![/]  ═══════════════════════════════════════════════════════\n"
        "  [bold yellow]![/]  CAPTCHA / TURNSTILE TERDETEKSI!\n"
        "  [bold yellow]![/]  Silakan solve captcha secara MANUAL di browser.\n"
        "  [bold yellow]![/]  Script otomatis melanjutkan setelah captcha selesai.\n"
        "  [bold yellow]![/]  ═══════════════════════════════════════════════════════\n",
        style="bold bright_yellow",
    )


    start = time.time()
    last_check = 0
    while (time.time() - start) < timeout:
        elapsed = int(time.time() - start)


        if elapsed - last_check >= 2:
            last_check = elapsed
            still_captcha = await detect_captcha(page)
            url = page.url
            on_dashboard = "dash.cloudflare.com" in url and "/login" not in url


            if not still_captcha or on_dashboard:
                fast_print(
                    f"  [bold green]+[/]  Captcha selesai! (setelah {elapsed}s)\n",
                    style="bold bright_green",
                )
                await asyncio.sleep(3)
                return True


            if elapsed > 0 and elapsed % 15 == 0:
                remaining = timeout - elapsed
                fast_print(
                    f"  [yellow]...[/]  Menunggu captcha... ({elapsed}s berlalu, {remaining}s tersisa)",
                    style="bright_yellow",
                )


        await asyncio.sleep(1)


    fast_print(
        "\n  [bold red]![/]  Timeout captcha! Mencoba melanjutkan...\n",
        style="bold bright_red",
    )
    return False


async def wait_for_captcha_on_page(page, page_desc="halaman", timeout=120):
    """Deteksi captcha di halaman apapun"""
    await asyncio.sleep(2)
    has_captcha = await detect_captcha(page)
    if not has_captcha:
        return True


    fast_print(
        f"\n  [bold yellow]![/]  CAPTCHA terdeteksi di {page_desc}! "
        f"Silakan solve di browser (timeout: {timeout}s)...\n",
        style="bold bright_yellow",
    )


    start = time.time()
    while (time.time() - start) < timeout:
        await asyncio.sleep(2)
        elapsed = int(time.time() - start)
        still_captcha = await detect_captcha(page)
        if not still_captcha:
            fast_print(
                f"  [bold green]+[/]  Captcha {page_desc} selesai! ({elapsed}s)\n",
                style="bold bright_green",
            )
            await asyncio.sleep(2)
            return True
        if elapsed > 0 and elapsed % 15 == 0:
            fast_print(
                f"  [yellow]...[/]  Menunggu captcha {page_desc}... ({elapsed}s)",
                style="bright_yellow",
            )


    fast_print(
        f"  [bold red]![/]  Timeout captcha {page_desc}, melanjutkan...\n",
        style="bold bright_red",
    )
    return False


# ── Google Login Handler ────────────────────────────────
async def handle_google_login(page, email, password):
    """Handle seluruh flow login Google OAuth"""


    step("> ", "Menunggu halaman Google...")
    await page.wait_for_url("**/accounts.google.com/**", timeout=60000)
    await asyncio.sleep(2)


    # Cek apakah ada email input langsung
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


    # Isi Email
        step("> ", f"Memasukkan email: {email}")
    email_input = page.locator('#identifierId')
    if await email_input.count() == 0:
        email_input = page.locator('input[type="email"]')
    if await email_input.count() > 0 and await email_input.first.is_visible():
        await email_input.first.click()
        await asyncio.sleep(0.2)
        await email_input.first.fill(email)
        await asyncio.sleep(0.3)


        # Klik Next
        step("> ", "Klik Next (email)...")
        next_btn = page.locator('#identifierNext')
        if await next_btn.count() > 0:
            await next_btn.click()
        else:
            await page.locator('span:text-is("Next")').first.click()
        await asyncio.sleep(3)


        # Cek error
        error_el = page.locator('.o6cuMc, .dEOOab, [data-error="true"]')
        if await error_el.count() > 0:
            err_text = await error_el.first.inner_text()
            if "find" in err_text.lower() or "tidak dapat menemukan" in err_text.lower():
                raise Exception(f"Google error: {err_text}")


    # Isi Password
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
    await asyncio.sleep(0.2)
    await password_input.first.fill(password)
    await asyncio.sleep(0.3)


    # Klik Next (password)
    step("> ", "Klik Next (password)...")
    next_btn = page.locator('#passwordNext')
    if await next_btn.count() > 0:
        await next_btn.click()
    else:
        await page.locator('span:text-is("Next")').first.click()
    await asyncio.sleep(2)


    # Handle "I understand" + "Continue" untuk akun GSuite baru
    step("> ", "Mengecek halaman interstitial GSuite baru...")
    await asyncio.sleep(1)

    # Klik "I understand" jika ada (akun baru GSuite)
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

        # Setelah klik "I understand", klik "Continue" jika ada
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
    else:
        step("[dim]>[/]", "Tidak ada halaman interstitial, lanjut...")

    # Handle phone verification (akun Google baru sering diminta verifikasi HP)
    await asyncio.sleep(1)
    current_url = page.url
    if "challenge" in current_url or "signin/v2" in current_url:
        await wait_for_page_ready(page, desc="Google challenge/verification", timeout=30000)
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
                "  [bold yellow]![/]  Solve MANUAL di browser (masukkan nomor + kode SMS).\n"
                "  [bold yellow]![/]  Script otomatis melanjutkan setelah selesai (timeout 180s).\n",
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
                    fast_print(
                        f"  [yellow]...[/]  Menunggu verifikasi HP... ({elapsed_pv}s)",
                        style="bright_yellow",
                    )
            else:
                step("!", "Timeout verifikasi HP, mencoba melanjutkan...")

    # Handle Google Workspace Terms of Service speedbump
    # URL: accounts.google.com/*/speedbump/workspacetermsofservice
    await asyncio.sleep(1)
    current_url = page.url
    if "speedbump" in current_url or "workspacetermsofservice" in current_url:
        step("[cyan]>[/]", "Halaman Google Workspace Terms...")
        await wait_for_page_ready(page, desc="Google Workspace Terms", timeout=30000)
        for _ in range(10):
            if "speedbump" not in page.url and "workspacetermsofservice" not in page.url:
                step("[cyan]>[/]", "Terms accepted, lanjut...")
                break
            for sel in [
                'button:has-text("Accept")',
                'span:text-is("Accept")',
                'button:has-text("I agree")',
                'span:text-is("I agree")',
                'button:has-text("Agree")',
                'span:text-is("Agree")',
                'button:has-text("Continue")',
                'span:text-is("Continue")',
                '[type="submit"]',
            ]:
                btn = page.locator(sel)
                if await btn.count() > 0 and await btn.first.is_visible():
                    step("[cyan]>[/]", f"Klik '{sel}' pada speedbump...")
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
                step("[dim]>[/]", "Tombol speedbump tidak ditemukan, tunggu...")
                await asyncio.sleep(3)

    # Handle 2FA — tunggu page ready dulu
    await wait_for_page_ready(page, desc="Google 2FA/verification", timeout=30000)
    current_url = page.url
    if "challenge" in current_url or "signin/v2" in current_url:
        step("!", "Halaman verifikasi/2FA, tunggu 10 detik...")
        await asyncio.sleep(10)


    # Klik Continue/Allow — loop sampai redirect ke Cloudflare atau OAuth callback
    step("[cyan]>[/]", "Mencari tombol Continue/Allow...")
    await wait_for_page_ready(page, desc="Google consent page", timeout=30000)
    for attempt in range(10):
        # Cek apakah sudah redirect (Cloudflare dashboard atau OAuth callback)
        try:
            cur = page.url
        except Exception:
            step("[cyan]>[/]", "Page closed (OAuth complete), lanjut...")
            break
        if "dash.cloudflare.com" in cur or "oidc.iam.cfapi.net" in cur:
            step("[cyan]>[/]", "Sudah redirect, lanjut...")
            break
        # Cari tombol Continue/Allow/Izinkan
        clicked = False
        try:
            for sel in [
                'span:text-is("Continue")',
                'button:has-text("Continue")',
                'span:text-is("Izinkan")',
                'button:has-text("Izinkan")',
                "#submit_approve_access",
                'button:has-text("Allow")',
            ]:
                btn = page.locator(sel)
                if await btn.count() > 0 and await btn.first.is_visible():
                    step("[cyan]>[/]", f"Klik Continue/Allow (attempt {attempt+1})...")
                    await btn.first.click()
                    clicked = True
                    break
        except Exception:
            pass  # page closed during search
        if not clicked:
            step("[dim]>[/]", "Tombol Continue/Allow tidak ditemukan, tunggu...")
        await asyncio.sleep(3)
        # Cek apakah sudah redirect
        try:
            cur = page.url
        except Exception:
            step("[cyan]>[/]", "Page closed, lanjut...")
            break
        if "dash.cloudflare.com" in cur or "oidc.iam.cfapi.net" in cur:
            step("[cyan]>[/]", "Redirect, lanjut...")
            break
    else:
        step("!", "Timeout menunggu redirect dari Google, lanjut...")


# ── API Token Creation (bypass UI) ─────────────────────
async def create_token_via_api(cookies, account_id, email):
    """
    Create Workers AI API token via Cloudflare Dashboard internal API.
    Uses dashboard session cookies (vses2, __cf_bm, __cf_logged_in).
    No browser dependency — pure HTTP, fast and resilient.
    Returns api_key string or None if API approach fails.
    """
    try:
        cookie_dict = {c["name"]: c["value"] for c in cookies} if isinstance(cookies, list) else cookies
        
        # Build cookie header string for httpx
        cookie_header = "; ".join(f"{k}={v}" for k, v in cookie_dict.items())
        
        if not cookie_dict.get("vses2"):
            raise Exception("vses2 session cookie not found — not logged in to dashboard")

        # Use dashboard internal API with session cookie
        api_base = "https://dash.cloudflare.com/api/v4"
        auth_headers = {
            "Content-Type": "application/json",
            "Cookie": cookie_header,
        }

        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            # Step 1: Fetch Workers AI permission group IDs
            step("> ", "Mengambil permission group IDs...")
            resp = await client.get(
                f"{api_base}/accounts/{account_id}/tokens/permission_groups",
                headers=auth_headers
            )
            if resp.status_code != 200:
                raise Exception(f"Permission groups API failed: {resp.status_code} {resp.text[:200]}")
            data = resp.json()
            if not data.get("success"):
                raise Exception(f"Permission groups API error: {data.get('errors', 'unknown')}")

            groups = data.get("result", [])
            read_id = next((g["id"] for g in groups if "Workers AI" in g.get("name", "") and "Read" in g.get("name", "")), None)
            write_id = next((g["id"] for g in groups if "Workers AI" in g.get("name", "") and ("Write" in g.get("name", "") or "Edit" in g.get("name", ""))), None)

            if not read_id or not write_id:
                group_names = [g.get("name", "") for g in groups]
                raise Exception(f"Workers AI permission groups not found. Available: {group_names[:20]}")

            step("> ", f"Workers AI groups: read={read_id}, write={write_id}")

            # Step 2: Create API Token
            step("> ", "Membuat API Token via API...")
            token_data = {
                "name": "Workers AI",
                "policies": [{
                    "effect": "allow",
                    "resources": {f"com.cloudflare.api.account.{account_id}": "*"},
                    "permission_groups": [
                        {"id": read_id},
                        {"id": write_id}
                    ]
                }]
            }

            resp = await client.post(
                f"{api_base}/accounts/{account_id}/tokens",
                headers=auth_headers,
                json=token_data
            )

            if resp.status_code != 200:
                raise Exception(f"Token creation API failed: {resp.status_code} {resp.text[:300]}")

            data = resp.json()
            if not data.get("success"):
                raise Exception(f"API returned error: {data.get('errors', 'unknown')}")

            token_value = data.get("result", {}).get("value")
            if not token_value:
                raise Exception(f"Token value not found. Response: {data}")

            step("[green]>[/]", f"API Token created via API: {token_value[:30]}...")
            return token_value

    except Exception as e:
        step("!", f"API approach failed: {e}")
        return None


# ── Main Processing ─────────────────────────────────────
async def process_account(context, email, password, index, total, dashboard_state=None, worker_id=1, register_mode=False):
    """Proses satu akun: login/register → buat token → copy credentials"""

    mode_label = "REGISTER" if register_mode else "LOGIN"
    fast_print(f"  [bold bright_cyan]>[/]  Akun {index}/{total} — {email} [Worker {worker_id}] [{mode_label}]", style="bold bright_cyan")


    def _update(stage: Stage, status: Status = Status.PROCESSING):
        if dashboard_state:
            dashboard_state.update_account(index, stage=stage, status=status)

    _update(Stage.INITIALIZE, Status.CONNECTING)


    page = await context.new_page()
    result = {"email": email, "password": password, "account_id": "ERROR", "api_key": "ERROR"}


    try:
        # 1. Cloudflare Login / Sign-up
        _update(Stage.OAUTH_REDIRECT, Status.CONNECTING)
        if register_mode:
            cf_url = "https://dash.cloudflare.com/sign-up"
            cf_desc = "Cloudflare Sign-up"
            step("> ", "Mode REGISTER: navigasi ke halaman sign-up...")
        else:
            cf_url = "https://dash.cloudflare.com/login"
            cf_desc = "Cloudflare Login"
        await goto_robust(page, cf_url, desc=cf_desc)


# 2. Klik Google
        _update(Stage.OAUTH_REDIRECT, Status.PROCESSING)
        if register_mode:
            step("> ", "Klik Google sign-up...")
        else:
            step("> ", "Klik Google login...")
        # Selector mencakup tombol "Continue with Google" (login) dan "Sign up with Google" (sign-up)
        google_btn = page.locator(
            'button:has-text("Continue with Google"), '
            'button:has-text("Sign up with Google"), '
            'a:has-text("Continue with Google"), '
            'a:has-text("Sign up with Google"), '
            'button:has-text("Google"), '
            'a:has-text("Google")'
        ).first
        try:
            await google_btn.click(force=True, timeout=10000)
        except Exception:
            try:
                await google_btn.evaluate("el => el.click()")
            except Exception:
                pass
        await page.wait_for_url("**/accounts.google.com/**", timeout=60000)


        # 3-4. Google Login
        _update(Stage.EXCHANGE_TOKEN, Status.PROCESSING)
        step("> ", "Login Google...")
        await handle_google_login(page, email, password)


        # 4b. Cek Captcha setelah Google Login
        await asyncio.sleep(1)
        await wait_for_captcha_or_continue(page, timeout=90)


# 5. Tunggu Cloudflare Dashboard
        _update(Stage.CREATE_SESSION, Status.REDIRECT)
        step("> ", "Redirect ke Cloudflare dashboard...")
        try:
            await page.wait_for_url(
                "https://dash.cloudflare.com/**",
                timeout=60000,
            )
        except Exception:
            if "dash.cloudflare.com" not in page.url:
                raise Exception(f"Tidak berhasil redirect ke Cloudflare. URL: {page.url}")

        # Handle OAuth callback URL (login/google?oidcJwt=...) — tunggu redirect ke dashboard
        if "login/google" in page.url:
            step("> ", "OAuth callback terdeteksi, tunggu redirect ke dashboard...")
            await wait_for_page_ready(page, desc="Cloudflare Dashboard", timeout=90000)
            await asyncio.sleep(3)
            # Coba tunggu sampai URL bukan login/google lagi
            for _ in range(20):
                if "login/google" not in page.url:
                    break
                await asyncio.sleep(2)


        step("[yellow]...[/]", "Halaman terdeteksi, menunggu SPA fully loaded...")
        await wait_for_page_ready(page, desc="Cloudflare Dashboard", timeout=90000)


        # Ekstrak Account ID dari URL
        url = page.url
        m = re.search(r"dash\.cloudflare\.com/([a-f0-9]+)/", url)
        cf_acc_id = m.group(1) if m else None


        if not cf_acc_id:
            step("[yellow]...[/]", "Account ID belum di URL, menunggu redirect account...")
            try:
                await page.wait_for_url(
                    "https://dash.cloudflare.com/[a-f0-9]*/**",
                    timeout=60000,
                )
            except Exception:
                pass
            m = re.search(r"dash\.cloudflare\.com/([a-f0-9]+)/", page.url)
            cf_acc_id = m.group(1) if m else None


        if not cf_acc_id:
            await asyncio.sleep(5)
            m = re.search(r"dash\.cloudflare\.com/([a-f0-9]+)/", page.url)
            cf_acc_id = m.group(1) if m else None


        if not cf_acc_id:
            raise Exception(
                f"Account ID tidak ditemukan di URL: {page.url}. "
                f"Pastikan login berhasil dan halaman dashboard sudah termuat."
            )

        step("[green]>[/]", f"Account ID ditemukan: {cf_acc_id}", "dari URL")

        # ── EXTRACT COOKIES + CLOSE BROWSER (no more UI needed) ──
        _update(Stage.GENERATE_API_KEY, Status.PROCESSING)
        step("> ", "Extract session cookies, close browser...")
        cookies = await context.cookies()
        await page.close()
        step("> ", "Browser closed, lanjut via API only")

        # ── API TOKEN CREATION (via REST API, no browser) ──
        api_key_val = await create_token_via_api(cookies, cf_acc_id, email)

        if not api_key_val:
            raise Exception("Gagal membuat token via API")

        result["api_key"] = api_key_val
        result["account_id"] = cf_acc_id
        result["success"] = True

        _update(Stage.SAVE_RESULT, Status.SUCCESS)
        step("[green]>[/]", f"Token created: {api_key_val[:30]}...")
        ok(f"AKUN #{index} BERHASIL! [Worker {worker_id}]")
        fast_print(f"    Account ID : {result['account_id']}")
        fast_print(f"    API Key    : {result['api_key']}")
        if dashboard_state:
            dashboard_state.finish_account(index, success=True)


    except Exception as e:
        fail(f"AKUN #{index} GAGAL: {e} [Worker {worker_id}]")
        result["success"] = False
        result["error"] = str(e)
        if dashboard_state:
            dashboard_state.finish_account(
                index, success=False, error_message=str(e),
            )
    finally:
        try:
            await page.close()
        except Exception:
            pass


    return result


# ── Robust Page Load Helpers ─────────────────────────────

async def goto_robust(page, url, desc="halaman", max_retries=3, timeout=120000):
    """
    goto() dengan retry + validasi konten.
    - Retry up to max_retries kali jika gagal
    - Tunggu 'load' state (bukan cuma domcontentloaded)
    - Validasi body tidak kosong setelah load
    - Backoff 5s antar retry
"""
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            step("> ", f"Navigasi ke {desc}...", f"attempt {attempt}/{max_retries}")
            if attempt == 1:
                await page.goto(url, wait_until="load", timeout=timeout)
            else:
                # Reload page instead of re-navigating (better for SPAs)
                await page.reload(wait_until="load", timeout=timeout)
            await asyncio.sleep(1)
            # Validasi halaman tidak blank
            body_text = await page.evaluate(
                "document.body ? document.body.innerText.trim().length : 0"
            )
            if body_text > 20:
                step("> ", f" {desc} loaded ({body_text} chars)", f"ok")
                return True
            else:
                step("!", f" {desc} blank ({body_text} chars), reload...")
                last_error = Exception(f"Halaman kosong: {body_text} chars")
        except Exception as e:
            step("!", f" {desc} gagal: {e}", f"retry {attempt}/{max_retries}")
            last_error = e
        if attempt < max_retries:
            await asyncio.sleep(5)
    raise last_error or Exception(f"Gagal load {desc} setelah {max_retries}x retry")


async def wait_for_page_ready(page, desc="halaman", timeout=60000):
    """
    Tunggu halaman benar-benar siap:
    1. networkidle (semua resource selesai)
    2. Body ada konten > 50 chars
    3. Jika timeout, tetap lanjut asal ada konten
    """
    # Step 1: networkidle
    try:
        await page.wait_for_load_state("networkidle", timeout=timeout)
        step("> ", f" {desc} network idle ok")
    except Exception:
        step("!", f" {desc} network idle timeout, lanjut...")

    # Step 2: validasi konten (retry up to 5x, reload jika blank 2x)
    blank_count = 0
    for attempt in range(1, 6):
        try:
            body_text = await page.evaluate(
                "document.body ? document.body.innerText.trim().length : 0"
            )
        except Exception:
            body_text = 0
            step("!", f" {desc} evaluate gagal (navigating?), retry...", f"attempt {attempt}/5")
        if body_text > 50:
            step("> ", f" {desc} konten siap ({body_text} chars)", f"attempt {attempt}")
            return True
        blank_count += 1
        if blank_count >= 2:
            step("!", f" {desc} blank 2x, reload page...", f"attempt {attempt}/5")
            try:
                await page.reload(wait_until="load", timeout=60000)
                await asyncio.sleep(2)
            except Exception as e:
                step("!", f" {desc} reload gagal: {e}", f"attempt {attempt}/5")
            blank_count = 0
        else:
            step("!", f" {desc} konten belum siap ({body_text} chars)", f"attempt {attempt}/5")
            await asyncio.sleep(3)
    # Last attempt: reload + tunggu ekstra
    try:
        await page.reload(wait_until="load", timeout=60000)
        await asyncio.sleep(5)
    except Exception:
        pass
    try:
        body_text = await page.evaluate(
            "document.body ? document.body.innerText.trim().length : 0"
        )
    except Exception:
        body_text = 0
    if body_text < 50:
        raise Exception(f"{desc} blank setelah 5x retry! ({body_text} chars)")
    step("> ", f" {desc} konten ok ({body_text} chars)", "final")
    return True


# ── Worker Function ──────────────────────────────────────
async def worker_task(account_index, email, password, state, browser, stealth, worker_id, register_mode=False):
    """Worker function: processes one account at a time."""
    ctx = await browser.new_context(
        permissions=["clipboard-read", "clipboard-write"],
        viewport={"width": 1366, "height": 768},
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
        ctx, email, password, account_index, state.total_accounts,
        dashboard_state=state, worker_id=worker_id, register_mode=register_mode,
    )
    await ctx.close()
    return r


# ── CLI Argument Parsing ────────────────────────────────
def parse_args():
    parser = argparse.ArgumentParser(
        description="Cloudflare Workers AI API Key Bot (Stealth Edition)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                          # Semua akun, 2 workers, headless
  python main.py 10                       # 10 akun pertama, 2 workers
  python main.py 10 4                     # 10 akun, 4 workers
  python main.py 10 4 --visible           # Tampilkan browser
  python main.py all 4                    # Semua akun, 4 workers
  python main.py 10 4 --inject-9router    # Inject ke 9router setelah buat API key
  python main.py all 2 --inject-9router --router-password MyPassword123

  # Inject dari file ke 9router (tanpa buat API key baru)
  python main.py --inject-from-file cloudflare_api.txt --router-password MyPassword123
  python main.py --inject-from-file cloudflare_api.txt 4 --router-password MyPassword123

  # Mode registrasi: buat akun Cloudflare baru via Google
  python main.py 10 4 --register
  python main.py 10 4 --register --visible
  python main.py all 4 --register --inject-9router --router-password MyPassword123
        """,
    )
    parser.add_argument(
        "jumlah",
        nargs="?",
        default="all",
        help="Jumlah akun yang diproses (default: all)",
    )
    parser.add_argument(
        "workers",
        nargs="?",
        type=int,
        default=2,
        help="Jumlah worker/thread paralel (default: 2)",
    )
    parser.add_argument(
        "-a", "--accounts",
        type=str, default=None,
        help="Path to accounts file (default: account.txt)",
    )
    parser.add_argument(
        "-o", "--output",
        type=str, default=None,
        help="Path to output file (default: cloudflare_api.txt)",
    )
    parser.add_argument(
        "-d", "--delay",
        type=float, default=3.0,
        help="Delay between batches in seconds (default: 3)",
    )
    parser.add_argument(
        "--visible",
        action="store_true",
        help="Tampilkan browser (default: headless)",
    )
    parser.add_argument(
        "--inject-9router",
        action="store_true",
        help="Inject akun ke 9router setelah API key berhasil dibuat",
    )
    parser.add_argument(
        "--router-url",
        type=str,
        default="http://localhost:20128",
        help="URL 9router server (default: http://localhost:20128)",
    )
    parser.add_argument(
        "--router-password",
        type=str,
        default=None,
        help="Password 9router dashboard (opsional, auto-login jika diisi)",
    )
    parser.add_argument(
        "--inject-from-file",
        type=str,
        default=None,
        metavar="FILE",
        help="Inject dari file cloudflare_api.txt ke 9router (format: account_id:apikey)",
    )
    parser.add_argument(
        "--register",
        action="store_true",
        help="Mode registrasi: sign-up akun Cloudflare baru via Google (bukan login)",
    )
    return parser.parse_args()


# ── Entry Point ─────────────────────────────────────────
async def main():
    args = parse_args()

    NUM_WORKERS = args.workers
    DELAY_BETWEEN_ACCOUNTS = args.delay
    # Mode register pakai registerakun.txt sebagai default; mode login pakai account.txt
    default_accounts_file = "registerakun.txt" if args.register else "account.txt"
    accounts_file = args.accounts or os.path.join(WORKSPACE, default_accounts_file)
    output_file = args.output or os.path.join(WORKSPACE, "cloudflare_api.txt")
    log_file = os.path.join(WORKSPACE, "account.json")
    log_example = os.path.join(WORKSPACE, "account.json.example")

    # Auto-init account.json dari template example jika belum ada
    if not os.path.exists(log_file):
        if os.path.exists(log_example):
            import shutil
            try:
                shutil.copy2(log_example, log_file)
                info(f"account.json dibuat dari template: {log_example}")
            except Exception as e:
                fail(f"Gagal menyalin account.json.example: {e}")
        else:
            # Fallback: buat file kosong jika example juga tidak ada
            try:
                with open(log_file, "w", encoding="utf-8") as f:
                    json.dump({}, f)
                info("account.json dibuat (kosong)")
            except Exception as e:
                fail(f"Gagal membuat account.json: {e}")

    headless = not args.visible  # default headless, --visible to show browser

    # Mode inject dari file (tidak perlu buat API key baru)
    if args.inject_from_file:
        file_path = args.inject_from_file
        if not os.path.isabs(file_path):
            file_path = os.path.join(WORKSPACE, file_path)

        # Saat --inject-from-file, positional pertama = workers (bukan jumlah)
        inject_workers = args.workers
        if args.jumlah != "all":
            try:
                inject_workers = int(args.jumlah)
            except ValueError:
                pass

        print()
        rule("\u2501")
        fast_print("  INJECT KE 9ROUTER DARI FILE", style="bold bright_cyan")
        rule("\u2501")
        print()
        info(f"File: {file_path}")
        info(f"9router: {args.router_url}")
        info(f"Workers: {inject_workers}")
        print()

        result = inject_from_file(
            file_path=file_path,
            router_url=args.router_url,
            password=args.router_password,
            workers=inject_workers,
        )

        if not result["success"]:
            fail(result["error"])
            return

        # Tampilkan hasil
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
        rule("\u2501")
        fast_print("  SELESAI", style="bold bright_green")
        rule("\u2501")
        print()
        return

    # Deteksi IP publik
    public_ip = get_public_ip()

    # Tampilkan mode
    if args.register:
        info("MODE: REGISTER (sign-up akun Cloudflare baru via Google)")
    else:
        info("MODE: LOGIN (akun Cloudflare yang sudah terdaftar)")

    # Baca akun
    if not os.path.exists(accounts_file):
        fail(f"File akun tidak ditemukan: {accounts_file}")
        return

    accounts = read_accounts(accounts_file)
    if not accounts:
        fail("Tidak ada akun valid di account.txt")
        return

    # Load processed emails from account.json
    processed_emails = {}
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                processed_emails = json.load(f)
        except Exception:
            processed_emails = {}
    info(f"{len(processed_emails)} akun sudah diproses sebelumnya")

    # Filter out already processed emails
    original_count = len(accounts)
    accounts = [(e, p) for e, p in accounts if e not in processed_emails]
    skipped = original_count - len(accounts)
    if skipped > 0:
        info(f"{skipped} akun dilewati (sudah diproses)")
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

    start_time = time.time()

    # Inisialisasi dashboard state
    state = DashboardState(len(accounts), num_workers=NUM_WORKERS, public_ip=public_ip)

    # Inisialisasi playwright-stealth
    stealth = Stealth()

    # Bagi akun menjadi batch (2 akun per batch)
    batches = []
    for i in range(0, len(accounts), NUM_WORKERS):
        batch = [(i + j + 1, accounts[i + j][0], accounts[i + j][1])
                 for j in range(min(NUM_WORKERS, len(accounts) - i))]
        batches.append(batch)

    total_batches = len(batches)
    out = output_file

    # Buka file cloudflare_api.txt dalam mode append (pertahankan data lama)
    if not os.path.exists(out):
        with open(out, "w", encoding="utf-8") as f:
            pass

    async with async_playwright() as p:
        global _live_mode
        _live_mode = True

        with Live(generate_layout(state), refresh_per_second=2, auto_refresh=False) as live:
            async def update_dashboard():
                while state.get_completed_count() < len(accounts):
                    live.update(generate_layout(state), refresh=True)
                    await asyncio.sleep(0.5)
                live.update(generate_layout(state), refresh=True)

            dashboard_task = asyncio.ensure_future(update_dashboard())

            for batch_idx, batch in enumerate(batches):
                batch_num = batch_idx + 1
                _log_buffer.clear()

                fast_print(f"  [bold bright_cyan]>[/]  Batch {batch_num}/{total_batches} — Memproses {len(batch)} akun...",
                           style="bold bright_cyan")

                # Buat browser BARU untuk setiap batch (bersih tanpa jejak/cookies)
                fresh_browser = await p.chromium.launch(
                    headless=headless,
                    args=BROWSER_ARGS,
                )

                # Jalankan 2 worker secara paralel dalam 1 batch
                batch_tasks = []
                for idx, email, pwd in batch:
                    wid = (idx - 1) % NUM_WORKERS + 1
                    state.start_account(idx, email, wid)
                    task = asyncio.create_task(worker_task(idx, email, pwd, state, fresh_browser, stealth, wid, register_mode=args.register))
                    batch_tasks.append(task)

                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

                # Tutup browser batch ini (hilangkan semua jejak/cookies)
                await fresh_browser.close()

                # Simpan hasil batch ini
                with open(out, "a", encoding="utf-8") as f:
                    for r in batch_results:
                        if isinstance(r, Exception):
                            continue
                        if isinstance(r, dict) and r.get("success", False):
                            f.write(f"{r['account_id']}:{r['api_key']}\n")

                # Inject ke 9router jika diminta
                if args.inject_9router:
                    for r in batch_results:
                        if isinstance(r, Exception):
                            continue
                        if isinstance(r, dict) and r.get("success", False):
                            result = inject_to_9router(
                                router_url=args.router_url,
                                password=args.router_password,
                                account_id=r["account_id"],
                                api_key=r["api_key"],
                                email=r.get("email", ""),
                            )
                            if result["success"]:
                                fast_print(f"  [bold green]>[/]  Injected ke 9router: {r.get('email', '')}",
                                           style="bold green")
                            else:
                                fast_print(f"  [bold red]x[/]  Gagal inject 9router: {result['error']}",
                                           style="bold red")

                # Update account.json log + handle register mode errors
                register_error_file = os.path.join(WORKSPACE, "account.txt")
                for r in batch_results:
                    if isinstance(r, Exception):
                        continue
                    if not isinstance(r, dict):
                        continue
                    email = r.get("email", "")
                    if not email:
                        continue
                    is_success = r.get("success", False)

                    if args.register and not is_success:
                        # Mode register + error: tulis ke account.txt untuk proses manual,
                        # JANGAN tulis ke account.json
                        pwd = r.get("password", "")
                        try:
                            with open(register_error_file, "a", encoding="utf-8") as f:
                                f.write(f"{email}:{pwd}\n")
                            step("[yellow]>[/]", f"Akun error dipindahkan ke account.txt: {email}")
                        except Exception as e:
                            fail(f"Gagal menulis ke account.txt: {e}")
                    else:
                        # Sukses (semua mode) atau error mode login: catat di account.json
                        processed_emails[email] = {
                            "success": is_success,
                            "account_id": r.get("account_id", ""),
                            "api_key": r.get("api_key", ""),
                            "error": r.get("error", ""),
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        }
                try:
                    with open(log_file, "w", encoding="utf-8") as f:
                        json.dump(processed_emails, f, indent=2, ensure_ascii=False)
                except Exception as e:
                    fail(f"Gagal simpan account.json: {e}")

                fast_print(f"  [bold green]>[/]  Batch {batch_num}/{total_batches} selesai — Tersimpan ke cloudflare_api.txt",
                           style="bold bright_green")

                # Delay antar batch (kecuali batch terakhir)
                if batch_idx < total_batches - 1:
                    fast_print(f"  [yellow]>[/]  Menunggu {DELAY_BETWEEN_ACCOUNTS}s sebelum batch berikutnya...",
                               style="bright_yellow")
                    await asyncio.sleep(DELAY_BETWEEN_ACCOUNTS)

            await dashboard_task

        _live_mode = False
    
    total_time = time.time() - start_time


    # Ringkasan
    print()
    rule("\u2501")
    fast_print("  RINGKASAN HASIL", style="bold bright_white")
    rule("\u2501")
    print()

    ok_count = state.success_count
    fail_count = state.failed_count
    total = state.get_completed_count()
    success_rate = state.get_success_rate()

    print(f"  Total Akun  : {total}")
    print(f"  Total Batch : {total_batches}")
    print(f"  + Berhasil  : {ok_count}")
    print(f"  x Gagal     : {fail_count}")
    print(f"  Rate      : {success_rate:.1f}%")
    print()

    # Daftar akun SUKSES
    success_emails = []
    fail_emails = []
    for idx in state.completed_accounts:
        if idx in state.accounts:
            account = state.accounts[idx]
            if account.status == Status.SUCCESS:
                success_emails.append((idx, account.email, account.elapsed_ms))
            else:
                error_msg = account.error_message or "Unknown error"
                fail_emails.append((idx, account.email, error_msg))

    if success_emails:
        fast_print("  AKUN BERHASIL:", style="bold green")
        for idx, email, elapsed in success_emails:
            print(f"    + {idx}. {email}  ({elapsed}ms)")
        print()

    if fail_emails:
        fast_print("  AKUN GAGAL:", style="bold red")
        for idx, email, error_msg in fail_emails:
            print(f"    x {idx}. {email}")
            print(f"         Error: {error_msg}")
        if args.register:
            print()
            info("Akun gagal (register mode) sudah dipindahkan ke account.txt")
            info("Proses manual dengan: python main.py")
        print()

    print(f"  Tersimpan di: {out}")
    print(f"  Log akun   : {log_file}")
    if args.inject_9router:
        print(f"  9router    : {args.router_url} (injected)")
    print()
    fast_print(f"  Total waktu: {total_time:.1f}s (rata-rata {total_time / len(accounts):.1f}s/akun)", style="bright_cyan")
    print()
    rule("\u2501")
    fast_print("  SELESAI", style="bold bright_green")
    rule("\u2501")
    print()


if __name__ == "__main__":
    asyncio.run(main())