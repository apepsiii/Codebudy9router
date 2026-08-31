"""
V2Fun.ai Google OAuth Login - Multi-Account Automation
Automatically login multiple Google accounts, complete survey, and extract JWT tokens

Format account.txt:
email1@gmail.com|password1
email2@gmail.com|password2
email3@gmail.com|password3
"""

import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright, Page, BrowserContext
from playwright_stealth import Stealth
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich import box

console = Console()

# Survey answers
SURVEY_ANSWERS = {
    "describe_you": "ecommerce",  # Options: ecommerce, aitool, student
    "use_scenarios": "game",  # Options: game, virtual, interior, education
    "plan_to_use": "personal use",  # Options: personal use, commercial use
    "hear_about": "search engine"  # Options: search engine, youtube, discord, chatgpt
}

# Initialize stealth
stealth = Stealth()


class V2FunGoogleLogin:
    def __init__(self, email: str, password: str, account_number: int, total_accounts: int):
        self.email = email
        self.password = password
        self.account_number = account_number
        self.total_accounts = total_accounts
        self.tokens = {}
        self.cookies = []
        self.local_storage = {}
        self.success = False
        
    def print_header(self):
        """Print account header"""
        console.print("\n" + "="*80, style="cyan")
        console.print(f"[bold cyan]Account {self.account_number}/{self.total_accounts}: {self.email}[/bold cyan]")
        console.print("="*80 + "\n", style="cyan")
    
    def print_step(self, step: str, status: str = "info"):
        """Print step with status"""
        icons = {
            "info": "[*]",
            "success": "[+]",
            "error": "[!]",
            "warning": "[~]",
            "progress": "[>]"
        }
        colors = {
            "info": "cyan",
            "success": "green",
            "error": "red",
            "warning": "yellow",
            "progress": "blue"
        }
        icon = icons.get(status, "•")
        color = colors.get(status, "white")
        console.print(f"{icon} {step}", style=color)
    
    async def wait_and_click(self, page: Page, selector: str, timeout: int = 10000, description: str = ""):
        """Wait for element and click"""
        try:
            await page.wait_for_selector(selector, timeout=timeout)
            await page.click(selector)
            if description:
                self.print_step(f"Clicked: {description}", "success")
            return True
        except Exception as e:
            if description:
                self.print_step(f"Failed to click {description}: {str(e)[:50]}", "error")
            return False
    
    async def fill_input(self, page: Page, selector: str, value: str, timeout: int = 10000, description: str = ""):
        """Wait for input and fill"""
        try:
            await page.wait_for_selector(selector, timeout=timeout)
            await page.fill(selector, value)
            if description:
                self.print_step(f"Filled: {description}", "success")
            return True
        except Exception as e:
            if description:
                self.print_step(f"Failed to fill {description}: {str(e)[:50]}", "error")
            return False
    
    async def handle_google_login_popup(self, popup: Page, main_page: Page):
        """Handle Google OAuth login flow in popup window"""
        self.print_step("Starting Google OAuth login...", "progress")
        
        # Prevent popup from closing prematurely by listening to beforeunload
        try:
            await popup.evaluate("""() => {
                window.preventEarlyClose = true;
            }""")
        except:
            pass
        
        try:
            await popup.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(2)
            await popup.wait_for_load_state("networkidle", timeout=10000)
            self.print_step("Google OAuth popup loaded", "success")
            
            # Check if we're on Google accounts page
            current_url = popup.url
            self.print_step(f"Current URL: {current_url[:60]}...", "info")
            
            if "accounts.google.com" not in current_url:
                await popup.wait_for_url("**/accounts.google.com/**", timeout=10000)
            self.print_step("Google login page loaded", "success")
            
            # Enter email - try multiple selectors
            await asyncio.sleep(3)
            email_selectors = [
                'input[type="email"]',
                'input[name="identifier"]',
                'input[id="identifierId"]',
                '#identifierId',
                'input[aria-label*="email"]',
                'input[aria-label*="Email"]'
            ]
            
            email_filled = False
            for selector in email_selectors:
                try:
                    await popup.wait_for_selector(selector, timeout=5000, state="visible")
                    await popup.fill(selector, self.email)
                    self.print_step(f"Filled email using: {selector}", "success")
                    email_filled = True
                    break
                except:
                    continue
            
            if not email_filled:
                self.print_step("Could not find email input field", "error")
                # Take screenshot for debugging
                await popup.screenshot(path="v2fun_data/debug_email_page.png")
                self.print_step("Screenshot saved to v2fun_data/debug_email_page.png", "info")
                return False
            
            await asyncio.sleep(2)
            
            # Click Next button or press Enter
            try:
                next_button_selectors = [
                    'button:has-text("Next")',
                    'button:has-text("Berikutnya")',
                    '#identifierNext',
                    'button[type="button"]'
                ]
                
                button_clicked = False
                for selector in next_button_selectors:
                    try:
                        if await popup.locator(selector).count() > 0:
                            await popup.click(selector)
                            self.print_step("Clicked Next button", "success")
                            button_clicked = True
                            break
                    except:
                        continue
                
                if not button_clicked:
                    await popup.keyboard.press("Enter")
                    self.print_step("Pressed Enter to submit email", "success")
            except:
                await popup.keyboard.press("Enter")
                self.print_step("Pressed Enter to submit email", "success")
            
            # Wait for password page
            await asyncio.sleep(5)
            
            # Enter password - try multiple selectors
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'input[aria-label*="password"]',
                'input[aria-label*="Password"]'
            ]
            
            password_filled = False
            for selector in password_selectors:
                try:
                    await popup.wait_for_selector(selector, timeout=5000, state="visible")
                    await popup.fill(selector, self.password)
                    self.print_step(f"Filled password using: {selector}", "success")
                    password_filled = True
                    break
                except:
                    continue
            
            if not password_filled:
                self.print_step("Could not find password input field", "error")
                await popup.screenshot(path="v2fun_data/debug_password_page.png")
                self.print_step("Screenshot saved to v2fun_data/debug_password_page.png", "info")
                return False
            
            await asyncio.sleep(2)
            
            # Click Next button or press Enter
            try:
                next_button_selectors = [
                    'button:has-text("Next")',
                    'button:has-text("Berikutnya")',
                    '#passwordNext',
                    'button[type="button"]'
                ]
                
                button_clicked = False
                for selector in next_button_selectors:
                    try:
                        if await popup.locator(selector).count() > 0:
                            await popup.click(selector)
                            self.print_step("Clicked Next button", "success")
                            button_clicked = True
                            break
                    except:
                        continue
                
                if not button_clicked:
                    await popup.keyboard.press("Enter")
                    self.print_step("Pressed Enter to submit password", "success")
            except:
                await popup.keyboard.press("Enter")
                self.print_step("Pressed Enter to submit password", "success")
            
            # Wait for potential 2FA, consent screen, or welcome screen
            await asyncio.sleep(8)
            
            # Check for "Welcome to your new account" or GSuite onboarding
            try:
                # Check if we're on a welcome/onboarding page
                page_content = await popup.content()
                
                welcome_indicators = [
                    "Welcome to your new account",
                    "welcome to your account",
                    "Get started with",
                    "Mulai dengan"
                ]
                
                is_welcome_page = any(indicator.lower() in page_content.lower() for indicator in welcome_indicators)
                
                if is_welcome_page:
                    self.print_step("Detected GSuite welcome screen", "info")
                    
                    # Try multiple selectors for "I understand" or similar buttons
                    understand_selectors = [
                        'button:has-text("I understand")',
                        'button:has-text("Understand")',
                        'button:has-text("Got it")',
                        'button:has-text("Next")',
                        'button:has-text("Continue")',
                        'button:has-text("Saya mengerti")',
                        'button:has-text("Mengerti")',
                        'button:has-text("Lanjutkan")',
                        '[role="button"]:has-text("I understand")',
                        '[role="button"]:has-text("Understand")',
                        '[role="button"]:has-text("Got it")',
                        'button[type="button"]',
                        'div[role="button"]'
                    ]
                    
                    clicked = False
                    for selector in understand_selectors:
                        try:
                            element_count = await popup.locator(selector).count()
                            if element_count > 0:
                                # Get the first visible button
                                await popup.click(selector, timeout=5000)
                                self.print_step(f"Clicked welcome button: {selector}", "success")
                                clicked = True
                                await asyncio.sleep(3)
                                break
                        except Exception as e:
                            continue
                    
                    if not clicked:
                        self.print_step("Could not find welcome button, trying generic button", "warning")
                        
                        # Take screenshot for debugging
                        try:
                            screenshot_path = f"v2fun_data/debug_welcome_screen_{self.email.replace('@', '_at_').replace('.', '_')}.png"
                            await popup.screenshot(path=screenshot_path)
                            self.print_step(f"Screenshot saved: {screenshot_path}", "info")
                        except:
                            pass
                        
                        # Try to click any visible button as fallback
                        try:
                            await popup.evaluate("""() => {
                                const buttons = document.querySelectorAll('button');
                                for (let btn of buttons) {
                                    if (btn.offsetParent !== null) {
                                        btn.click();
                                        return true;
                                    }
                                }
                                return false;
                            }""")
                            self.print_step("Clicked generic button via JavaScript", "success")
                            await asyncio.sleep(3)
                        except Exception as e:
                            self.print_step(f"Could not click any button: {str(e)[:50]}", "warning")
                            
                            # Last resort: try pressing Enter
                            try:
                                await popup.keyboard.press("Enter")
                                self.print_step("Pressed Enter as fallback", "info")
                                await asyncio.sleep(3)
                            except:
                                pass
                    
                    # Additional wait after handling welcome screen
                    await asyncio.sleep(3)
            except Exception as e:
                self.print_step(f"Welcome screen check: {str(e)[:80]}", "info")
            
            # Check for "Welcome to your new account" popup / GSuite welcome screen
            try:
                welcome_selectors = [
                    'button:has-text("I understand")',
                    'button:has-text("Understand")',
                    'button:has-text("Got it")',
                    'button:has-text("Saya mengerti")',
                    'button:has-text("Mengerti")',
                    '[role="button"]:has-text("I understand")',
                    '[role="button"]:has-text("Understand")'
                ]
                
                welcome_clicked = False
                for selector in welcome_selectors:
                    try:
                        if await popup.locator(selector).count() > 0:
                            await popup.click(selector, timeout=5000)
                            self.print_step("Clicked: Welcome screen (I understand)", "success")
                            welcome_clicked = True
                            await asyncio.sleep(3)
                            break
                    except:
                        continue
                
                if welcome_clicked:
                    self.print_step("GSuite welcome screen handled", "success")
            except Exception as e:
                self.print_step("No GSuite welcome screen", "info")
            
            # Check for consent/continue button
            try:
                consent_selectors = [
                    'button:has-text("Continue")',
                    'button:has-text("Allow")',
                    'button:has-text("Izinkan")',
                    'button:has-text("Setuju")',
                    '[role="button"]:has-text("Continue")',
                    '[role="button"]:has-text("Allow")'
                ]
                
                for selector in consent_selectors:
                    try:
                        if await popup.locator(selector).count() > 0:
                            await popup.click(selector)
                            self.print_step("Consent given", "success")
                            break
                    except:
                        continue
            except Exception as e:
                self.print_step("No consent screen (already authorized)", "info")
            
            # Wait for redirect back to V2Fun (check URL change)
            self.print_step("Waiting for OAuth completion...", "progress")
            try:
                # Wait for URL to change to v2fun.ai (indicates successful OAuth)
                max_wait = 30  # 30 seconds max
                for i in range(max_wait):
                    current_url = popup.url
                    if "v2fun.ai" in current_url or popup.is_closed():
                        self.print_step("OAuth redirect detected", "success")
                        break
                    await asyncio.sleep(1)
                
                # Wait a bit more to ensure token is set
                if not popup.is_closed():
                    await asyncio.sleep(3)
                    self.print_step("Waiting for token synchronization...", "progress")
                
                # Now wait for popup to close naturally or close it
                try:
                    await popup.wait_for_event("close", timeout=10000)
                    self.print_step("OAuth popup closed naturally", "success")
                except:
                    self.print_step("Popup still open, closing manually...", "info")
                    try:
                        if not popup.is_closed():
                            await popup.close()
                            self.print_step("Popup closed manually", "success")
                    except Exception as e:
                        self.print_step(f"Popup already closed: {str(e)[:50]}", "info")
            except Exception as e:
                self.print_step(f"OAuth completion check: {str(e)[:80]}", "warning")
                # Try to close popup if still open
                try:
                    if not popup.is_closed():
                        await popup.close()
                except:
                    pass
            
            # Wait for main page to update after OAuth
            await asyncio.sleep(5)
            
            self.print_step("Successfully logged in with Google!", "success")
            return True
            
        except Exception as e:
            self.print_step(f"Google login failed: {str(e)[:100]}", "error")
            # Take screenshot for debugging
            try:
                await popup.screenshot(path="v2fun_data/debug_error_page.png")
                self.print_step("Error screenshot saved to v2fun_data/debug_error_page.png", "info")
            except:
                pass
            return False
    
    async def handle_survey(self, page: Page):
        """Handle post-login survey popup"""
        self.print_step("Checking for survey popup...", "progress")
        
        try:
            # Wait for survey modal to appear
            await asyncio.sleep(5)
            
            # Question 1: Which of the following best describes you?
            self.print_step("Q1: Which best describes you?", "info")
            q1_selectors = [
                f'text="{SURVEY_ANSWERS["describe_you"]}"',
                f'button:has-text("{SURVEY_ANSWERS["describe_you"]}")',
                f'[data-value="{SURVEY_ANSWERS["describe_you"]}"]',
                f'[role="radio"]:has-text("{SURVEY_ANSWERS["describe_you"]}")',
                f'div:has-text("{SURVEY_ANSWERS["describe_you"]}")'
            ]
            
            clicked = False
            for selector in q1_selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        await page.click(selector, timeout=5000)
                        self.print_step(f"Clicked Q1: {SURVEY_ANSWERS['describe_you']}", "success")
                        clicked = True
                        break
                except:
                    continue
            
            if not clicked:
                self.print_step("Q1 option not found, may be optional", "warning")
            
            await asyncio.sleep(2)
            
            # Click Next/Continue button
            next_buttons = [
                'button:has-text("Next")',
                'button:has-text("Continue")',
                'button:has-text("Berikutnya")',
                'button:has-text("Lanjut")',
                'button[type="submit"]'
            ]
            
            for btn in next_buttons:
                try:
                    if await page.locator(btn).count() > 0:
                        await page.click(btn, timeout=5000)
                        self.print_step("Clicked Next button", "success")
                        break
                except:
                    continue
            
            await asyncio.sleep(3)
            
            # Question 2: What scenarios do you plan to use V2Fun for?
            self.print_step("Q2: Use scenarios", "info")
            q2_selectors = [
                f'text="{SURVEY_ANSWERS["use_scenarios"]}"',
                f'button:has-text("{SURVEY_ANSWERS["use_scenarios"]}")',
                f'[data-value="{SURVEY_ANSWERS["use_scenarios"]}"]',
                f'[role="checkbox"]:has-text("{SURVEY_ANSWERS["use_scenarios"]}")',
                f'div:has-text("{SURVEY_ANSWERS["use_scenarios"]}")'
            ]
            
            clicked = False
            for selector in q2_selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        await page.click(selector, timeout=5000)
                        self.print_step(f"Clicked Q2: {SURVEY_ANSWERS['use_scenarios']}", "success")
                        clicked = True
                        break
                except:
                    continue
            
            if not clicked:
                self.print_step("Q2 option not found, may be optional", "warning")
            
            await asyncio.sleep(2)
            
            # Click Next/Continue
            for btn in next_buttons:
                try:
                    if await page.locator(btn).count() > 0:
                        await page.click(btn, timeout=5000)
                        self.print_step("Clicked Next button", "success")
                        break
                except:
                    continue
            
            await asyncio.sleep(3)
            
            # Question 3: How do you plan to use V2Fun?
            self.print_step("Q3: How to use", "info")
            q3_selectors = [
                f'text="{SURVEY_ANSWERS["plan_to_use"]}"',
                f'button:has-text("{SURVEY_ANSWERS["plan_to_use"]}")',
                f'[data-value="{SURVEY_ANSWERS["plan_to_use"]}"]',
                f'[role="radio"]:has-text("{SURVEY_ANSWERS["plan_to_use"]}")',
                f'div:has-text("{SURVEY_ANSWERS["plan_to_use"]}")'
            ]
            
            clicked = False
            for selector in q3_selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        await page.click(selector, timeout=5000)
                        self.print_step(f"Clicked Q3: {SURVEY_ANSWERS['plan_to_use']}", "success")
                        clicked = True
                        break
                except:
                    continue
            
            if not clicked:
                self.print_step("Q3 option not found, may be optional", "warning")
            
            await asyncio.sleep(2)
            
            # Click Next/Continue
            for btn in next_buttons:
                try:
                    if await page.locator(btn).count() > 0:
                        await page.click(btn, timeout=5000)
                        self.print_step("Clicked Next button", "success")
                        break
                except:
                    continue
            
            await asyncio.sleep(3)
            
            # Question 4: Where did you hear about V2Fun?
            self.print_step("Q4: Hear about", "info")
            q4_selectors = [
                f'text="{SURVEY_ANSWERS["hear_about"]}"',
                f'button:has-text("{SURVEY_ANSWERS["hear_about"]}")',
                f'[data-value="{SURVEY_ANSWERS["hear_about"]}"]',
                f'[role="radio"]:has-text("{SURVEY_ANSWERS["hear_about"]}")',
                f'div:has-text("{SURVEY_ANSWERS["hear_about"]}")'
            ]
            
            clicked = False
            for selector in q4_selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        await page.click(selector, timeout=5000)
                        self.print_step(f"Clicked Q4: {SURVEY_ANSWERS['hear_about']}", "success")
                        clicked = True
                        break
                except:
                    continue
            
            if not clicked:
                self.print_step("Q4 option not found, may be optional", "warning")
            
            await asyncio.sleep(2)
            
            # Click "Get Started" or final submit button
            final_buttons = [
                'button:has-text("Get Started")',
                'button:has-text("Get started")',
                'button:has-text("Submit")',
                'button:has-text("Finish")',
                'button:has-text("Complete")',
                'button:has-text("Done")',
                'button[type="submit"]'
            ]
            
            for button in final_buttons:
                try:
                    if await page.locator(button).count() > 0:
                        await page.click(button, timeout=5000)
                        self.print_step(f"Clicked: {button}", "success")
                        break
                except:
                    continue
            
            await asyncio.sleep(3)
            self.print_step("Survey completed!", "success")
            return True
            
        except Exception as e:
            self.print_step(f"Survey handling: {str(e)[:80]}", "warning")
            self.print_step("Continuing anyway (survey may be optional)", "info")
            return False
    
    async def extract_tokens(self, page: Page, context: BrowserContext):
        """Extract JWT tokens from cookies, localStorage, and network requests"""
        self.print_step("Extracting authentication tokens...", "progress")
        
        try:
            # Get cookies
            self.cookies = await context.cookies()
            self.print_step(f"Extracted {len(self.cookies)} cookies", "success")
            
            # Get localStorage
            self.local_storage = await page.evaluate("""() => {
                let storage = {};
                for (let i = 0; i < localStorage.length; i++) {
                    let key = localStorage.key(i);
                    storage[key] = localStorage.getItem(key);
                }
                return storage;
            }""")
            self.print_step(f"Extracted {len(self.local_storage)} localStorage items", "success")
            
            # Get sessionStorage
            session_storage = await page.evaluate("""() => {
                let storage = {};
                for (let i = 0; i < sessionStorage.length; i++) {
                    let key = sessionStorage.key(i);
                    storage[key] = sessionStorage.getItem(key);
                }
                return storage;
            }""")
            self.print_step(f"Extracted {len(session_storage)} sessionStorage items", "success")
            
            # Find JWT tokens
            # Search in cookies
            for cookie in self.cookies:
                if 'token' in cookie['name'].lower() or 'auth' in cookie['name'].lower():
                    self.tokens[f"cookie_{cookie['name']}"] = cookie['value']
                    self.print_step(f"Found token in cookie: {cookie['name']}", "success")
            
            # Search in localStorage
            for key, value in self.local_storage.items():
                if 'token' in key.lower() or 'auth' in key.lower():
                    self.tokens[f"localStorage_{key}"] = value
                    self.print_step(f"Found token in localStorage: {key}", "success")
            
            # Search in sessionStorage
            for key, value in session_storage.items():
                if 'token' in key.lower() or 'auth' in key.lower():
                    self.tokens[f"sessionStorage_{key}"] = value
                    self.print_step(f"Found token in sessionStorage: {key}", "success")
            
            if not self.tokens:
                self.print_step("No explicit tokens found, saving all storage data", "warning")
                self.tokens = {
                    "localStorage": self.local_storage,
                    "sessionStorage": session_storage
                }
            
            return True
            
        except Exception as e:
            self.print_step(f"Token extraction failed: {str(e)[:80]}", "error")
            return False
    
    async def save_session(self):
        """Save tokens and cookies to file (only latest, no timestamped duplicates)"""
        self.print_step("Saving session data...", "progress")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = "v2fun_data"
        os.makedirs(output_dir, exist_ok=True)
        
        # Sanitize email for filename
        email_safe = self.email.replace("@", "_at_").replace(".", "_")
        
        session_data = {
            "timestamp": timestamp,
            "email": self.email,
            "account_number": self.account_number,
            "tokens": self.tokens,
            "cookies": self.cookies,
            "localStorage": self.local_storage
        }
        
        # Only save to latest file (overwrite previous, no duplicates)
        latest_file = os.path.join(output_dir, f"v2fun_session_{email_safe}_latest.json")
        with open(latest_file, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        self.print_step(f"Session saved: {latest_file}", "success")
    
    async def run(self, browser):
        """Main execution flow for one account"""
        self.print_header()
        
        # Create context
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        
        # Apply stealth
        await stealth.apply_stealth_async(page)
        
        try:
            # Navigate to V2Fun
            self.print_step("Navigating to V2Fun.ai...", "progress")
            await page.goto("https://v2fun.ai", wait_until="domcontentloaded")
            await asyncio.sleep(3)
            self.print_step("V2Fun.ai loaded", "success")
            
            # Click login button
            self.print_step("Looking for login button...", "progress")
            login_selectors = [
                'button:has-text("Login")',
                'button:has-text("Log in")',
                'a:has-text("Login")',
                '[href*="login"]'
            ]
            for selector in login_selectors:
                if await self.wait_and_click(page, selector, timeout=5000, description="Login button"):
                    break
            
            # Click "Continue with Google" button and wait for popup
            self.print_step("Looking for Google OAuth button...", "progress")
            google_selectors = [
                'button:has-text("Continue with Google")',
                'button:has-text("Google")',
                '[aria-label*="Google"]',
                'button[class*="google"]'
            ]
            
            # Find the button first
            button_selector = None
            for selector in google_selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        button_selector = selector
                        break
                except:
                    continue
            
            if not button_selector:
                self.print_step("Google OAuth button not found", "error")
                await context.close()
                return False
            
            # Click button and wait for popup simultaneously
            self.print_step("Clicking Google OAuth button...", "progress")
            async with context.expect_page(timeout=30000) as popup_info:
                await page.click(button_selector)
                self.print_step("Clicked: Continue with Google", "success")
            
            # Handle Google OAuth in popup
            if not await self.handle_google_login_popup(await popup_info.value, page):
                self.print_step("Login failed - skipping this account", "error")
                await context.close()
                return False
            
            # Handle survey popup
            await self.handle_survey(page)
            
            # Wait for dashboard to load
            self.print_step("Waiting for dashboard to load...", "progress")
            await asyncio.sleep(5)
            self.print_step("Dashboard loaded", "success")
            
            # Extract tokens
            if await self.extract_tokens(page, context):
                # Save session
                await self.save_session()
                self.success = True
                self.print_step("Account processing completed successfully!", "success")
            else:
                self.print_step("Failed to extract tokens", "error")
            
        except Exception as e:
            self.print_step(f"Error during automation: {str(e)[:100]}", "error")
            import traceback
            console.print(traceback.format_exc(), style="red dim")
        finally:
            await context.close()
        
        return self.success


def has_valid_token(email: str) -> bool:
    """Check if account already has a valid (non-expired) token"""
    email_safe = email.replace("@", "_at_").replace(".", "_")
    session_file = os.path.join("v2fun_data", f"v2fun_session_{email_safe}_latest.json")
    
    if not os.path.exists(session_file):
        return False
    
    try:
        with open(session_file, "r", encoding="utf-8") as f:
            session = json.load(f)
        
        token = session.get("tokens", {}).get("cookie_token", "")
        if not token:
            return False
        
        # Decode JWT to check expiry
        import base64
        parts = token.split(".")
        if len(parts) < 2:
            return False
        
        payload = parts[1] + "=" * (4 - len(parts[1]) % 4)
        decoded = base64.b64decode(payload)
        data = json.loads(decoded)
        
        exp = data.get("exp")
        if not exp:
            return False
        
        # Check if token is still valid (> 6 hours remaining)
        import time
        remaining = exp - time.time()
        if remaining > 21600:  # 6 hours
            return True
        
        return False
    except Exception:
        return False


def load_accounts(filepath: str = "account.txt"):
    """Load accounts from file"""
    accounts = []
    
    if not os.path.exists(filepath):
        console.print(f"[red][!] File not found: {filepath}[/red]")
        console.print("\n[yellow]Create account.txt with format:[/yellow]")
        console.print("[cyan]email1@gmail.com|password1[/cyan]")
        console.print("[cyan]email2@gmail.com:password2[/cyan]")
        return accounts
    
    with open(filepath, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            # Support both | and : as separator
            if "|" in line:
                separator = "|"
            elif ":" in line:
                separator = ":"
            else:
                console.print(f"[yellow][~] Line {line_num}: Invalid format, skipping[/yellow]")
                continue
            
            parts = line.split(separator)
            if len(parts) >= 2:
                email = parts[0].strip()
                password = parts[1].strip()
                accounts.append((email, password))
            else:
                console.print(f"[yellow][~] Line {line_num}: Invalid format, skipping[/yellow]")
    
    return accounts


async def main():
    """Entry point"""
    console.print(Panel.fit(
        "[bold cyan]V2Fun.ai Multi-Account Google Login Automation[/bold cyan]\n"
        "[dim]Automated login, survey completion, and token extraction[/dim]",
        border_style="cyan",
        box=box.DOUBLE
    ))
    
    # Load accounts
    console.print("\n[bold]Loading accounts from account.txt...[/bold]")
    accounts = load_accounts("account.txt")
    
    if not accounts:
        console.print("[red]No valid accounts found. Exiting.[/red]")
        return
    
    console.print(f"[green][+] Loaded {len(accounts)} account(s)[/green]\n")
    
    # Show account list
    table = Table(title="Accounts to Process", box=box.ROUNDED)
    table.add_column("No.", style="cyan", justify="center")
    table.add_column("Email", style="yellow")
    table.add_column("Password", style="dim")
    
    for idx, (email, password) in enumerate(accounts, 1):
        masked_password = password[:2] + "*" * (len(password) - 4) + password[-2:] if len(password) > 4 else "****"
        table.add_row(str(idx), email, masked_password)
    
    console.print(table)
    console.print()
    
    # Launch browser (shared for all accounts)
    async with async_playwright() as p:
        console.print("[bold]Launching browser...[/bold]")
        browser = await p.chromium.launch(
            headless=False,  # Show browser
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ]
        )
        
        results = []
        
        # Process each account
        for idx, (email, password) in enumerate(accounts, 1):
            # Skip if already has valid token
            if has_valid_token(email):
                console.print(f"\n[green][+] Account {idx}/{len(accounts)}: {email} already has valid token. Skipping.[/green]")
                results.append((email, True))
                continue
            
            login = V2FunGoogleLogin(email, password, idx, len(accounts))
            success = await login.run(browser)
            results.append((email, success))
            
            # Wait between accounts
            if idx < len(accounts):
                console.print(f"\n[dim]Waiting 5 seconds before next account...[/dim]\n")
                await asyncio.sleep(5)
        
        await browser.close()
        
        # Summary
        console.print("\n" + "="*80, style="cyan")
        console.print("[bold cyan]SUMMARY[/bold cyan]")
        console.print("="*80 + "\n", style="cyan")
        
        summary_table = Table(box=box.ROUNDED)
        summary_table.add_column("No.", style="cyan", justify="center")
        summary_table.add_column("Email", style="yellow")
        summary_table.add_column("Status", justify="center")
        
        success_count = 0
        for idx, (email, success) in enumerate(results, 1):
            status = "[green][+] Success[/green]" if success else "[red][!] Failed[/red]"
            summary_table.add_row(str(idx), email, status)
            if success:
                success_count += 1
        
        console.print(summary_table)
        console.print(f"\n[bold]Total: {success_count}/{len(accounts)} accounts successful[/bold]")
        console.print(f"[dim]Tokens saved in v2fun_data/ folder[/dim]\n")


if __name__ == "__main__":
    asyncio.run(main())
