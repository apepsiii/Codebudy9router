# 🔄 Merge Plan: Unified V2Fun Application

**Goal:** Combine v2fun_web_v2.py + v2fun_backend_api.py into single application

---

## 📊 Current Architecture (Separated)

```
┌─────────────────────────┐     ┌─────────────────────────┐
│  v2fun_web_v2.py        │     │  v2fun_backend_api.py   │
│  Port: 5000             │     │  Port: 5001             │
│  - User Auth            │     │  - REST API             │
│  - Dashboard UI         │     │  - Round-robin          │
│  - Manual Generation    │     │  - Job Queue            │
│  - SSE Monitor          │     │  - Polling              │
└─────────────────────────┘     └─────────────────────────┘
         User                          Hermes Agent
```

---

## 🎯 Proposed Architecture (Unified)

```
┌────────────────────────────────────────────────────────┐
│              Unified V2Fun Application                  │
│                    Port: 5000                           │
│                                                         │
│  Web Routes:                API Routes:                 │
│  - /                       - /api/generate             │
│  - /login                  - /api/status/<id>          │
│  - /dashboard              - /api/accounts             │
│  - /register               - /api/health               │
│                            - /api/jobs                 │
│                                                         │
│  Shared:                                               │
│  - Database                                            │
│  - Account Pool                                        │
│  - Job Queue                                           │
│  - SSE Monitor                                         │
└────────────────────────────────────────────────────────┘
           Both Users & Hermes Agent
```

---

## ✅ Benefits of Merging

1. **Single Port** - Easier deployment, single systemd service
2. **Shared Resources** - One account pool, one job queue
3. **Unified Monitoring** - Dashboard shows both manual + API jobs
4. **Less Complexity** - One codebase to maintain
5. **Better Integration** - Web UI can call same API endpoints

---

## 🔧 Implementation Steps

### Step 1: Copy Backend API Routes to Web App

**File:** `v2fun_scripts/v2fun_web_v2.py`

Add these imports from backend_api:
```python
# Add at top
from typing import Optional, Tuple, List, Dict
import uuid
import threading
import time
```

Add AccountPool class:
```python
class AccountPool:
    """Round-robin account selection"""
    def __init__(self):
        self.accounts = []
        self.current_index = 0
        self.lock = threading.Lock()
        self.load_accounts()
    
    def load_accounts(self):
        # Load from v2fun_accounts table
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, email, status, jwt_token, token_expiry
            FROM v2fun_accounts
            WHERE status = 'done' AND jwt_token IS NOT NULL
        """)
        rows = cursor.fetchall()
        conn.close()
        
        self.accounts = []
        for row in rows:
            if is_token_valid(row[3]):
                self.accounts.append({
                    'id': row[0],
                    'email': row[1],
                    'token': row[3]
                })
    
    def get_next_account(self):
        with self.lock:
            if not self.accounts:
                return None
            account = self.accounts[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.accounts)
            return account

# Initialize account pool
account_pool = AccountPool()

# Jobs dictionary for API
jobs = {}
jobs_lock = threading.Lock()
```

### Step 2: Add API Routes

Add these routes to v2fun_web_v2.py:
```python
@app.route('/api/generate', methods=['POST'])
def api_generate_v2():
    """API endpoint for Hermes agent - stateless"""
    data = request.json
    
    if not data or not data.get('prompt'):
        return jsonify({"success": False, "error": "Prompt required"}), 400
    
    # Get account from pool (round-robin)
    account = account_pool.get_next_account()
    if not account:
        return jsonify({"success": False, "error": "No accounts available"}), 503
    
    # Create job
    job_id = str(uuid.uuid4())
    model = data.get('model', 'nano-banana-pro')
    quality = data.get('quality', 'high')
    ratio = data.get('ratio', '16:9')
    
    with jobs_lock:
        jobs[job_id] = {
            'id': job_id,
            'prompt': data['prompt'],
            'status': 'queued',
            'source': 'api',  # Mark as API request
            'account': account['email'],
            'model': model,
            'quality': quality,
            'ratio': ratio,
            'created_at': datetime.now().isoformat()
        }
    
    # Start background worker
    threading.Thread(
        target=process_api_job,
        args=(job_id, data['prompt'], account, model, quality, ratio),
        daemon=True
    ).start()
    
    return jsonify({
        'success': True,
        'job_id': job_id,
        'status': 'queued',
        'account': account['email']
    })

@app.route('/api/status/<job_id>')
def api_status(job_id):
    """Check job status"""
    job = jobs.get(job_id)
    if not job:
        return jsonify({'success': False, 'error': 'Job not found'}), 404
    
    return jsonify({'success': True, 'job': job})

@app.route('/api/health')
def api_health():
    """Health check"""
    return jsonify({
        'status': 'ok',
        'accounts': len(account_pool.accounts),
        'jobs': len(jobs)
    })

@app.route('/api/jobs')
def api_jobs():
    """List all jobs (for monitoring)"""
    # Get jobs from last 24 hours
    recent_jobs = [j for j in jobs.values()]
    recent_jobs.sort(key=lambda x: x['created_at'], reverse=True)
    
    return jsonify({
        'success': True,
        'total': len(recent_jobs),
        'jobs': recent_jobs[:50]  # Last 50 jobs
    })
```

### Step 3: Update Dashboard to Show All Jobs

Update dashboard.html to fetch from `/api/jobs`:
```javascript
async function loadAllJobs() {
    const resp = await fetch('/api/jobs');
    const data = await resp.json();
    
    // Show both manual (user) and API jobs
    renderJobsList(data.jobs);
}

function renderJobsList(jobs) {
    const html = jobs.map(job => `
        <div class="job-item ${job.source}">
            <span class="badge-${job.status}">${job.status}</span>
            <span class="job-prompt">${job.prompt}</span>
            <span class="job-source">${job.source}</span>
            <span class="job-time">${new Date(job.created_at).toLocaleString()}</span>
        </div>
    `).join('');
    
    document.getElementById('jobs-list').innerHTML = html;
}
```

### Step 4: Remove v2fun_backend_api.py

Once merged, delete:
```bash
rm v2fun_backend_api.py
rm run_backend_api.bat
```

---

## 🚀 New Unified Usage

### Start Single Application
```bash
python v2fun_scripts/v2fun_web_v2.py
```

### Access Points
```
Web UI:      http://localhost:5000
API:         http://localhost:5000/api/generate
Dashboard:   http://localhost:5000/dashboard
Jobs List:   http://localhost:5000/api/jobs
```

### For Hermes Agent
```python
# Same API, different port
requests.post('http://localhost:5000/api/generate', json={
    'prompt': 'a cat on the moon'
})
```

---

## 📋 Migration Checklist

- [ ] Copy AccountPool class to v2fun_web_v2.py
- [ ] Add API routes (/api/generate, /api/status, /api/health, /api/jobs)
- [ ] Add jobs dictionary and background worker
- [ ] Update dashboard to show API jobs
- [ ] Add source field (manual/api) to jobs
- [ ] Test API endpoints
- [ ] Test web UI still works
- [ ] Update documentation
- [ ] Update systemd service (single service)
- [ ] Delete v2fun_backend_api.py

---

## 🎯 Result

**Before:**
```bash
# Start 2 processes
python v2fun_scripts/v2fun_web_v2.py  # Port 5000
python v2fun_backend_api.py           # Port 5001
```

**After:**
```bash
# Start 1 process
python v2fun_scripts/v2fun_web_v2.py  # Port 5000 (everything)
```

---

**Should we implement this merge now?** 🤔

It will simplify the system significantly!
