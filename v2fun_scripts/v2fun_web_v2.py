"""
V2Fun.ai Web UI V2 - Enhanced Flask Backend
Features: User auth, image upload, database integration, generation history

Usage:
    python v2fun_scripts/v2fun_web_v2.py
    Open: http://localhost:5000
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory, Response
import json
import os
import sys
import requests
import threading
from pathlib import Path
from datetime import datetime
from werkzeug.utils import secure_filename
import secrets

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from v2fun_scripts.database import (
    init_db, create_user, verify_user, get_user_by_id,
    update_user_token, create_generation, update_generation_status,
    get_user_generations, save_uploaded_image,
    create_session as create_db_session, verify_session as verify_db_session,
    delete_session,
    import_v2fun_account, get_pending_accounts, get_all_v2fun_accounts,
    update_v2fun_account_status, delete_v2fun_account, get_v2fun_account_by_id
)
from v2fun_scripts.sse_monitor import SSEMonitor
from v2fun_scripts.token_manager import (
    get_token_status, get_time_remaining, is_token_valid,
    check_and_refresh_if_needed, get_all_tokens_status
)

# Active monitors: {user_id: SSEMonitor}
active_monitors: dict = {}
# Pending events queue: {generation_id: [events]}
pending_events: dict = {}

app = Flask(__name__, 
            template_folder='../v2fun_web_v2/templates',
            static_folder='../v2fun_web_v2/static')
app.secret_key = secrets.token_hex(32)
app.config['UPLOAD_FOLDER'] = Path('v2fun_data/uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Ensure upload folder exists
app.config['UPLOAD_FOLDER'].mkdir(parents=True, exist_ok=True)


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def get_current_user():
    """Get current logged in user from session"""
    session_token = session.get('session_token')
    if not session_token:
        return None
    
    user_data = verify_db_session(session_token)
    if not user_data:
        session.pop('session_token', None)
        return None
    
    return user_data


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
        payload = {
            "prompt": prompt,
            "model": kwargs.get("model", "nano-banana-pro"),
            "ratio": kwargs.get("ratio", "16:9"),
            "num": kwargs.get("num", 1),
            "quality": kwargs.get("quality", "medium")
        }
        
        if kwargs.get("reference_images"):
            payload["referenceImages"] = kwargs["reference_images"]
        
        try:
            response = requests.post(
                f"{self.base_url}/work/external/generate/image-generate?lan=en",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()
                
        except requests.exceptions.RequestException as e:
            return {"success": False, "message": str(e)}
    
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
        except Exception as e:
            return {"success": False, "message": str(e)}
    
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
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def get_upload_credentials(self):
        """Get Alibaba Cloud OSS STS credentials from V2Fun"""
        try:
            response = requests.post(
                f"{self.base_url}/sys/oss/nologin/getAliSTS?lan=en",
                headers={**self.headers, "Content-Type": "application/json"},
                json={},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def upload_to_oss(self, file_path: str, mime_type: str = "image/jpeg"):
        """Upload file to Alibaba Cloud OSS using STS credentials from V2Fun"""
        # Step 1: Get STS credentials
        sts_resp = self.get_upload_credentials()
        if not sts_resp.get("success"):
            return {"success": False, "message": "Failed to get upload credentials"}
        
        sts = sts_resp.get("result", {})
        oss_host = sts.get("ossHost")  # e.g. https://external-v2fun-data-hk-1.oss-accelerate.aliyuncs.com
        oss_path = sts.get("path")     # e.g. upload/image/2026/08/26/20260826150013a15830.jpg
        
        # Step 2: Upload to OSS using POST form
        with open(file_path, "rb") as f:
            files = {
                "file": (os.path.basename(file_path), f, mime_type)
            }
            form_data = {
                "OSSAccessKeyId": sts.get("accessKeyId"),
                "policy": sts.get("policy"),
                "Signature": sts.get("signature"),
                "key": oss_path,
                "x-oss-security-token": sts.get("securityToken"),
                "success_action_status": "200"
            }
            
            upload_resp = requests.post(
                oss_host,
                data=form_data,
                files=files,
                timeout=30
            )
            
            if upload_resp.status_code == 200:
                return {"success": True, "oss_path": oss_path}
            else:
                return {"success": False, "message": f"OSS upload failed: {upload_resp.status_code} - {upload_resp.text[:200]}"}
        
        return {"success": False, "message": "Upload failed"}


@app.route('/')
def index():
    """Main page - redirect to login if not authenticated"""
    user = get_current_user()
    if not user:
        return redirect(url_for('login_page'))
    return render_template('dashboard.html', user=user)


@app.route('/login')
def login_page():
    """Login page"""
    return render_template('login.html')


@app.route('/register')
def register_page():
    """Registration page"""
    return render_template('register.html')


@app.route('/api/register', methods=['POST'])
def api_register():
    """Register new user"""
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"success": False, "message": "Email and password required"})
    
    if len(password) < 6:
        return jsonify({"success": False, "message": "Password must be at least 6 characters"})
    
    user_id = create_user(email, password)
    
    if user_id:
        return jsonify({"success": True, "message": "Registration successful! Please login."})
    else:
        return jsonify({"success": False, "message": "Email already exists"})


@app.route('/api/login', methods=['POST'])
def api_login():
    """Login user"""
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"success": False, "message": "Email and password required"})
    
    user = verify_user(email, password)
    
    if user:
        # Create session
        session_token = create_db_session(user['id'])
        session['session_token'] = session_token
        
        return jsonify({
            "success": True,
            "message": "Login successful!",
            "user": {
                "email": user['email'],
                "credits": user['credits']
            }
        })
    else:
        return jsonify({"success": False, "message": "Invalid email or password"})


@app.route('/api/logout', methods=['POST'])
def api_logout():
    """Logout user"""
    session_token = session.get('session_token')
    if session_token:
        delete_session(session_token)
        session.pop('session_token', None)
    
    return jsonify({"success": True, "message": "Logged out successfully"})


@app.route('/api/me')
def api_me():
    """Get current user info with live credits from V2Fun"""
    user = get_current_user()
    
    if not user:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    credits = user['credits']
    
    # Fetch live credits from V2Fun if token exists
    if user.get('v2fun_token'):
        client = V2FunClient(user['v2fun_token'])
        balance_resp = client.get_balance()
        if balance_resp.get("success"):
            result = balance_resp.get("result", {})
            # Try various possible field names
            if isinstance(result, dict):
                credits = result.get('balance') or result.get('credits') or result.get('points') or credits
    
    return jsonify({
        "success": True,
        "user": {
            "email": user['email'],
            "credits": credits,
            "has_v2fun_token": bool(user.get('v2fun_token'))
        }
    })


@app.route('/api/connect-v2fun', methods=['POST'])
def api_connect_v2fun():
    """Connect V2Fun token to user account"""
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    data = request.json
    v2fun_email = data.get('v2fun_email')
    
    if not v2fun_email:
        return jsonify({"success": False, "message": "V2Fun email required"})
    
    # Load token from saved session
    v2fun_data_dir = Path("v2fun_data")
    email_safe = v2fun_email.replace("@", "_at_").replace(".", "_")
    session_file = v2fun_data_dir / f"v2fun_session_{email_safe}_latest.json"
    
    if not session_file.exists():
        return jsonify({"success": False, "message": "V2Fun session not found. Please login first."})
    
    with open(session_file, "r", encoding="utf-8") as f:
        v2fun_session = json.load(f)
    
    tokens = v2fun_session.get("tokens", {})
    token = tokens.get("cookie_token") or tokens.get("localStorage_access_token")
    
    if not token:
        return jsonify({"success": False, "message": "No token found in session"})
    
    # Update user
    update_user_token(user['user_id'], token)
    
    return jsonify({"success": True, "message": "V2Fun account connected successfully!"})


@app.route('/api/upload-image', methods=['POST'])
def api_upload_image():
    """Upload reference image to V2Fun OSS"""
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    if not user.get('v2fun_token'):
        return jsonify({"success": False, "message": "Please connect V2Fun account first"})
    
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "No file uploaded"})
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"success": False, "message": "No file selected"})
    
    if not allowed_file(file.filename):
        return jsonify({"success": False, "message": "File type not allowed"})
    
    # Save locally first
    original_filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{original_filename}"
    file_path = app.config['UPLOAD_FOLDER'] / filename
    
    file.save(str(file_path))
    file_size = os.path.getsize(file_path)
    
    # Save to local database
    image_id = save_uploaded_image(
        user['user_id'],
        filename,
        original_filename,
        str(file_path),
        file_size,
        file.content_type
    )
    
    # Upload to V2Fun OSS
    client = V2FunClient(user['v2fun_token'])
    mime = file.content_type or "image/jpeg"
    oss_result = client.upload_to_oss(str(file_path), mime)
    
    if oss_result.get("success"):
        return jsonify({
            "success": True,
            "message": "Image uploaded to V2Fun OSS successfully!",
            "image": {
                "id": image_id,
                "filename": filename,
                "url": f"/uploads/{filename}",
                "oss_path": oss_result["oss_path"]  # This is what V2Fun API needs
            }
        })
    else:
        return jsonify({
            "success": False,
            "message": f"OSS upload failed: {oss_result.get('message', 'Unknown error')}"
        })


@app.route('/api/generate', methods=['POST'])
def api_generate():
    """Generate image"""
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    if not user.get('v2fun_token'):
        return jsonify({"success": False, "message": "Please connect your V2Fun account first"})
    
    data = request.json
    prompt = data.get('prompt')
    
    if not prompt:
        return jsonify({"success": False, "message": "Prompt is required"})
    
    client = V2FunClient(user['v2fun_token'])
    
    result = client.generate_image(
        prompt=prompt,
        model=data.get("model", "nano-banana-pro"),
        quality=data.get("quality", "medium"),
        ratio=data.get("ratio", "16:9"),
        num=data.get("num", 1),
        reference_images=data.get("reference_images")
    )
    
    if result.get("success"):
        # Save to database
        result_data = result.get("result", {})
        task_uuid = result_data.get("taskuuid")
        generation_id = create_generation(
            user['user_id'],
            prompt,
            model=data.get("model"),
            quality=data.get("quality"),
            ratio=data.get("ratio"),
            num=data.get("num"),
            task_uuid=task_uuid,
            work_area_id=result_data.get("id"),
            task_ids=json.dumps(result_data.get("taskIds", []))
        )
        
        result["generation_id"] = generation_id
        
        # Start SSE monitor in background
        if task_uuid:
            start_monitor(user['user_id'], user['v2fun_token'], generation_id, task_uuid)
    
    return jsonify(result)


@app.route('/api/generations')
def api_generations():
    """Get user's generation history"""
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    generations = get_user_generations(user['user_id'], limit=20)
    
    return jsonify({
        "success": True,
        "generations": generations
    })


