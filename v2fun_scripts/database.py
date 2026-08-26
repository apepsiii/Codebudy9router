"""
V2Fun.ai Database Models
SQLite database for users and generations
"""

import sqlite3
import hashlib
import secrets
from datetime import datetime
from pathlib import Path

DB_PATH = Path("v2fun_data/v2fun.db")


def get_db():
    """Get database connection"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            google_email TEXT,
            v2fun_token TEXT,
            v2fun_user_id TEXT,
            credits INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Generations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS generations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            prompt TEXT NOT NULL,
            model TEXT DEFAULT 'nano-banana-pro',
            quality TEXT DEFAULT 'medium',
            ratio TEXT DEFAULT '16:9',
            num INTEGER DEFAULT 1,
            reference_image TEXT,
            task_uuid TEXT,
            work_area_id TEXT,
            task_ids TEXT,
            status TEXT DEFAULT 'pending',
            result_url TEXT,
            thumbnail_url TEXT,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    
    # Uploaded images table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS uploaded_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER,
            mime_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    
    # Sessions table (for login sessions)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_token TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    
    # V2Fun Accounts table (imported accounts to be processed)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS v2fun_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            user_id INTEGER,
            status TEXT DEFAULT 'pending',
            jwt_token TEXT,
            token_expiry TEXT,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_at TIMESTAMP NULL
        )
    """)
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")


def import_v2fun_account(email: str, password: str, user_id: int = None) -> bool:
    """Import a V2Fun account to database (without processing)"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO v2fun_accounts (email, password, user_id, status)
            VALUES (?, ?, ?, 'pending')
        """, (email, password, user_id))
        
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        # Account already exists, update to pending if was failed
        cursor.execute("""
            UPDATE v2fun_accounts 
            SET password = ?, status = 'pending', error_message = NULL
            WHERE email = ? AND status = 'failed'
        """, (password, email))
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Import error: {e}")
        conn.close()
        return False


def get_pending_accounts(user_id: int = None) -> list:
    """Get all pending V2Fun accounts"""
    conn = get_db()
    cursor = conn.cursor()
    
    if user_id:
        cursor.execute("""
            SELECT id, email, password, status, created_at
            FROM v2fun_accounts
            WHERE status = 'pending' AND (user_id = ? OR user_id IS NULL)
            ORDER BY created_at ASC
        """, (user_id,))
    else:
        cursor.execute("""
            SELECT id, email, password, status, created_at
            FROM v2fun_accounts
            WHERE status = 'pending'
            ORDER BY created_at ASC
        """)
    
    accounts = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return accounts


def get_all_v2fun_accounts(user_id: int = None) -> list:
    """Get all V2Fun accounts regardless of status"""
    conn = get_db()
    cursor = conn.cursor()
    
    if user_id:
        cursor.execute("""
            SELECT id, email, status, jwt_token, token_expiry, 
                   error_message, created_at, processed_at
            FROM v2fun_accounts
            WHERE user_id = ? OR user_id IS NULL
            ORDER BY created_at DESC
        """, (user_id,))
    else:
        cursor.execute("""
            SELECT id, email, status, jwt_token, token_expiry, 
                   error_message, created_at, processed_at
            FROM v2fun_accounts
            ORDER BY created_at DESC
        """)
    
    accounts = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return accounts


def update_v2fun_account_status(account_id: int, status: str, 
                                 jwt_token: str = None, token_expiry: str = None,
                                 error_message: str = None):
    """Update V2Fun account status after processing"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE v2fun_accounts
        SET status = ?, jwt_token = ?, token_expiry = ?, 
            error_message = ?, processed_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (status, jwt_token, token_expiry, error_message, account_id))
    
    conn.commit()
    conn.close()


def delete_v2fun_account(account_id: int):
    """Delete a V2Fun account"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM v2fun_accounts WHERE id = ?", (account_id,))
    
    conn.commit()
    conn.close()


def get_v2fun_account_by_id(account_id: int) -> dict:
    """Get V2Fun account by ID"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, email, password, status, jwt_token, token_expiry, created_at
        FROM v2fun_accounts
        WHERE id = ?
    """, (account_id,))
    
    account = cursor.fetchone()
    conn.close()
    
    if account:
        return dict(account)
    return None


