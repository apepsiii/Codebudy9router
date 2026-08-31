"""
Manage Users for V2Fun Web UI
Usage: 
    python manage_users.py list
    python manage_users.py create <email> <password>
    python manage_users.py reset <email> <new_password>
"""

import sys
from v2fun_scripts.database import (
    get_db, create_user, init_db, hash_password
)

def list_users():
    """List all users"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, email, google_email, credits, created_at FROM users')
    rows = cursor.fetchall()
    conn.close()
    
    print("="*80)
    print("Existing Users in Database")
    print("="*80)
    if not rows:
        print("No users found.")
    else:
        print(f"{'ID':<5} {'Email':<35} {'Google Email':<25} {'Credits':<10} {'Created'}")
        print("-"*80)
        for row in rows:
            goog = row[2] or "-"
            print(f"{row[0]:<5} {row[1]:<35} {goog:<25} {row[3]:<10} {row[4]}")
    print()

def create_new_user(email, password):
    """Create new user"""
    user_id = create_user(email, password)
    if user_id:
        print(f"[+] User created successfully!")
        print(f"    Email: {email}")
        print(f"    User ID: {user_id}")
    else:
        print(f"[-] Failed to create user. Email '{email}' may already exist.")

def reset_password(email, new_password):
    """Reset user password"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    
    if not user:
        print(f"[-] User '{email}' not found.")
        conn.close()
        return
    
    # Update password
    new_hash = hash_password(new_password)
    cursor.execute('UPDATE users SET password_hash = ? WHERE email = ?', (new_hash, email))
    conn.commit()
    conn.close()
    
    print(f"[+] Password reset successfully for '{email}'")

def main():
    init_db()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python manage_users.py list")
        print("  python manage_users.py create <email> <password>")
        print("  python manage_users.py reset <email> <new_password>")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_users()
    elif command == "create":
        if len(sys.argv) < 4:
            print("Usage: python manage_users.py create <email> <password>")
            sys.exit(1)
        create_new_user(sys.argv[2], sys.argv[3])
    elif command == "reset":
        if len(sys.argv) < 4:
            print("Usage: python manage_users.py reset <email> <new_password>")
            sys.exit(1)
        reset_password(sys.argv[2], sys.argv[3])
    else:
        print(f"Unknown command: {command}")
        print("Available commands: list, create, reset")

if __name__ == "__main__":
    main()
