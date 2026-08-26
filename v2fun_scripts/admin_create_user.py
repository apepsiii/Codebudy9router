"""
Admin User Management CLI
Create users for V2Fun Web UI (invite-only system)

Usage:
    python v2fun_scripts/admin_create_user.py
    python v2fun_scripts/admin_create_user.py --email admin@example.com --password mypass
"""

import sys
import os
import getpass
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from v2fun_scripts.database import init_db, create_user, verify_user, get_user_by_id


def main():
    parser = argparse.ArgumentParser(description="Admin User Management - V2Fun Web UI")
    parser.add_argument("--email", "-e", help="User email")
    parser.add_argument("--password", "-p", help="User password")
    parser.add_argument("--list", "-l", action="store_true", help="List all users")
    args = parser.parse_args()

    init_db()

    if args.list:
        import sqlite3
        from v2fun_scripts.database import get_db
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, created_at FROM users ORDER BY id")
        users = cursor.fetchall()
        conn.close()
        
        if users:
            print(f"\n{'ID':<5} {'Email':<40} {'Created'}")
            print("-" * 70)
            for u in users:
                print(f"{u[0]:<5} {u[1]:<40} {u[2]}")
        else:
            print("No users found.")
        return

    email = args.email
    password = args.password

    if not email:
        email = input("Enter email: ").strip()
    
    if not password:
        password = getpass.getpass("Enter password: ").strip()
        confirm = getpass.getpass("Confirm password: ").strip()
        if password != confirm:
            print("Error: Passwords do not match")
            sys.exit(1)
    
    if len(password) < 6:
        print("Error: Password must be at least 6 characters")
        sys.exit(1)

    user_id = create_user(email, password)
    
    if user_id:
        print(f"\n[+] User created successfully!")
        print(f"    Email: {email}")
        print(f"    ID: {user_id}")
        print(f"\nUser can now login at the web UI.")
    else:
        print(f"\n[!] User already exists with email: {email}")
        sys.exit(1)


if __name__ == "__main__":
    main()
