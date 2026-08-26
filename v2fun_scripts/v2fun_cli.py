"""
V2Fun.ai CLI Tool - Generate Images from Terminal
Command-line interface for V2Fun.ai image generation

Usage:
    python v2fun_scripts/v2fun_cli.py generate --prompt "a red sports car"
    python v2fun_scripts/v2fun_cli.py generate --prompt "cat" --quality high --ratio 1:1
    python v2fun_scripts/v2fun_cli.py generate --prompt "dog" --image path/to/ref.jpg
"""

import asyncio
import json
import os
import sys
import argparse
import requests
import time
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()


class V2FunClient:
    def __init__(self, token: str):
        self.base_url = "https://api.prod.v2fun.ai"
        self.token = token
        self.headers = {
            "Authorization": token,
            "X-Access-Token": token,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Referer": "https://v2fun.ai/"
        }
    
    def generate_image(self, prompt: str, **kwargs):
        """Generate image with V2Fun API"""
        console.print(f"\n[bold]Submitting generation request...[/bold]")
        
        payload = {
            "prompt": prompt,
            "model": kwargs.get("model", "nano-banana-pro"),
            "ratio": kwargs.get("ratio", "16:9"),
            "num": kwargs.get("num", 1),
            "quality": kwargs.get("quality", "medium")
        }
        
        if kwargs.get("reference_images"):
            payload["referenceImages"] = kwargs["reference_images"]
        
        console.print(f"[cyan]Prompt:[/cyan] {prompt[:100]}...")
        console.print(f"[cyan]Model:[/cyan] {payload['model']}")
        console.print(f"[cyan]Quality:[/cyan] {payload['quality']}")
        console.print(f"[cyan]Ratio:[/cyan] {payload['ratio']}")
        
        try:
            response = requests.post(
                f"{self.base_url}/work/external/generate/image-generate?lan=en",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get("success"):
                console.print("[green][+] Generation request submitted successfully![/green]")
                return result.get("result")
            else:
                console.print(f"[red][!] API Error: {result.get('message')}[/red]")
                return None
                
        except requests.exceptions.RequestException as e:
            console.print(f"[red][!] Request failed: {str(e)}[/red]")
            return None
    
    def get_balance(self):
        """Get user credit balance"""
        try:
            response = requests.get(
                f"{self.base_url}/sys/user/get-balance?lan=en",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except:
            return None
    
    def get_user_info(self):
        """Get user login info"""
        try:
            response = requests.post(
                f"{self.base_url}/sys/user/getLoginInfo?lan=en",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except:
            return None


def load_token_from_session(email: str = None):
    """Load token from saved session file"""
    v2fun_data = Path("v2fun_data")
    
    # Find session files
    if email:
        # Specific email
        email_safe = email.replace("@", "_at_").replace(".", "_")
        session_file = v2fun_data / f"v2fun_session_{email_safe}_latest.json"
        if not session_file.exists():
            console.print(f"[red][!] Session not found for {email}[/red]")
            return None
    else:
        # Find any latest session
        session_files = list(v2fun_data.glob("v2fun_session_*_latest.json"))
        if not session_files:
            console.print("[red][!] No session files found[/red]")
            console.print("[yellow]Run v2fun_google_login.py first to get tokens[/yellow]")
            return None
        session_file = session_files[0]
    
    # Load session
    with open(session_file, "r", encoding="utf-8") as f:
        session = json.load(f)
    
    # Extract token
    tokens = session.get("tokens", {})
    token = tokens.get("cookie_token") or tokens.get("localStorage_access_token")
    
    if not token:
        console.print("[red][!] No token found in session[/red]")
        return None
    
    console.print(f"[green][+] Loaded session for: {session.get('email')}[/green]")
    return token


def upload_reference_image(client: V2FunClient, image_path: str):
    """Upload reference image to OSS"""
    console.print(f"\n[bold]Uploading reference image...[/bold]")
    console.print(f"[cyan]File:[/cyan] {image_path}")
    
    # TODO: Implement OSS upload
    # For now, return None (will skip reference image)
    console.print("[yellow][~] Image upload not yet implemented[/yellow]")
    console.print("[yellow][~] Generating without reference image[/yellow]")
    return None


def display_result(result: dict):
    """Display generation result"""
    console.print("\n" + "="*80)
    console.print("[bold green]GENERATION RESULT[/bold green]")
    console.print("="*80)
    
    task_uuid = result.get("taskuuid")
    task_ids = result.get("taskIds", [])
    work_area_id = result.get("id")
    
    table = Table(box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="yellow")
    
    table.add_row("Task UUID", str(task_uuid))
    table.add_row("Work Area ID", str(work_area_id))
    table.add_row("Task IDs", ", ".join(map(str, task_ids)))
    table.add_row("Status", "In Progress (I)")
    table.add_row("Create Time", result.get("createTime", "N/A"))
    
    console.print(table)
    
    # Get work details
    child = result.get("child", [])
    if child:
        work_item = child[0]
        console.print(f"\n[bold]Work Item Details:[/bold]")
        console.print(f"  Model: {work_item.get('model')}")
        console.print(f"  Quality: {work_item.get('quality')}")
        console.print(f"  Ratio: {work_item.get('ratio')}")
        console.print(f"  Type: {work_item.get('generateType')}")
        console.print(f"  Progress: {work_item.get('progress')}%")
    
    console.print("\n[yellow][~] Note: Real-time monitoring via SSE not yet implemented[/yellow]")
    console.print("[yellow][~] Check V2Fun.ai dashboard for generation status[/yellow]")
    
    # Save result
    output_dir = Path("v2fun_data/generations")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = output_dir / f"generation_{task_uuid}_{timestamp}.json"
    
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    console.print(f"\n[green][+] Result saved to: {result_file}[/green]")


def cmd_generate(args):
    """Generate command"""
    console.print(Panel.fit(
        "[bold cyan]V2Fun.ai Image Generation[/bold cyan]\n"
        "[dim]Generate images from command line[/dim]",
        border_style="cyan",
        box=box.DOUBLE
    ))
    
    # Load token
    token = load_token_from_session(args.email)
    if not token:
        return 1
    
    # Create client
    client = V2FunClient(token)
    
    # Get user info
    if args.show_info:
        user_info = client.get_user_info()
        balance = client.get_balance()
        
        if user_info and user_info.get("success"):
            result = user_info.get("result", {})
            console.print(f"\n[bold]User Info:[/bold]")
            console.print(f"  Username: {result.get('username')}")
            console.print(f"  User ID: {result.get('id')}")
        
        if balance and balance.get("success"):
            result = balance.get("result", {})
            console.print(f"\n[bold]Balance:[/bold]")
            console.print(f"  Credits: {result.get('balance', 0)}")
        
        console.print()
    
    # Upload reference image if provided
    reference_images = None
    if args.image:
        uploaded_path = upload_reference_image(client, args.image)
        if uploaded_path:
            reference_images = [uploaded_path]
    
    # Generate
    result = client.generate_image(
        prompt=args.prompt,
        model=args.model,
        quality=args.quality,
        ratio=args.ratio,
        num=args.num,
        reference_images=reference_images
    )
    
    if result:
        display_result(result)
        return 0
    else:
        console.print("[red][!] Generation failed[/red]")
        return 1


def cmd_list_sessions(args):
    """List available sessions"""
    v2fun_data = Path("v2fun_data")
    session_files = list(v2fun_data.glob("v2fun_session_*_latest.json"))
    
    if not session_files:
        console.print("[yellow]No sessions found[/yellow]")
        return 1
    
    console.print(f"\n[bold]Available Sessions:[/bold]\n")
    
    table = Table(box=box.ROUNDED)
    table.add_column("No.", style="cyan", justify="center")
    table.add_column("Email", style="yellow")
    table.add_column("User ID", style="green")
    table.add_column("Timestamp", style="dim")
    
    for idx, file in enumerate(session_files, 1):
        with open(file, "r", encoding="utf-8") as f:
            session = json.load(f)
        
        email = session.get("email")
        timestamp = session.get("timestamp")
        
        # Try to extract user ID from token
        tokens = session.get("tokens", {})
        token = tokens.get("cookie_token", "")
        user_id = "N/A"
        
        table.add_row(str(idx), email, user_id, timestamp)
    
    console.print(table)
    console.print()
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="V2Fun.ai CLI Tool - Generate images from terminal",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate with text prompt
  python v2fun_cli.py generate --prompt "a red sports car"
  
  # Generate with quality and ratio
  python v2fun_cli.py generate --prompt "cat" --quality high --ratio 1:1
  
  # Generate with reference image
  python v2fun_cli.py generate --prompt "dog" --image ref.jpg
  
  # List available sessions
  python v2fun_cli.py list-sessions
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate images")
    gen_parser.add_argument("--prompt", "-p", required=True, help="Text prompt for generation")
    gen_parser.add_argument("--model", "-m", default="nano-banana-pro", help="Model to use (default: nano-banana-pro)")
    gen_parser.add_argument("--quality", "-q", choices=["low", "medium", "high"], default="medium", help="Quality level")
    gen_parser.add_argument("--ratio", "-r", choices=["1:1", "16:9", "9:16"], default="16:9", help="Aspect ratio")
    gen_parser.add_argument("--num", "-n", type=int, default=1, help="Number of images")
    gen_parser.add_argument("--image", "-i", help="Reference image path")
    gen_parser.add_argument("--email", "-e", help="Email of session to use")
    gen_parser.add_argument("--show-info", action="store_true", help="Show user info and balance")
    gen_parser.set_defaults(func=cmd_generate)
    
    # List sessions command
    list_parser = subparsers.add_parser("list-sessions", help="List available sessions")
    list_parser.set_defaults(func=cmd_list_sessions)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