def hash_password(password: str) -> str:
    """Hash password with SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(email: str, password: str, google_email: str = None) -> int:
    """Create a new user"""
    conn = get_db()
    cursor = conn.cursor()
    
    password_hash = hash_password(password)
    
    try:
        cursor.execute("""
            INSERT INTO users (email, password_hash, google_email)
            VALUES (?, ?, ?)
        """, (email, password_hash, google_email))
        
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        conn.close()
        return None


def verify_user(email: str, password: str) -> dict:
    """Verify user credentials"""
    conn = get_db()
    cursor = conn.cursor()
    
    password_hash = hash_password(password)
    
    cursor.execute("""
        SELECT id, email, google_email, v2fun_token, credits
        FROM users
        WHERE email = ? AND password_hash = ?
    """, (email, password_hash))
    
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return dict(user)
    return None


def get_user_by_id(user_id: int) -> dict:
    """Get user by ID"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, email, google_email, v2fun_token, v2fun_user_id, credits, created_at
        FROM users
        WHERE id = ?
    """, (user_id,))
    
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return dict(user)
    return None


def update_user_token(user_id: int, v2fun_token: str, v2fun_user_id: str = None):
    """Update user's V2Fun token"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE users
        SET v2fun_token = ?, v2fun_user_id = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (v2fun_token, v2fun_user_id, user_id))
    
    conn.commit()
    conn.close()


def create_generation(user_id: int, prompt: str, **kwargs) -> int:
    """Create a new generation record"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO generations (
            user_id, prompt, model, quality, ratio, num, 
            reference_image, task_uuid, work_area_id, task_ids, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        prompt,
        kwargs.get('model', 'nano-banana-pro'),
        kwargs.get('quality', 'medium'),
        kwargs.get('ratio', '16:9'),
        kwargs.get('num', 1),
        kwargs.get('reference_image'),
        kwargs.get('task_uuid'),
        kwargs.get('work_area_id'),
        kwargs.get('task_ids'),
        'pending'
    ))
    
    conn.commit()
    generation_id = cursor.lastrowid
    conn.close()
    return generation_id


def update_generation_status(generation_id: int, status: str, result_url: str = None, 
                             thumbnail_url: str = None, error_message: str = None):
    """Update generation status"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE generations
        SET status = ?, result_url = ?, thumbnail_url = ?, 
            error_message = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (status, result_url, thumbnail_url, error_message, generation_id))
    
    conn.commit()
    conn.close()


def get_user_generations(user_id: int, limit: int = 20) -> list:
    """Get user's generation history"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, prompt, model, quality, ratio, num, status, 
               result_url, thumbnail_url, task_uuid, created_at
        FROM generations
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (user_id, limit))
    
    generations = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return generations


def get_all_generations(limit: int = 50) -> list:
    """Get all generations (admin view)"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT g.id, g.prompt, g.status, g.created_at, u.email
        FROM generations g
        JOIN users u ON g.user_id = u.id
        ORDER BY g.created_at DESC
        LIMIT ?
    """, (limit,))
    
    generations = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return generations


def save_uploaded_image(user_id: int, filename: str, original_filename: str, 
                       file_path: str, file_size: int, mime_type: str) -> int:
    """Save uploaded image record"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO uploaded_images (
            user_id, filename, original_filename, file_path, file_size, mime_type
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, filename, original_filename, file_path, file_size, mime_type))
    
    conn.commit()
    image_id = cursor.lastrowid
    conn.close()
    return image_id


def create_session(user_id: int, expires_in_days: int = 7) -> str:
    """Create a login session"""
    from datetime import timedelta
    
    conn = get_db()
    cursor = conn.cursor()
    
    session_token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(days=expires_in_days)
    
    cursor.execute("""
        INSERT INTO sessions (user_id, session_token, expires_at)
        VALUES (?, ?, ?)
    """, (user_id, session_token, expires_at))
    
    conn.commit()
    conn.close()
    return session_token


def verify_session(session_token: str) -> dict:
    """Verify session token"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT s.user_id, u.email, u.v2fun_token, u.credits
        FROM sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.session_token = ? AND s.expires_at > CURRENT_TIMESTAMP
    """, (session_token,))
    
    session = cursor.fetchone()
    conn.close()
    
    if session:
        return dict(session)
    return None


def delete_session(session_token: str):
    """Delete a session (logout)"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM sessions WHERE session_token = ?", (session_token,))
    
    conn.commit()
    conn.close()


if __name__ == "__main__":
    # Initialize database
    init_db()
    print("Database schema created successfully!")
    
    # Create test user
    user_id = create_user("test@example.com", "password123")
    if user_id:
        print(f"Test user created with ID: {user_id}")
    else:
        print("User already exists")
