"""
V2Fun Backend API for Hermes Agent Integration
REST API with round-robin account selection and model priority

Features:
- REST API endpoint for Hermes agent
- Round-robin account rotation
- Model priority system
- Queue management
- Telegram notification
- Status tracking

Usage:
    python v2fun_backend_api.py

API Endpoints:
    POST /api/generate - Generate image
    GET  /api/status/{job_id} - Check generation status
    GET  /api/health - Health check
    GET  /api/accounts - List available accounts
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import sys
import threading
import time
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List, Dict
import uuid

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from v2fun_scripts.database import get_db, init_db
from v2fun_scripts.token_manager import is_token_valid, get_token_status

app = Flask(__name__)
CORS(app)

# Model priority (best to fallback)
MODEL_PRIORITY = [
    "nano-banana-pro",      # Priority 1: Best quality
    "gpt-image-2",          # Priority 2: Good alternative
    "nano-banana-2",        # Priority 3: Standard
    "nano-banana-2-lite",   # Priority 4: Fast
    "qwen-edit"             # Priority 5: High volume (50+ images)
]

# Account round-robin state
account_index = 0
account_lock = threading.Lock()

# Job tracking
jobs = {}  # {job_id: {status, prompt, result, error, ...}}
jobs_lock = threading.Lock()


class AccountPool:
    """Manage V2Fun accounts with round-robin selection"""
    
    def __init__(self):
        self.accounts = []
        self.current_index = 0
        self.lock = threading.Lock()
        self.load_accounts()
    
    def load_accounts(self):
        """Load all active V2Fun accounts from database"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, email, status, jwt_token, token_expiry
            FROM v2fun_accounts
            WHERE status = 'done' AND jwt_token IS NOT NULL
            ORDER BY id ASC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        self.accounts = []
        for row in rows:
            account = {
                'id': row[0],
                'email': row[1],
                'status': row[2],
                'token': row[3],
                'expiry': row[4]
            }
            
            # Check if token is still valid
            if is_token_valid(account['token']):
                self.accounts.append(account)
        
        print(f"[POOL] Loaded {len(self.accounts)} valid accounts")
    
    def get_next_account(self) -> Optional[Dict]:
        """Get next account using round-robin"""
        with self.lock:
            if not self.accounts:
                return None
            
            account = self.accounts[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.accounts)
            
            # Re-check token validity
            if not is_token_valid(account['token']):
                print(f"[POOL] Token expired for {account['email']}, reloading pool...")
                self.load_accounts()
                return self.get_next_account()
            
            return account
    
    def reload(self):
        """Reload account pool (e.g., after token refresh)"""
        with self.lock:
            old_count = len(self.accounts)
            self.load_accounts()
            new_count = len(self.accounts)
            print(f"[POOL] Reloaded: {old_count} -> {new_count} accounts")


class V2FunClient:
    """V2Fun API client"""
    
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
    
    def generate_image(self, prompt: str, model: str = "nano-banana-pro", 
                      quality: str = "medium", ratio: str = "16:9") -> Dict:
        """Generate image"""
        payload = {
            "prompt": prompt,
            "model": model,
            "ratio": ratio,
            "num": 1,
            "quality": quality
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/work/external/generate/image-generate?lan=en",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_quota(self) -> Dict:
        """Get remaining quota"""
        try:
            response = requests.post(
                f"{self.base_url}/work/get-free-cnt?lan=en",
                headers=self.headers,
                json={"configIds": []},
                timeout=10
            )
            return response.json()
        except:
            return {"success": False}


def send_telegram_notification(message: str, telegram_token: str = None, chat_id: str = None):
    """Send notification to Telegram"""
    if not telegram_token or not chat_id:
        # Load from env or config
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not telegram_token or not chat_id:
        print(f"[TELEGRAM] Not configured, skipping: {message}")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, json=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"[TELEGRAM] Error: {e}")
        return False


def process_generation_job(job_id: str, prompt: str, account: Dict, 
                          model: str, quality: str, ratio: str):
    """Background worker to process generation"""
    try:
        # Update job status
        with jobs_lock:
            jobs[job_id]['status'] = 'processing'
            jobs[job_id]['account'] = account['email']
            jobs[job_id]['model'] = model
            jobs[job_id]['started_at'] = datetime.now().isoformat()
        
        # Create client
        client = V2FunClient(account['token'])
        
        # Generate
        result = client.generate_image(prompt, model, quality, ratio)
        
        if result.get('success'):
            task_uuid = result.get('result', {}).get('taskuuid')
            
            with jobs_lock:
                jobs[job_id]['status'] = 'completed'
                jobs[job_id]['task_uuid'] = task_uuid
                jobs[job_id]['result'] = result
                jobs[job_id]['completed_at'] = datetime.now().isoformat()
            
            # Send Telegram notification
            msg = f"✅ *Generation Completed*\n"
            msg += f"Job ID: `{job_id}`\n"
            msg += f"Prompt: {prompt[:50]}...\n"
            msg += f"Model: {model}\n"
            msg += f"Account: {account['email']}\n"
            msg += f"Task UUID: {task_uuid}"
            send_telegram_notification(msg)
        else:
            error_msg = result.get('message') or result.get('error', 'Unknown error')
            
            with jobs_lock:
                jobs[job_id]['status'] = 'failed'
                jobs[job_id]['error'] = error_msg
                jobs[job_id]['completed_at'] = datetime.now().isoformat()
            
            # Send Telegram notification
            msg = f"❌ *Generation Failed*\n"
            msg += f"Job ID: `{job_id}`\n"
            msg += f"Prompt: {prompt[:50]}...\n"
            msg += f"Error: {error_msg}\n"
            msg += f"Account: {account['email']}"
            send_telegram_notification(msg)
    
    except Exception as e:
        with jobs_lock:
            jobs[job_id]['status'] = 'error'
            jobs[job_id]['error'] = str(e)
            jobs[job_id]['completed_at'] = datetime.now().isoformat()
        
        # Send Telegram notification
        msg = f"⚠️ *Generation Error*\n"
        msg += f"Job ID: `{job_id}`\n"
        msg += f"Error: {str(e)}"
        send_telegram_notification(msg)


