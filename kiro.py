#!/usr/bin/env python
"""
Kiro CLI - Command-line interface for Kiro Token Generator
Usage: kiro [command] [options]
"""
import sys
import os
import subprocess
import argparse

# Add web directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web'))


def start_server(host="0.0.0.0", port=8000, reload=False):
    """Start the web dashboard server"""
    print("[*] Starting Kiro Web Dashboard...")
    print(f"[*] Server: http://{host}:{port}")
    print(f"[*] Local: http://localhost:{port}")
    print("\n[*] Press CTRL+C to stop\n")
    
    # Initialize database first
    from web.database import init_db
    init_db()
    
    # Start uvicorn server
    import uvicorn
    uvicorn.run(
        "web.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


def init_database():
    """Initialize the database"""
    print("[*] Initializing database...")
    from web.database import init_db
    init_db()
    print("[+] Database initialized successfully")


def show_version():
    """Show version information"""
    print("Kiro Token Generator v1.0.0")
    print("Web Dashboard Edition")


def show_help():
    """Show help message"""
    help_text = """
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║               KIRO TOKEN GENERATOR - CLI COMMANDS                    ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝

USAGE:
    kiro <command> [options]

COMMANDS:
    start               Start the web dashboard server
    init                Initialize the database
    version             Show version information
    help                Show this help message

OPTIONS:
    --host HOST         Server host (default: 0.0.0.0)
    --port PORT         Server port (default: 8000)
    --reload            Enable auto-reload (development mode)

EXAMPLES:
    kiro start                          # Start server on default port 8000
    kiro start --port 3000              # Start server on port 3000
    kiro start --reload                 # Start with auto-reload
    kiro init                           # Initialize database

WEB DASHBOARD:
    Once started, open your browser to:
    http://localhost:8000

    Features:
    ✓ Add accounts (single or bulk import)
    ✓ Monitor processing status
    ✓ View tokens and export
    ✓ Real-time statistics
    ✓ Manual inject workflow

DIRECTORY STRUCTURE:
    kiro.db             Database file (SQLite)
    kiro_tokens.txt     Exported tokens
    web/                Web dashboard files
    ├── app.py          FastAPI backend
    ├── database.py     Database models
    └── static/         Frontend files

SUPPORT:
    Documentation: README.md
    Issues: GitHub Issues
    
═══════════════════════════════════════════════════════════════════════
"""
    print(help_text)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Kiro Token Generator CLI",
        add_help=False
    )
    parser.add_argument("command", nargs="?", default="help", 
                       choices=["start", "init", "version", "help"],
                       help="Command to run")
    parser.add_argument("--host", default="0.0.0.0", help="Server host")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    if args.command == "start":
        start_server(host=args.host, port=args.port, reload=args.reload)
    elif args.command == "init":
        init_database()
    elif args.command == "version":
        show_version()
    elif args.command == "help":
        show_help()
    else:
        show_help()


if __name__ == "__main__":
    main()