@app.route('/api/sessions')
def api_sessions():
    """Get available V2Fun sessions"""
    v2fun_data = Path("v2fun_data")
    session_files = list(v2fun_data.glob("v2fun_session_*_latest.json"))
    
    sessions = []
    for file in session_files:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
        tokens = data.get("tokens", {})
        token = tokens.get("cookie_token") or tokens.get("localStorage_access_token")
        if token:
            sessions.append({
                "email": data.get("email"),
                "timestamp": data.get("timestamp")
            })
    
    return jsonify({"success": True, "sessions": sessions})


@app.route('/api/import-accounts', methods=['POST'])
def api_import_accounts():
    """Import V2Fun accounts to database without processing"""
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    data = request.json
    accounts_text = data.get('accounts', '')
    
    accounts = []
    for line in accounts_text.strip().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '|' in line:
            parts = line.split('|', 1)
        elif ':' in line:
            parts = line.split(':', 1)
        else:
            continue
        accounts.append((parts[0].strip(), parts[1].strip()))
    
    if not accounts:
        return jsonify({"success": False, "message": "No valid accounts found"})
    
    imported = 0
    duplicates = 0
    for email, password in accounts:
        if import_v2fun_account(email, password, user.get('user_id')):
            imported += 1
        else:
            duplicates += 1
    
    return jsonify({
        "success": True,
        "message": f"Imported {imported} accounts ({duplicates} duplicates skipped)",
        "imported": imported,
        "duplicates": duplicates,
        "total": len(accounts)
    })


