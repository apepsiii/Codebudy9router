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
    
    def poll_result(self, task_uuid: str, max_attempts: int = 60, interval: int = 5) -> Dict:
        """Poll V2Fun API until image generation is complete
        
        Args:
            task_uuid: Task UUID from generate_image response
            max_attempts: Maximum polling attempts (default: 60 = 5 minutes with 5s interval)
            interval: Seconds between polling attempts (default: 5)
            
        Returns:
            Dict with workUrl, thumb, and status
        """
        payload = {
            "pager": {
                "orderBy": "updateTime",
                "pageSize": 20,
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
        
        for attempt in range(max_attempts):
            try:
                response = requests.post(
                    f"{self.base_url}/work/getResourceList?lan=en",
                    headers=self.headers,
                    json=payload,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        result = data.get("result", {})
                        records = result.get("records") or []
                        
                        for record in records:
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
                                            
                                            return {
                                                "success": True,
                                                "status": "completed",
                                                "workUrl": full_url,
                                                "thumb": thumb if thumb else full_url,
                                                "progress": 100,
                                                "attempts": attempt + 1
                                            }
                                        
                                        elif gen_status == "I":
                                            # Still in progress
                                            pct = int(float(progress) * 100) if progress else 50
                                            print(f"[POLL] Attempt {attempt+1}/{max_attempts}: {pct}% (status: {gen_status})")
                                            time.sleep(interval)
                                            break  # Continue outer loop
                                        
                                        elif gen_status == "E":
                                            # Error
                                            return {
                                                "success": False,
                                                "status": "failed",
                                                "error": "Generation failed on V2Fun side"
                                            }
            except Exception as e:
                print(f"[POLL] Error on attempt {attempt+1}: {e}")
                time.sleep(interval)
        
        # Timeout
        return {
            "success": False,
            "status": "timeout",
            "error": f"Polling timeout after {max_attempts * interval}s"
        }


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
            
            # Update job with task_uuid
            with jobs_lock:
                jobs[job_id]['status'] = 'rendering'
                jobs[job_id]['task_uuid'] = task_uuid
                jobs[job_id]['result'] = result
            
            print(f"[JOB {job_id}] Task submitted to V2Fun: {task_uuid}")
            
            # Poll for result (wait until image is ready)
            poll_result = client.poll_result(task_uuid, max_attempts=60, interval=5)
            
            if poll_result.get('success'):
                # Image generation completed!
                work_url = poll_result.get('workUrl')
                thumb = poll_result.get('thumb')
                
                with jobs_lock:
                    jobs[job_id]['status'] = 'completed'
                    jobs[job_id]['work_url'] = work_url
                    jobs[job_id]['thumb'] = thumb
                    jobs[job_id]['poll_attempts'] = poll_result.get('attempts')
                    jobs[job_id]['completed_at'] = datetime.now().isoformat()
                
                print(f"[JOB {job_id}] Completed! URL: {work_url}")
                
                # Send Telegram notification
                msg = f"✅ *Generation Completed*\n"
                msg += f"Job ID: `{job_id}`\n"
                msg += f"Prompt: {prompt[:50]}...\n"
                msg += f"Model: {model}\n"
                msg += f"Account: {account['email']}\n"
                msg += f"Image URL: {work_url}"
                send_telegram_notification(msg)
            else:
                # Polling failed or timeout
                error_msg = poll_result.get('error', 'Polling failed')
                
                with jobs_lock:
                    jobs[job_id]['status'] = 'timeout'
                    jobs[job_id]['error'] = error_msg
                    jobs[job_id]['task_uuid'] = task_uuid
                    jobs[job_id]['completed_at'] = datetime.now().isoformat()
                
                print(f"[JOB {job_id}] Polling failed: {error_msg}")
                
                # Send Telegram notification
                msg = f"⚠️ *Generation Timeout*\n"
                msg += f"Job ID: `{job_id}`\n"
                msg += f"Prompt: {prompt[:50]}...\n"
                msg += f"Error: {error_msg}\n"
                msg += f"Task UUID: {task_uuid} (check manually on V2Fun)"
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


# ============================================================================
# WEB UI - Simple dashboard for Backend API
# ============================================================================

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>V2Fun Backend API - Dashboard</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --color-primary: #7C3AED;
            --color-on-primary: #FFFFFF;
            --color-secondary: #6366F1;
            --color-accent: #EC4899;
            --color-background: #FAF5FF;
            --color-foreground: #0F172A;
            --color-muted: #F7F3FD;
            --color-border: #EFE7FC;
            --color-destructive: #DC2626;
            --space-1: 4px; --space-2: 8px; --space-3: 12px; --space-4: 16px;
            --space-6: 24px; --space-8: 32px; --space-10: 40px; --space-12: 48px;
            --radius-sm: 6px; --radius-md: 10px; --radius-lg: 16px;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'DM Sans', sans-serif;
            background: var(--color-background);
            color: var(--color-foreground);
            min-height: 100vh;
        }
        .sidebar {
            position: fixed; top: 0; left: 0; bottom: 0; width: 240px;
            background: white; border-right: 1px solid var(--color-border);
            display: flex; flex-direction: column; padding: var(--space-6);
            z-index: 100;
        }
        .sidebar-logo {
            font-family: 'Space Grotesk', sans-serif; font-size: 22px;
            font-weight: 700; color: var(--color-primary);
            margin-bottom: var(--space-8); padding-bottom: var(--space-6);
            border-bottom: 1px solid var(--color-border);
        }
        .sidebar-logo span { color: var(--color-accent); }
        .nav-item {
            display: flex; align-items: center; gap: var(--space-3);
            padding: var(--space-3) var(--space-4); border-radius: var(--radius-md);
            font-size: 14px; font-weight: 500; color: #64748b;
            cursor: pointer; transition: background 150ms ease, color 150ms ease;
            text-decoration: none; margin-bottom: var(--space-1);
        }
        .nav-item:hover { background: var(--color-muted); color: var(--color-primary); }
        .nav-item.active { background: var(--color-muted); color: var(--color-primary); font-weight: 600; }
        .nav-icon { width: 18px; height: 18px; }
        .sidebar-bottom {
            margin-top: auto; padding-top: var(--space-6);
            border-top: 1px solid var(--color-border);
        }
        .status-dot {
            width: 8px; height: 8px; border-radius: 50%;
            background: #10b981; display: inline-block; margin-right: 6px;
        }
        .status-dot.offline { background: #ef4444; }
        .main { margin-left: 240px; padding: var(--space-8); min-height: 100vh; }
        .page { display: none; }
        .page.active { display: block; }
        .page-header { margin-bottom: var(--space-8); }
        .page-header h1 {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 28px; font-weight: 700; margin-bottom: var(--space-2);
        }
        .page-header p { color: #64748b; font-size: 14px; }
        .card {
            background: white; border-radius: var(--radius-lg);
            padding: var(--space-6); border: 1px solid var(--color-border);
            margin-bottom: var(--space-6);
        }
        .card-title {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 16px; font-weight: 600; margin-bottom: var(--space-4);
        }
        .stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: var(--space-4); margin-bottom: var(--space-6); }
        .stat-card {
            background: white; border-radius: var(--radius-lg); padding: var(--space-6);
            border: 1px solid var(--color-border); text-align: center;
        }
        .stat-value { font-family: 'Space Grotesk', sans-serif; font-size: 32px; font-weight: 700; color: var(--color-primary); }
        .stat-label { font-size: 13px; color: #64748b; margin-top: 4px; }
        .form-group { margin-bottom: var(--space-4); }
        .form-group label { display: block; margin-bottom: var(--space-2); font-size: 13px; font-weight: 500; }
        .form-group input, .form-group select, .form-group textarea {
            width: 100%; padding: 10px 14px; border: 2px solid var(--color-border);
            border-radius: var(--radius-md); font-size: 14px; font-family: inherit;
            transition: border-color 150ms ease; background: white; color: var(--color-foreground);
        }
        .form-group input:focus, .form-group select:focus, .form-group textarea:focus {
            outline: none; border-color: var(--color-primary);
        }
        .form-group textarea { resize: vertical; min-height: 120px; }
        .form-row { display: grid; grid-template-columns: 2fr 1fr; gap: var(--space-4); }
        .btn {
            padding: 10px 20px; border-radius: var(--radius-md); font-size: 14px;
            font-weight: 600; font-family: 'Space Grotesk', sans-serif;
            cursor: pointer; transition: opacity 150ms ease, transform 150ms ease;
            border: none; display: inline-flex; align-items: center; gap: var(--space-2);
        }
        .btn:hover { opacity: 0.9; transform: translateY(-1px); }
        .btn:active { transform: translateY(0); }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
        .btn-primary { background: var(--color-primary); color: white; }
        .btn-accent { background: var(--color-accent); color: white; }
        .btn-outline { background: transparent; color: var(--color-primary); border: 2px solid var(--color-primary); }
        .btn-sm { padding: 6px 14px; font-size: 12px; }
        .btn-full { width: 100%; justify-content: center; }
        .alert {
            padding: 12px 16px; border-radius: var(--radius-md);
            margin-bottom: var(--space-4); font-size: 14px; display: none;
        }
        .alert.active { display: block; }
        .alert.success { background: #D1FAE5; color: #065F46; border: 1px solid #A7F3D0; }
        .alert.error { background: #FEE2E2; color: #991B1B; border: 1px solid #FECACA; }
        .alert.info { background: #E0E7FF; color: #3730A3; border: 1px solid #C7D2FE; }
        .badge {
            display: inline-flex; align-items: center; padding: 2px 8px;
            border-radius: 99px; font-size: 11px; font-weight: 600;
        }
        .badge-pending { background: #FEF3C7; color: #92400E; }
        .badge-processing { background: #E0E7FF; color: #3730A3; }
        .badge-done { background: #D1FAE5; color: #065F46; }
        .badge-failed { background: #FEE2E2; color: #991B1B; }
        .spinner {
            border: 3px solid var(--color-muted);
            border-top: 3px solid var(--color-primary);
            border-radius: 50%; width: 32px; height: 32px;
            animation: spin 1s linear infinite;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .accounts-table { width: 100%; border-collapse: collapse; font-size: 14px; }
        .accounts-table th {
            text-align: left; padding: var(--space-3) var(--space-4);
            border-bottom: 2px solid var(--color-border);
            font-weight: 600; color: #64748b; font-size: 12px; text-transform: uppercase;
        }
        .accounts-table td {
            padding: var(--space-3) var(--space-4);
            border-bottom: 1px solid var(--color-border);
        }
        .accounts-table tr:last-child td { border-bottom: none; }
        .accounts-table tr:hover td { background: var(--color-muted); }
        .gallery-grid {
            display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: var(--space-4);
        }
        .gallery-item {
            border-radius: var(--radius-md); overflow: hidden;
            border: 1px solid var(--color-border); background: white;
            transition: transform 150ms ease, box-shadow 150ms ease;
        }
        .gallery-item:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(124,58,237,0.1); }
        .gallery-item img { width: 100%; aspect-ratio: 1; object-fit: cover; }
        .gallery-item-info { padding: var(--space-3); }
        .gallery-item-prompt { font-size: 12px; color: var(--color-foreground); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: var(--space-1); }
        .gallery-item-meta { font-size: 11px; color: #94a3b8; }
        .job-card {
            background: white; border-radius: var(--radius-lg);
            border: 1px solid var(--color-border); padding: var(--space-6);
            margin-bottom: var(--space-4);
        }
        .job-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-3); }
        .job-id { font-family: monospace; font-size: 12px; color: #64748b; }
        .job-prompt { font-size: 14px; margin-bottom: var(--space-3); }
        .job-result-img { max-width: 100%; border-radius: var(--radius-md); border: 2px solid var(--color-border); }
        .progress-bar-bg { background: var(--color-muted); border-radius: 99px; height: 8px; overflow: hidden; margin: var(--space-3) 0; }
        .progress-bar-fill { height: 100%; background: var(--color-primary); border-radius: 99px; transition: width 300ms ease; }
        .code-block {
            background: #1e293b; color: #e2e8f0; padding: var(--space-4);
            border-radius: var(--radius-md); font-family: 'Courier New', monospace;
            font-size: 13px; overflow-x: auto; margin-top: var(--space-3);
        }
        .code-block .key { color: #93c5fd; }
        .code-block .str { color: #86efac; }
        .endpoint-card {
            background: var(--color-muted); border-radius: var(--radius-md);
            padding: var(--space-4); margin-bottom: var(--space-3);
        }
        .method-badge {
            display: inline-block; padding: 2px 8px; border-radius: 6px;
            font-size: 11px; font-weight: 700; font-family: monospace; margin-right: 8px;
        }
        .method-get { background: #DBEAFE; color: #1E40AF; }
        .method-post { background: #D1FAE5; color: #065F46; }
        @media (max-width: 768px) {
            .sidebar { display: none; }
            .main { margin-left: 0; padding: var(--space-4); }
            .form-row { grid-template-columns: 1fr; }
            .stats-row { grid-template-columns: repeat(2, 1fr); }
        }
        @media (prefers-reduced-motion: reduce) {
            * { animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; }
        }
    </style>
</head>
<body>

<aside class="sidebar">
    <div class="sidebar-logo">V2Fun<span> API</span></div>
    <nav>
        <a class="nav-item active" onclick="showPage('dashboard', event)" href="#">
            <svg class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>
            Dashboard
        </a>
        <a class="nav-item" onclick="showPage('generate', event)" href="#">
            <svg class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
            Generate
        </a>
        <a class="nav-item" onclick="showPage('jobs', event)" href="#">
            <svg class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>
            Jobs
        </a>
        <a class="nav-item" onclick="showPage('accounts', event)" href="#">
            <svg class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a4 4 0 00-3-3.87M9 20H4v-2a4 4 0 013-3.87m6-2a4 4 0 10-8 0 4 4 0 008 0zm6 0a4 4 0 11-8 0 4 4 0 018 0z"/></svg>
            Accounts
        </a>
        <a class="nav-item" onclick="showPage('docs', event)" href="#">
            <svg class="nav-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
            API Docs
        </a>
    </nav>
    <div class="sidebar-bottom">
        <div style="display:flex;align-items:center;gap:8px;padding:8px">
            <span class="status-dot" id="statusDot"></span>
            <span style="font-size:13px;font-weight:500" id="statusText">Checking...</span>
        </div>
        <div style="font-size:11px;color:#94a3b8;padding:0 8px" id="versionText">v1.0.0</div>
    </div>
</aside>

<main class="main">

    <!-- Dashboard Page -->
    <div id="page-dashboard" class="page active">
        <div class="page-header">
            <h1>Dashboard</h1>
            <p>Monitor V2Fun Backend API status and job queue</p>
        </div>
        <div id="alert-dash" class="alert"></div>
        <div class="stats-row">
            <div class="stat-card">
                <div class="stat-value" id="statAccounts">—</div>
                <div class="stat-label">Available Accounts</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="statJobs">—</div>
                <div class="stat-label">Active Jobs</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="statTotal">—</div>
                <div class="stat-label">Total Jobs</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="statStatus">—</div>
                <div class="stat-label">API Status</div>
            </div>
        </div>
        <div class="card">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:var(--space-4)">
                <div class="card-title" style="margin:0">Model Priority</div>
                <button class="btn btn-primary btn-sm" onclick="loadDashboard()">
                    <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
                    Refresh
                </button>
            </div>
            <div id="modelList"><p style="color:#94a3b8;text-align:center;padding:20px">Loading...</p></div>
        </div>
        <div class="card">
            <div class="card-title">Recent Jobs</div>
            <div id="recentJobs"><p style="color:#94a3b8;text-align:center;padding:20px">Loading...</p></div>
        </div>
    </div>

    <!-- Generate Page -->
    <div id="page-generate" class="page">
        <div class="page-header">
            <h1>Generate Image</h1>
            <p>Submit a prompt to generate an image via V2Fun API</p>
        </div>
        <div id="alert-gen" class="alert"></div>
        <div class="card">
            <div class="card-title">Prompt</div>
            <div class="form-group">
                <textarea id="prompt" placeholder="Describe the image you want to generate..." maxlength="5000" oninput="updateCharCount()"></textarea>
                <div style="text-align:right;font-size:12px;color:#94a3b8;margin-top:4px" id="charCount">0 / 5000</div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Model</label>
                    <select id="model">
                        <option value="nano-banana-pro">nano-banana-pro (Best)</option>
                        <option value="gpt-image-2">gpt-image-2</option>
                        <option value="nano-banana-2">nano-banana-2</option>
                        <option value="nano-banana-2-lite">nano-banana-2-lite (Fast)</option>
                        <option value="qwen-edit">qwen-edit (High volume)</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Aspect Ratio</label>
                    <select id="aspect">
                        <option value="1:1">1:1 (Square)</option>
                        <option value="16:9">16:9 (Wide)</option>
                        <option value="9:16">9:16 (Portrait)</option>
                        <option value="4:3">4:3</option>
                        <option value="3:4">3:4</option>
                    </select>
                </div>
            </div>
            <button class="btn btn-primary btn-full" id="generateBtn" onclick="generateImage()">
                <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                Generate Image
            </button>
        </div>
        <div class="card" id="genResult" style="display:none">
            <div class="card-title">Result</div>
            <div id="genResultContent"></div>
        </div>
    </div>

    <!-- Jobs Page -->
    <div id="page-jobs" class="page">
        <div class="page-header">
            <h1>Jobs</h1>
            <p>Track all image generation jobs</p>
        </div>
        <div id="alert-jobs" class="alert"></div>
        <div class="card">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:var(--space-4)">
                <div class="card-title" style="margin:0">All Jobs</div>
                <button class="btn btn-primary btn-sm" onclick="loadJobs()">Refresh</button>
            </div>
            <div id="jobsList"><p style="color:#94a3b8;text-align:center;padding:20px">Loading...</p></div>
        </div>
    </div>

    <!-- Accounts Page -->
    <div id="page-accounts" class="page">
        <div class="page-header">
            <h1>Accounts</h1>
            <p>V2Fun account pool with round-robin selection</p>
        </div>
        <div id="alert-accounts" class="alert"></div>
        <div class="card">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:var(--space-4)">
                <div class="card-title" style="margin:0">Account Pool</div>
                <button class="btn btn-primary btn-sm" onclick="reloadAccounts()">Reload Pool</button>
            </div>
            <div id="accountsList"><p style="color:#94a3b8;text-align:center;padding:20px">Loading...</p></div>
        </div>
    </div>

    <!-- API Docs Page -->
    <div id="page-docs" class="page">
        <div class="page-header">
            <h1>API Documentation</h1>
            <p>REST API endpoints for V2Fun Backend</p>
        </div>
        <div class="card">
            <div class="card-title">Endpoints</div>
            <div class="endpoint-card">
                <span class="method-badge method-get">GET</span>
                <code>/api/health</code>
                <p style="font-size:13px;color:#64748b;margin-top:8px">Check API health, account count, and active jobs</p>
            </div>
            <div class="endpoint-card">
                <span class="method-badge method-get">GET</span>
                <code>/api/accounts</code>
                <p style="font-size:13px;color:#64748b;margin-top:8px">List all available V2Fun accounts</p>
            </div>
            <div class="endpoint-card">
                <span class="method-badge method-post">POST</span>
                <code>/api/generate</code>
                <p style="font-size:13px;color:#64748b;margin-top:8px">Submit image generation job</p>
                <div class="code-block">{ "prompt": "string", "model": "nano-banana-pro", "aspect": "1:1" }</div>
            </div>
            <div class="endpoint-card">
                <span class="method-badge method-get">GET</span>
                <code>/api/status/&lt;job_id&gt;</code>
                <p style="font-size:13px;color:#64748b;margin-top:8px">Check status of a specific job</p>
            </div>
            <div class="endpoint-card">
                <span class="method-badge method-post">POST</span>
                <code>/api/reload-accounts</code>
                <p style="font-size:13px;color:#64748b;margin-top:8px">Reload the account pool (admin)</p>
            </div>
        </div>
        <div class="card">
            <div class="card-title">Example: Generate Image</div>
            <div class="code-block">curl -X POST https://image-gen-v2.gxa.my.id/api/generate \\
  -H "Content-Type: application/json" \\
  -d '{"prompt": "a cat on the moon", "model": "nano-banana-pro"}'</div>
        </div>
        <div class="card">
            <div class="card-title">Example: Check Status</div>
            <div class="code-block">curl https://image-gen-v2.gxa.my.id/api/status/&lt;job_id&gt;</div>
        </div>
    </div>

</main>

<script>
const API = window.location.origin;
let currentPage = 'dashboard';
let pollInterval = null;
let activeJobIds = [];

function showPage(name, event) {
    currentPage = name;
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.getElementById('page-' + name).classList.add('active');
    if (event && event.currentTarget) { event.currentTarget.classList.add('active'); }
    if (name === 'dashboard') loadDashboard();
    if (name === 'jobs') loadJobs();
    if (name === 'accounts') loadAccounts();
}

async function apiGet(path) {
    const r = await fetch(API + path);
    return r.json();
}

async function apiPost(path, body) {
    const r = await fetch(API + path, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(body)
    });
    return r.json();
}

async function loadDashboard() {
    try {
        const h = await apiGet('/api/health');
        document.getElementById('statAccounts').textContent = h.accounts_available;
        document.getElementById('statJobs').textContent = h.active_jobs;
        document.getElementById('statTotal').textContent = h.total_jobs || h.active_jobs;
        document.getElementById('statStatus').textContent = h.status === 'healthy' ? '✓ Healthy' : '✗ Error';
        document.getElementById('statStatus').style.color = h.status === 'healthy' ? '#10b981' : '#ef4444';
        document.getElementById('versionText').textContent = 'v' + h.version;
        document.getElementById('statusText').textContent = h.status === 'healthy' ? 'Online' : 'Offline';
        document.getElementById('statusDot').className = h.status === 'healthy' ? 'status-dot' : 'status-dot offline';

        // Model priority list
        const models = ['nano-banana-pro', 'gpt-image-2', 'nano-banana-2', 'nano-banana-2-lite', 'qwen-edit'];
        const labels = ['Best quality', 'Good alternative', 'Standard', 'Fast', 'High volume (50+)'];
        document.getElementById('modelList').innerHTML = models.map((m, i) => 
            `<div style="display:flex;align-items:center;gap:12px;padding:10px 0;${i < models.length-1 ? 'border-bottom:1px solid var(--color-border)' : ''}">
                <span style="background:var(--color-muted);color:var(--color-primary);font-weight:700;font-size:12px;width:24px;height:24px;border-radius:50%;display:flex;align-items:center;justify-content:center">${i+1}</span>
                <span style="font-weight:600;font-size:14px">${m}</span>
                <span style="color:#94a3b8;font-size:13px;margin-left:auto">${labels[i]}</span>
            </div>`
        ).join('');

        // Recent jobs
        if (activeJobIds.length > 0) {
            document.getElementById('recentJobs').innerHTML = activeJobIds.slice(0, 5).map(id =>
                `<div style="padding:8px 0;border-bottom:1px solid var(--color-border)">
                    <span class="job-id">${id}</span>
                    <span id="dash-job-${id}" style="margin-left:12px"><span class="badge badge-processing">Checking...</span></span>
                </div>`
            ).join('');
            for (const id of activeJobIds.slice(0, 5)) { pollJob(id, 'dash-job-' + id); }
        } else {
            document.getElementById('recentJobs').innerHTML = '<p style="color:#94a3b8;text-align:center;padding:20px">No active jobs</p>';
        }
    } catch (err) {
        showAlert('alert-dash', 'Error: ' + err.message, 'error');
    }
}

async function loadAccounts() {
    try {
        const data = await apiGet('/api/accounts');
        const accounts = data.accounts || [];
        if (accounts.length === 0) {
            document.getElementById('accountsList').innerHTML = '<p style="color:#94a3b8;text-align:center;padding:20px">No accounts available</p>';
            return;
        }
        document.getElementById('accountsList').innerHTML = `
            <table class="accounts-table">
                <thead><tr><th>#</th><th>Email</th><th>Status</th></tr></thead>
                <tbody>
                ${accounts.map((a, i) => `
                    <tr>
                        <td>${i+1}</td>
                        <td style="font-size:13px">${a.email}</td>
                        <td><span class="badge badge-done">${a.status}</span></td>
                    </tr>
                `).join('')}
                </tbody>
            </table>`;
    } catch (err) {
        document.getElementById('accountsList').innerHTML = `<p style="color:#ef4444;text-align:center;padding:20px">Error: ${err.message}</p>`;
    }
}

async function reloadAccounts() {
    try {
        const data = await apiPost('/api/reload-accounts', {});
        showAlert('alert-accounts', `Reloaded! ${data.accounts_available} accounts available`, data.success ? 'success' : 'error');
        loadAccounts();
    } catch (err) {
        showAlert('alert-accounts', 'Error: ' + err.message, 'error');
    }
}

async function loadJobs() {
    if (activeJobIds.length === 0) {
        document.getElementById('jobsList').innerHTML = '<p style="color:#94a3b8;text-align:center;padding:20px">No jobs yet. Generate an image first!</p>';
        return;
    }
    document.getElementById('jobsList').innerHTML = activeJobIds.map(id => `
        <div class="job-card" id="job-card-${id}">
            <div class="job-card-header">
                <span class="job-id">${id}</span>
                <span id="job-status-${id}"><span class="badge badge-processing">Loading...</span></span>
            </div>
            <div id="job-body-${id}"></div>
        </div>
    `).join('');
    for (const id of activeJobIds) { pollJob(id, 'job-status-' + id, 'job-body-' + id); }
}

async function pollJob(jobId, statusElId, bodyElId) {
    try {
        const data = await apiGet('/api/status/' + jobId);
        const statusEl = document.getElementById(statusElId);
        if (!statusEl) return;
        const badge = data.status === 'done' ? 'badge-done' : data.status === 'failed' ? 'badge-failed' : 'badge-processing';
        statusEl.innerHTML = `<span class="badge ${badge}">${data.status}</span>`;

        if (bodyElId) {
            const bodyEl = document.getElementById(bodyElId);
            if (bodyEl) {
                if (data.status === 'processing' || data.status === 'pending') {
                    bodyEl.innerHTML = `
                        <div class="job-prompt">${data.prompt || ''}</div>
                        <div class="progress-bar-bg"><div class="progress-bar-fill" style="width:${data.progress || 0}%"></div></div>
                        <p style="font-size:12px;color:#94a3b8">${data.message || 'Processing...'}</p>`;
                } else if (data.status === 'done' && data.image_url) {
                    bodyEl.innerHTML = `
                        <div class="job-prompt">${data.prompt || ''}</div>
                        <img class="job-result-img" src="${data.image_url}" alt="Result" style="max-height:300px">
                        <div style="margin-top:10px;display:flex;gap:8px">
                            <a href="${data.image_url}" target="_blank" class="btn btn-primary btn-sm">Open</a>
                            <a href="${data.image_url}" download class="btn btn-outline btn-sm">Download</a>
                        </div>`;
                } else if (data.status === 'failed') {
                    bodyEl.innerHTML = `<div class="job-prompt">${data.prompt || ''}</div><p style="color:#ef4444">${data.error || 'Generation failed'}</p>`;
                } else {
                    bodyEl.innerHTML = `<div class="job-prompt">${data.prompt || ''}</div><pre style="font-size:12px;color:#64748b">${JSON.stringify(data, null, 2)}</pre>`;
                }
            }
        }
    } catch (err) {
        const el = document.getElementById(statusElId);
        if (el) el.innerHTML = `<span class="badge badge-failed">Error</span>`;
    }
}

async function generateImage() {
    const prompt = document.getElementById('prompt').value.trim();
    if (!prompt) { showAlert('alert-gen', 'Please enter a prompt', 'error'); return; }
    const model = document.getElementById('model').value;
    const aspect = document.getElementById('aspect').value;
    const btn = document.getElementById('generateBtn');
    btn.disabled = true; btn.innerHTML = '<div class="spinner" style="width:18px;height:18px;border-width:2px"></div> Generating...';

    try {
        const data = await apiPost('/api/generate', { prompt, model, aspect });
        if (data.success || data.job_id) {
            const jobId = data.job_id;
            activeJobIds.unshift(jobId);
            showAlert('alert-gen', `Job created: ${jobId}`, 'success');
            document.getElementById('genResult').style.display = 'block';
            document.getElementById('genResultContent').innerHTML = `
                <p style="font-size:14px;margin-bottom:12px"><strong>Job ID:</strong> <code>${jobId}</code></p>
                <div id="gen-job-status"><span class="badge badge-processing">Processing...</span></div>
                <div id="gen-job-body"></div>`;
            startPolling(jobId);
        } else {
            showAlert('alert-gen', data.message || 'Generation failed', 'error');
        }
    } catch (err) {
        showAlert('alert-gen', 'Error: ' + err.message, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg> Generate Image';
    }
}

function startPolling(jobId) {
    const poll = () => {
        pollJob(jobId, 'gen-job-status', 'gen-job-body');
        if (currentPage === 'dashboard' || currentPage === 'jobs') {
            pollJob(jobId, 'dash-job-' + jobId);
            pollJob(jobId, 'job-status-' + jobId, 'job-body-' + jobId);
        }
    };
    poll();
    const interval = setInterval(() => {
        poll();
        // Stop polling after 5 minutes
        setTimeout(() => clearInterval(interval), 300000);
    }, 3000);
}

function updateCharCount() {
    const t = document.getElementById('prompt');
    const c = document.getElementById('charCount');
    c.textContent = `${t.value.length} / 5000`;
    c.style.color = t.value.length > 4900 ? '#ef4444' : t.value.length > 4000 ? '#f59e0b' : '#94a3b8';
}

function showAlert(id, message, type) {
    const el = document.getElementById(id);
    if (!el) return;
    el.className = 'alert ' + type + ' active';
    el.textContent = message;
    setTimeout(() => el.classList.remove('active'), 5000);
}

// Auto-refresh dashboard every 10s
setInterval(() => { if (currentPage === 'dashboard') loadDashboard(); }, 10000);
loadDashboard();
</script>
</body>
</html>"""


@app.route('/', methods=['GET'])
def dashboard_ui():
    """Serve the web UI dashboard"""
    return DASHBOARD_HTML


@app.route('/ui', methods=['GET'])
def dashboard_ui_alias():
    """Alias for /ui path"""
    return DASHBOARD_HTML


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
