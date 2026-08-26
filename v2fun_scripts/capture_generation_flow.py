"""
V2Fun.ai Generation Flow Capture - Interactive Manual Mode
Restore session from saved tokens and capture all API calls during image generation

Usage:
    python v2fun_scripts/capture_generation_flow.py

This script will:
1. Load saved session tokens
2. Open browser with authenticated session
3. Show step-by-step instructions
4. Capture all network requests
5. Save generation API flow to JSON file
"""

import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright, Page, BrowserContext
from playwright_stealth import Stealth
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich import box

console = Console()
stealth = Stealth()

# Network capture storage
captured_requests = []
generation_requests = []


class V2FunFlowCapture:
    def __init__(self, session_file: str):
        self.session_file = session_file
        self.session_data = None
        self.email = None
        self.tokens = {}
        self.cookies = []
        
    def load_session(self):
        """Load session from JSON file"""
        console.print("\n[bold]Loading session data...[/bold]")
        
        if not os.path.exists(self.session_file):
            console.print(f"[red][!] Session file not found: {self.session_file}[/red]")
            return False
        
        with open(self.session_file, "r", encoding="utf-8") as f:
            self.session_data = json.load(f)
        
        self.email = self.session_data.get("email")
        self.tokens = self.session_data.get("tokens", {})
        self.cookies = self.session_data.get("cookies", [])
        
        console.print(f"[green][+] Loaded session for: {self.email}[/green]")
        console.print(f"[green][+] Tokens found: {len(self.tokens)}[/green]")
        console.print(f"[green][+] Cookies found: {len(self.cookies)}[/green]")
        
        return True
    
    async def setup_network_capture(self, page: Page):
        """Setup network request/response capture"""
        
        async def handle_request(request):
            """Capture outgoing requests"""
            url = request.url
            method = request.method
            
            # Only capture API calls to v2fun.ai
            if "v2fun.ai" in url or "api" in url.lower():
                request_data = {
                    "timestamp": datetime.now().isoformat(),
                    "type": "request",
                    "method": method,
                    "url": url,
                    "headers": dict(request.headers),
                    "post_data": request.post_data if method == "POST" else None
                }
                
                captured_requests.append(request_data)
                
                # Check if it's a generation request
                if any(keyword in url.lower() for keyword in ["generate", "create", "upload", "image", "model", "3d"]):
                    console.print(f"[yellow][>] API Call: {method} {url[:80]}...[/yellow]")
        
        async def handle_response(response):
            """Capture incoming responses"""
            url = response.url
            status = response.status
            
            # Only capture API responses
            if "v2fun.ai" in url or "api" in url.lower():
                try:
                    # Try to get response body
                    body = None
                    content_type = response.headers.get("content-type", "")
                    
                    if "application/json" in content_type:
                        try:
                            body = await response.json()
                        except:
                            body = await response.text()
                    elif "text" in content_type:
                        body = await response.text()
                    
                    response_data = {
                        "timestamp": datetime.now().isoformat(),
                        "type": "response",
                        "status": status,
                        "url": url,
                        "headers": dict(response.headers),
                        "body": body
                    }
                    
                    captured_requests.append(response_data)
                    
                    # Check if it's a generation response
                    if any(keyword in url.lower() for keyword in ["generate", "create", "upload", "image", "model", "3d"]):
                        generation_requests.append(response_data)
                        console.print(f"[green][+] API Response: {status} {url[:80]}...[/green]")
                        
                except Exception as e:
                    console.print(f"[red][!] Error capturing response: {str(e)[:50]}[/red]")
        
        # Attach event listeners
        page.on("request", handle_request)
        page.on("response", handle_response)
        
        console.print("[green][+] Network capture enabled[/green]")
    
    def show_instructions(self):
        """Show step-by-step instructions for user"""
        console.print("\n" + "="*80)
        console.print(Panel.fit(
            "[bold cyan]MANUAL GENERATION FLOW CAPTURE[/bold cyan]\n\n"
            "[yellow]Browser akan terbuka dengan session yang sudah login.[/yellow]\n"
            "[yellow]Ikuti instruksi berikut untuk capture API flow:[/yellow]",
            border_style="cyan",
            box=box.DOUBLE
        ))
        
        instructions = Table(title="Step-by-Step Instructions", box=box.ROUNDED, show_header=True, header_style="bold cyan")
        instructions.add_column("Step", style="cyan", justify="center", width=6)
        instructions.add_column("Action", style="yellow", width=60)
        instructions.add_column("What to Check", style="green", width=30)
        
        instructions.add_row(
            "1",
            "Klik tombol 'Generate' atau 'Create'",
            "Dashboard loaded"
        )
        instructions.add_row(
            "2",
            "Pilih 'Text to 3D' atau 'Image to 3D'",
            "Generation form muncul"
        )
        instructions.add_row(
            "3",
            "Masukkan prompt atau upload image\nContoh: 'a red sports car'",
            "Input field terisi"
        )
        instructions.add_row(
            "4",
            "Pilih quality/settings jika ada",
            "Settings applied"
        )
        instructions.add_row(
            "5",
            "Klik 'Generate' atau 'Submit'",
            "Generation started"
        )
        instructions.add_row(
            "6",
            "Tunggu hingga generation selesai\natau lihat progress bar",
            "Model generated/preview"
        )
        instructions.add_row(
            "7",
            "Klik 'Download' jika ada",
            "File download started"
        )
        instructions.add_row(
            "8",
            "Kembali ke terminal dan ketik 'done'",
            "Capture completed"
        )
        
        console.print(instructions)
        console.print("\n[bold]Browser akan tetap terbuka. Jangan ditutup![/bold]")
        console.print("[bold]Semua API calls akan tercapture secara otomatis.[/bold]\n")
    
    async def restore_session_and_capture(self):
        """Main flow: restore session and start capture"""
        
        async with async_playwright() as p:
            # Launch browser
            console.print("\n[bold]Launching browser...[/bold]")
            browser = await p.chromium.launch(
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox'
                ]
            )
            
            # Create context and restore cookies
            console.print("[bold]Creating browser context...[/bold]")
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            # Add cookies
            if self.cookies:
                await context.add_cookies(self.cookies)
                console.print(f"[green][+] Restored {len(self.cookies)} cookies[/green]")
            
            page = await context.new_page()
            
            # Apply stealth
            await stealth.apply_stealth_async(page)
            
            # Setup network capture
            await self.setup_network_capture(page)
            
            # Navigate to V2Fun dashboard
            console.print("\n[bold]Navigating to V2Fun.ai dashboard...[/bold]")
            await page.goto("https://v2fun.ai/create", wait_until="domcontentloaded")
            await asyncio.sleep(3)
            
            # Restore localStorage
            if self.session_data.get("localStorage"):
                for key, value in self.session_data["localStorage"].items():
                    try:
                        await page.evaluate(f"localStorage.setItem('{key}', {json.dumps(value)})")
                    except:
                        pass
                console.print("[green][+] Restored localStorage items[/green]")
            
            # Reload page to apply localStorage
            await page.reload(wait_until="domcontentloaded")
            await asyncio.sleep(3)
            
            console.print("[green][+] Session restored successfully![/green]")
            console.print(f"[green][+] Logged in as: {self.email}[/green]")
            
            # Show instructions
            self.show_instructions()
            
            # Wait for user to complete manual actions
            console.print("\n[bold yellow]Silakan lakukan generation flow di browser...[/bold yellow]")
            console.print("[dim]Browser akan tetap terbuka untuk capture[/dim]\n")
            
            # Interactive wait loop
            while True:
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: Prompt.ask(
                        "[bold]Ketik 'done' jika sudah selesai, atau 'status' untuk lihat capture[/bold]",
                        default="status"
                    )
                )
                
                if user_input.lower() == "done":
                    console.print("\n[green][+] Capture selesai![/green]")
                    break
                elif user_input.lower() == "status":
                    console.print(f"\n[cyan]Total requests captured: {len(captured_requests)}[/cyan]")
                    console.print(f"[cyan]Generation requests: {len(generation_requests)}[/cyan]")
                    
                    if generation_requests:
                        console.print("\n[bold]Recent generation requests:[/bold]")
                        for req in generation_requests[-5:]:
                            console.print(f"  - {req['url'][:80]}...")
                else:
                    console.print("[yellow]Unknown command. Use 'done' or 'status'[/yellow]")
            
            # Keep browser open for a bit
            console.print("\n[bold]Saving captured data...[/bold]")
            await asyncio.sleep(2)
            
            # Save captured data
            self.save_captured_data()
            
            # Keep browser open for inspection
            console.print("\n[bold yellow]Browser akan tetap terbuka 30 detik untuk inspeksi...[/bold yellow]")
            await asyncio.sleep(30)
            
            await browser.close()
    
    def save_captured_data(self):
        """Save captured requests to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = "v2fun_data"
        os.makedirs(output_dir, exist_ok=True)
        
        # Save all requests
        all_requests_file = os.path.join(output_dir, f"v2fun_capture_generation_{timestamp}.json")
        with open(all_requests_file, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": timestamp,
                "email": self.email,
                "total_requests": len(captured_requests),
                "requests": captured_requests
            }, f, indent=2, ensure_ascii=False)
        
        console.print(f"[green][+] All requests saved to: {all_requests_file}[/green]")
        
        # Save generation-specific requests
        if generation_requests:
            gen_requests_file = os.path.join(output_dir, f"v2fun_generation_api_{timestamp}.json")
            with open(gen_requests_file, "w", encoding="utf-8") as f:
                json.dump({
                    "timestamp": timestamp,
                    "email": self.email,
                    "generation_requests_count": len(generation_requests),
                    "requests": generation_requests
                }, f, indent=2, ensure_ascii=False)
            
            console.print(f"[green][+] Generation API saved to: {gen_requests_file}[/green]")
        
        # Print summary
        console.print("\n" + "="*80)
        console.print("[bold cyan]CAPTURE SUMMARY[/bold cyan]")
        console.print("="*80)
        console.print(f"Total requests captured: {len(captured_requests)}")
        console.print(f"Generation API calls: {len(generation_requests)}")
        
        if generation_requests:
            console.print("\n[bold]Generation endpoints found:[/bold]")
            unique_urls = set()
            for req in generation_requests:
                url = req.get("url", "")
                if url:
                    # Extract endpoint path
                    if "v2fun.ai" in url:
                        path = url.split("v2fun.ai")[1].split("?")[0]
                        unique_urls.add(path)
            
            for url in sorted(unique_urls):
                console.print(f"  [yellow]- {url}[/yellow]")
    
    async def run(self):
        """Main entry point"""
        console.print(Panel.fit(
            "[bold cyan]V2Fun.ai Generation Flow Capture[/bold cyan]\n"
            "[dim]Interactive manual mode with network capture[/dim]",
            border_style="cyan",
            box=box.DOUBLE
        ))
        
        # Load session
        if not self.load_session():
            return False
        
        # Start capture
        await self.restore_session_and_capture()
        
        return True


def list_available_sessions():
    """List all available session files"""
    console.print("\n[bold]Available sessions:[/bold]\n")
    
    session_files = []
    v2fun_data_dir = "v2fun_data"
    
    if os.path.exists(v2fun_data_dir):
        for file in os.listdir(v2fun_data_dir):
            if file.startswith("v2fun_session_") and file.endswith("_latest.json"):
                session_files.append(os.path.join(v2fun_data_dir, file))
    
    if not session_files:
        console.print("[red]No session files found in v2fun_data/[/red]")
        console.print("[yellow]Please run v2fun_google_login.py first[/yellow]")
        return None
    
    table = Table(box=box.ROUNDED)
    table.add_column("No.", style="cyan", justify="center")
    table.add_column("Email", style="yellow")
    table.add_column("File", style="green")
    
    for idx, file in enumerate(session_files, 1):
        # Extract email from filename
        filename = os.path.basename(file)
        email_part = filename.replace("v2fun_session_", "").replace("_latest.json", "")
        email = email_part.replace("_at_", "@").replace("_", ".")
        
        table.add_row(str(idx), email, filename)
    
    console.print(table)
    
    return session_files


async def main():
    """Entry point"""
    
    # List available sessions
    session_files = list_available_sessions()
    
    if not session_files:
        return
    
    # Prompt user to select session
    console.print()
    choice = Prompt.ask(
        "[bold]Pilih session (nomor)[/bold]",
        default="1"
    )
    
    try:
        choice_idx = int(choice) - 1
        if choice_idx < 0 or choice_idx >= len(session_files):
            console.print("[red]Invalid choice[/red]")
            return
        
        selected_session = session_files[choice_idx]
        console.print(f"\n[green][+] Selected: {os.path.basename(selected_session)}[/green]")
        
    except ValueError:
        console.print("[red]Invalid input[/red]")
        return
    
    # Start capture
    capture = V2FunFlowCapture(selected_session)
    await capture.run()


if __name__ == "__main__":
    asyncio.run(main())