@app.route('/api/v2fun-accounts')
def api_v2fun_accounts():
    """Get all imported V2Fun accounts with status"""
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    accounts = get_all_v2fun_accounts(user.get('user_id'))
    
    # Mask JWT tokens for security (show only first 30 chars)
    for acc in accounts:
        if acc.get('jwt_token'):
            acc['jwt_token'] = acc['jwt_token'][:30] + '...'
    
    return jsonify({"success": True, "accounts": accounts})


@app.route('/api/process-account', methods=['POST'])
def api_process_account():
    """Process a single V2Fun account (login + get JWT)"""
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    data = request.json
    account_id = data.get('account_id')
    
    if not account_id:
        return jsonify({"success": False, "message": "Account ID required"})
    
    account = get_v2fun_account_by_id(account_id)
    if not account:
        return jsonify({"success": False, "message": "Account not found"})
    
    # Check if account already has valid token (skip re-login)
    from v2fun_scripts.token_manager import is_token_valid, get_token_expiry
    email_safe = account['email'].replace("@", "_at_").replace(".", "_")
    session_file = Path("v2fun_data") / f"v2fun_session_{email_safe}_latest.json"
    
    if session_file.exists():
        with open(session_file, "r", encoding="utf-8") as f:
            session_data = json.load(f)
        
        existing_token = session_data.get("tokens", {}).get("cookie_token", "")
        
        if existing_token and is_token_valid(existing_token):
            # Token still valid - skip re-login!
            expiry = get_token_expiry(existing_token)
            update_v2fun_account_status(
                account_id, 'done',
                jwt_token=existing_token,
                token_expiry=expiry.isoformat() if expiry else None
            )
            
            return jsonify({
                "success": True,
                "message": f"Account {account['email']} already has valid token. Skipped re-login.",
                "status": "done",
                "jwt_token": existing_token[:50] + "...",
                "token_expiry": expiry.isoformat() if expiry else None,
                "skipped": True
            })
    
    # No valid token - proceed with login
    update_v2fun_account_status(account_id, 'processing')
    
    # Write temp account file
    temp_account_file = Path("v2fun_data/temp_account.txt")
    temp_account_file.write_text(f"{account['email']}:{account['password']}", encoding="utf-8")
    
    try:
        import subprocess
        result = subprocess.run(
            ["python", "v2fun_scripts/v2fun_google_login.py"],
            capture_output=True, text=True, timeout=180
        )
        
        # Check if token was saved
        if session_file.exists():
            with open(session_file, "r", encoding="utf-8") as f:
                session_data = json.load(f)
            
            token = session_data.get("tokens", {}).get("cookie_token", "")
            
            # Get token expiry
            expiry = get_token_expiry(token)
            
            update_v2fun_account_status(
                account_id, 'done',
                jwt_token=token,
                token_expiry=expiry.isoformat() if expiry else None
            )
            
            return jsonify({
                "success": True,
                "message": f"Account {account['email']} processed successfully!",
                "status": "done",
                "jwt_token": token[:50] + "...",
                "token_expiry": expiry.isoformat() if expiry else None
            })
        else:
            update_v2fun_account_status(account_id, 'failed', error_message="Login automation failed")
            return jsonify({
                "success": False,
                "message": f"Processing failed for {account['email']}",
                "status": "failed"
            })
    
    except subprocess.TimeoutExpired:
        update_v2fun_account_status(account_id, 'failed', error_message="Timeout")
        return jsonify({"success": False, "message": "Automation timed out"})
    except Exception as e:
        update_v2fun_account_status(account_id, 'failed', error_message=str(e))
        return jsonify({"success": False, "message": f"Error: {str(e)}"})
    finally:
        if temp_account_file.exists():
            temp_account_file.unlink()


