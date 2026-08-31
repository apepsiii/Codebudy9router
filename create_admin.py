"""
Create Admin Account for V2Fun Web UI
Usage: python create_admin.py <email> <password>
Example: python create_admin.py admin@example.com MyPassword123
"""

import sys
from v2fun_scripts.database import create_user, init_db

def main():
    # Initialize database first
    init_db()
    
    print("="*60)
    print("Create Admin Account - V2Fun Web UI")
    print("="*60)
    
    # Check arguments
    if len(sys.argv) < 3:
        print("\nUsage: python create_admin.py <email> <password>")
        print("Example: python create_admin.py admin@example.com MyPassword123")
        sys.exit(1)
    
    email = sys.argv[1].strip()
    password = sys.argv[2].strip()
    
    if not email or not password:
        print("❌ Email and password cannot be empty!")
        sys.exit(1)
    
    # Create user
    user_id = create_user(email, password)
    
    if user_id:
        print(f"\n[+] Admin account created successfully!")
        print(f"    Email: {email}")
        print(f"    User ID: {user_id}")
        print(f"\n[+] You can now login at: http://localhost:5000/login")
    else:
        print(f"\n[-] Failed to create account.")
        print(f"    Email '{email}' may already exist in database.")
        print(f"\n[!] Tip: Check existing users in v2fun_data/v2fun.db")

if __name__ == "__main__":
    main()