# Initialize account pool
account_pool = AccountPool()


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "version": "1.0.0",
        "accounts_available": len(account_pool.accounts),
        "active_jobs": len([j for j in jobs.values() if j['status'] == 'processing'])
    })


@app.route('/api/accounts', methods=['GET'])
def list_accounts():
    """List available accounts"""
    accounts_info = []
    for acc in account_pool.accounts:
        accounts_info.append({
            "email": acc['email'],
            "status": get_token_status(acc['token'])
        })
    
    return jsonify({
        "success": True,
        "accounts": accounts_info,
        "total": len(accounts_info)
    })


@app.route('/api/generate', methods=['POST'])
def generate_image():
    """
    Generate image endpoint for Hermes agent
    
    Request Body:
    {
        "prompt": "your prompt here",
        "model": "nano-banana-pro" (optional, auto-selected by priority),
        "quality": "medium" (optional: low/medium/high),
        "ratio": "16:9" (optional: 1:1/16:9/9:16),
        "telegram_token": "..." (optional),
        "telegram_chat_id": "..." (optional)
    }
    
    Response:
    {
        "success": true,
        "job_id": "uuid",
        "status": "queued",
        "account": "email@gmail.com",
        "model": "nano-banana-pro"
    }
    """
    data = request.json
    
    if not data or not data.get('prompt'):
        return jsonify({
            "success": False,
            "error": "Prompt is required"
        }), 400
    
    prompt = data.get('prompt')
    model = data.get('model', MODEL_PRIORITY[0])  # Default to best model
    quality = data.get('quality', 'medium')
    ratio = data.get('ratio', '16:9')
    
    # Validate model
    if model not in MODEL_PRIORITY:
        model = MODEL_PRIORITY[0]
    
    # Get next account (round-robin)
    account = account_pool.get_next_account()
    
    if not account:
        return jsonify({
            "success": False,
            "error": "No available accounts. Please login some accounts first."
        }), 503
    
    # Create job
    job_id = str(uuid.uuid4())
    
    with jobs_lock:
        jobs[job_id] = {
            "id": job_id,
            "prompt": prompt,
            "status": "queued",
            "account": account['email'],
            "model": model,
            "quality": quality,
            "ratio": ratio,
            "created_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
            "result": None,
            "error": None
        }
    
    # Start background worker
    thread = threading.Thread(
        target=process_generation_job,
        args=(job_id, prompt, account, model, quality, ratio),
        daemon=True
    )
    thread.start()
    
    # Send Telegram notification
    msg = f"🚀 *New Generation Started*\n"
    msg += f"Job ID: `{job_id}`\n"
    msg += f"Prompt: {prompt[:50]}...\n"
    msg += f"Model: {model}\n"
    msg += f"Account: {account['email']}"
    send_telegram_notification(
        msg, 
        data.get('telegram_token'), 
        data.get('telegram_chat_id')
    )
    
    return jsonify({
        "success": True,
        "job_id": job_id,
        "status": "queued",
        "account": account['email'],
        "model": model
    })


@app.route('/api/status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get generation job status"""
    with jobs_lock:
        job = jobs.get(job_id)
    
    if not job:
        return jsonify({
            "success": False,
            "error": "Job not found"
        }), 404
    
    return jsonify({
        "success": True,
        "job": job
    })


@app.route('/api/reload-accounts', methods=['POST'])
def reload_accounts():
    """Reload account pool (admin endpoint)"""
    account_pool.reload()
    
    return jsonify({
        "success": True,
        "accounts_available": len(account_pool.accounts)
    })


if __name__ == '__main__':
    # Initialize database
    init_db()
    
    print("="*80)
    print("V2Fun Backend API for Hermes Agent")
    print("="*80)
    print(f"\nAccounts available: {len(account_pool.accounts)}")
    print(f"Model priority: {' > '.join(MODEL_PRIORITY)}")
    print(f"\nAPI Endpoints:")
    print(f"  POST http://localhost:5001/api/generate")
    print(f"  GET  http://localhost:5001/api/status/<job_id>")
    print(f"  GET  http://localhost:5001/api/health")
    print(f"  GET  http://localhost:5001/api/accounts")
    print(f"\nTelegram notifications: {'Enabled' if os.getenv('TELEGRAM_BOT_TOKEN') else 'Disabled'}")
    print(f"\nStarting server...")
    print()
    
    app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)