@app.route('/api/process-all-accounts', methods=['POST'])
def api_process_all_accounts():
    """Process all pending V2Fun accounts sequentially"""
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    pending = get_pending_accounts(user.get('user_id'))
    
    if not pending:
        return jsonify({"success": False, "message": "No pending accounts to process"})
    
    # Return list of pending accounts for frontend to process one by one
    return jsonify({
        "success": True,
        "message": f"Found {len(pending)} pending accounts",
        "pending_ids": [acc['id'] for acc in pending]
    })


@app.route('/api/delete-v2fun-account', methods=['POST'])
def api_delete_v2fun_account():
    """Delete a V2Fun account from database"""
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    data = request.json
    account_id = data.get('account_id')
    
    if not account_id:
        return jsonify({"success": False, "message": "Account ID required"})
    
    delete_v2fun_account(account_id)
    
    return jsonify({"success": True, "message": "Account deleted"})


@app.route('/api/manage-accounts')
def api_manage_accounts():
    """List all V2Fun sessions for management"""
    v2fun_data = Path("v2fun_data")
    session_files = list(v2fun_data.glob("v2fun_session_*_latest.json"))
    
    accounts = []
    for file in session_files:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
        tokens = data.get("tokens", {})
        token = tokens.get("cookie_token") or tokens.get("localStorage_access_token")
        accounts.append({
            "email": data.get("email"),
            "timestamp": data.get("timestamp"),
            "has_token": bool(token),
            "filename": file.name
        })
    
    return jsonify({"success": True, "accounts": accounts})


@app.route('/api/delete-account', methods=['POST'])
def api_delete_account():
    """Delete a V2Fun session file"""
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    data = request.json
    email = data.get('email')
    
    if not email:
        return jsonify({"success": False, "message": "Email required"})
    
    v2fun_data = Path("v2fun_data")
    email_safe = email.replace("@", "_at_").replace(".", "_")
    
    # Delete all session files for this email
    deleted = False
    for pattern in [f"v2fun_session_{email_safe}_latest.json", f"v2fun_tokens_{email_safe}_*.json"]:
        for f in v2fun_data.glob(pattern):
            f.unlink()
            deleted = True
    
    if deleted:
        return jsonify({"success": True, "message": f"Account {email} deleted successfully"})
    else:
        return jsonify({"success": False, "message": "Account not found"})


@app.route('/api/retry-account', methods=['POST'])
def api_retry_account():
    """Retry login for a specific V2Fun account"""
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    data = request.json
    email = data.get('email')
    
    if not email:
        return jsonify({"success": False, "message": "Email required"})
    
    # Read password from account.txt if exists
    password = None
    account_file = Path("account.txt")
    if account_file.exists():
        with open(account_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith('#') or not line:
                    continue
                if '|' in line:
                    parts = line.split('|', 1)
                elif ':' in line:
                    parts = line.split(':', 1)
                else:
                    continue
                if parts[0].strip() == email:
                    password = parts[1].strip()
                    break
    
    if not password:
        return jsonify({"success": False, "message": "Password not found in account.txt for this email"})
    
    # Write temp account file
    temp_account_file = Path("v2fun_data/temp_account.txt")
    temp_account_file.write_text(f"{email}:{password}", encoding="utf-8")
    
    try:
        import subprocess
        result = subprocess.run(
            ["python", "v2fun_scripts/v2fun_google_login.py"],
            capture_output=True, text=True, timeout=180
        )
        
        email_safe = email.replace("@", "_at_").replace(".", "_")
        session_file = Path("v2fun_data") / f"v2fun_session_{email_safe}_latest.json"
        
        if session_file.exists():
            return jsonify({"success": True, "message": f"Retry successful for {email}"})
        else:
            return jsonify({"success": False, "message": "Retry failed. Check credentials."})
    except subprocess.TimeoutExpired:
        return jsonify({"success": False, "message": "Automation timed out"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"})
    finally:
        if temp_account_file.exists():
            temp_account_file.unlink()


@app.route('/api/token-status')
def api_token_status():
    """Get token status for all accounts"""
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    statuses = get_all_tokens_status()
    return jsonify({"success": True, "tokens": statuses})


@app.route('/api/refresh-token', methods=['POST'])
def api_refresh_token():
    """Manually trigger token refresh for an account"""
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "message": "Not authenticated"}), 401
    
    data = request.json
    email = data.get('email')
    
    if not email:
        return jsonify({"success": False, "message": "Email required"})
    
    # Find password from account.txt
    password = None
    account_file = Path("account.txt")
    if account_file.exists():
        with open(account_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith('#') or not line:
                    continue
                if '|' in line:
                    parts = line.split('|', 1)
                elif ':' in line:
                    parts = line.split(':', 1)
                else:
                    continue
                if parts[0].strip() == email:
                    password = parts[1].strip()
                    break
    
    if not password:
        return jsonify({"success": False, "message": "Password not found in account.txt"})
    
    # Get current token
    v2fun_data = Path("v2fun_data")
    email_safe = email.replace("@", "_at_").replace(".", "_")
    session_file = v2fun_data / f"v2fun_session_{email_safe}_latest.json"
    
    if not session_file.exists():
        return jsonify({"success": False, "message": "Session file not found"})
    
    with open(session_file, "r", encoding="utf-8") as f:
        session = json.load(f)
    
    old_token = session.get("tokens", {}).get("cookie_token", "")
    status = get_token_status(old_token)
    
    # Refresh token
    new_status, new_token = check_and_refresh_if_needed(old_token, email, password)
    
    if new_token:
        # Update session file
        session["tokens"]["cookie_token"] = new_token
        session["timestamp"] = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session, f, indent=2, ensure_ascii=False)
        
        # If this is the connected account, update DB
        if user.get('v2fun_token') == old_token:
            update_user_token(user['user_id'], new_token)
        
        remaining = get_time_remaining(new_token)
        return jsonify({
            "success": True,
            "message": f"Token refreshed! Valid for {remaining}",
            "new_status": new_status,
            "remaining": str(remaining)
        })
    else:
        return jsonify({
            "success": False,
            "message": f"Refresh failed. Current status: {status}",
            "new_status": new_status
        })


def auto_refresh_if_needed(user_data: dict) -> dict:
    """Auto-check and refresh token before API calls (middleware)"""
    token = user_data.get('v2fun_token')
    if not token:
        return user_data
    
    status = get_token_status(token)
    
    # Only auto-refresh if expired or critical
    if status in ("expired", "critical"):
        email = user_data.get('email') or user_data.get('google_email')
        if email:
            # Find password
            password = None
            account_file = Path("account.txt")
            if account_file.exists():
                with open(account_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('#') or not line:
                            continue
                        if '|' in line:
                            parts = line.split('|', 1)
                        elif ':' in line:
                            parts = line.split(':', 1)
                        else:
                            continue
                        if parts[0].strip() == email:
                            password = parts[1].strip()
                            break
            
            if password:
                new_status, new_token = check_and_refresh_if_needed(token, email, password)
                if new_token:
                    user_data['v2fun_token'] = new_token
                    update_user_token(user_data['user_id'], new_token)
    
    return user_data


def start_monitor(user_id: int, token: str, generation_id: int, task_uuid: str):
    """Start monitoring for generation completion (SSE + polling fallback)"""
    def download_image(url: str) -> str:
        """Download generated image to local storage"""
        if not url:
            return None
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            results_dir = Path("v2fun_data/results")
            results_dir.mkdir(parents=True, exist_ok=True)
            # Detect extension from URL
            ext = ".png"
            if ".jpg" in url or ".jpeg" in url:
                ext = ".jpg"
            elif ".webp" in url:
                ext = ".webp"
            filename = f"gen_{generation_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
            filepath = results_dir / filename
            with open(filepath, 'wb') as f:
                f.write(resp.content)
            return f"/results/{filename}"
        except Exception as e:
            print(f"Download failed: {e}")
            return None

    def push_event(ev):
        if generation_id not in pending_events:
            pending_events[generation_id] = []
        pending_events[generation_id].append(ev)

    def on_update(tid, event):
        push_event({
            "type": "progress",
            "progress": event.get("progress", 0),
            "status": event.get("status", ""),
            "work_url": event.get("work_url"),
            "thumb": event.get("thumb")
        })

    def on_done(tid, event):
        status = event.get("status", "")
        work_url = event.get("work_url") or event.get("thumb")
        db_status = "done" if status in ("C", "COMPLETED", "DONE", "SUCCESS") else "failed"
        local_url = download_image(work_url) if work_url else None
        update_generation_status(generation_id, db_status, work_url, work_url)
        push_event({"type": "done", "status": db_status, "work_url": work_url, "local_url": local_url})
        active_monitors.pop(user_id, None)

    def on_error(tid, error):
        update_generation_status(generation_id, "failed", error_message=error)
        push_event({"type": "error", "message": error})
        active_monitors.pop(user_id, None)

    # Start SSE monitor
    monitor = SSEMonitor(token)
    active_monitors[user_id] = monitor
    t = threading.Thread(target=lambda: monitor.watch(task_uuid, on_update=on_update, on_done=on_done, on_error=on_error), daemon=True)
    t.start()

    # Start polling fallback (cek status setiap 10 detik)
    def polling_fallback():
        """Poll V2Fun API for generation status (fallback if SSE doesn't work)"""
        import time
        time.sleep(10)  # Wait 10s before starting polling
        client = V2FunClient(token)
        
        # Correct request body for getResourceList (POST)
        payload = {
            "pager": {
                "orderBy": "updateTime",
                "pageSize": 10,
                "pageNo": 1,
                "needQueryCount": True
            },
            "parm": {
                "keyword": "",
                "workType": "",
                "listType": "folder",
                "isUpload": 0,
                "bindState": None,
                "license": "",
                "orderBy": "updateTime",
                "simple": 1
            }
        }
        
        max_attempts = 60  # 10 minutes max (polling every 10s)
        for attempt in range(max_attempts):
            if user_id not in active_monitors:
                return  # Monitor already finished via SSE
            
            try:
                resp = requests.post(
                    f"{client.base_url}/work/getResourceList?lan=en",
                    headers=client.headers,
                    json=payload,
                    timeout=10
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("success"):
                        result = data.get("result", {})
                        records = result.get("records") or []
                        
                        if isinstance(records, list):
                            for record in records:
                                # Navigate: record -> child[] -> works[]
                                children = record.get("child", [])
                                for child_item in children:
                                    works = child_item.get("works", [])
                                    for work in works:
                                        task_id = str(work.get("taskId", ""))
                                        gen_status = work.get("generateStatus", "")
                                        work_url = work.get("workUrl") or ""
                                        thumb = work.get("thumb") or ""
                                        progress = work.get("progress", 0)
                                        
                                        # Match by taskId
                                        if task_id == str(task_uuid):
                                            # Status "A" = Active/Done, "I" = In Progress
                                            if gen_status == "A" and (work_url or thumb):
                                                # Generation complete!
                                                full_url = work_url if work_url else thumb
                                                # Build full asset URL if relative
                                                if full_url and not full_url.startswith("http"):
                                                    full_url = f"https://asset.v2fun.ai/{full_url}"
                                                
                                                local_url = download_image(full_url)
                                                update_generation_status(generation_id, "done", full_url, thumb if thumb else full_url)
                                                push_event({
                                                    "type": "done",
                                                    "status": "done",
                                                    "work_url": full_url,
                                                    "local_url": local_url
                                                })
                                                active_monitors.pop(user_id, None)
                                                return
                                            
                                            elif gen_status == "I":
                                                # Still in progress
                                                pct = int(float(progress) * 100) if progress else 50
                                                push_event({
                                                    "type": "progress",
                                                    "progress": pct,
                                                    "status": "processing"
                                                })
                                            
                                            elif gen_status == "F":
                                                # Failed
                                                update_generation_status(generation_id, "failed", error_message="Generation failed on server")
                                                push_event({
                                                    "type": "done",
                                                    "status": "failed",
                                                    "work_url": None
                                                })
                                                active_monitors.pop(user_id, None)
                                                return
            except Exception as e:
                print(f"Polling error: {e}")
            
            time.sleep(10)
        
        # Timeout - mark as pending (user can check gallery later)
        push_event({
            "type": "done",
            "status": "timeout",
            "work_url": None
        })
        active_monitors.pop(user_id, None)

    t2 = threading.Thread(target=polling_fallback, daemon=True)
    t2.start()


@app.route('/api/generation-stream/<int:generation_id>')
def api_generation_stream(generation_id):
    """SSE endpoint - stream generation progress to browser"""
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "message": "Not authenticated"}), 401

    def event_stream():
        import time
        timeout = 300
        elapsed = 0
        while elapsed < timeout:
            events = pending_events.pop(generation_id, [])
            for ev in events:
                yield f"data: {json.dumps(ev)}\n\n"
                if ev.get("type") in ("done", "error"):
                    return
            time.sleep(1)
            elapsed += 1
        yield f"data: {json.dumps({'type': 'timeout'})}\n\n"

    return Response(event_stream(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded reference images"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/results/<filename>')
def result_file(filename):
    """Serve downloaded result images"""
    return send_from_directory(Path("v2fun_data/results"), filename)


if __name__ == '__main__':
    # Initialize database
    init_db()
    
    print("="*80)
    print("V2Fun.ai Web UI V2 - Enhanced")
    print("="*80)
    print("\nFeatures:")
    print("  [+] User registration & login")
    print("  [+] Image upload for references")
    print("  [+] Database-backed generation history")
    print("  [+] Session management")
    print("\nStarting server...")
    print("Open browser: http://localhost:5000")
    print("\nPress Ctrl+C to stop\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
