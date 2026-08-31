# V2Fun Backend API - Integration Guide for Hermes Agent

**File:** `v2fun_backend_api.py`  
**Port:** 5001  
**Purpose:** REST API untuk Hermes agent generate gambar otomatis  
**Created:** 2026-08-31

---

## 🎯 Arsitektur Overview

```
┌──────────────────────────────────────────────────────────────┐
│                      HERMES AGENT                             │
│  - Generate content ideas                                     │
│  - Create multiple prompts                                    │
│  - Send HTTP requests to V2Fun Backend                        │
│  - Receive job_id                                             │
│  - Check status                                               │
│  - Report to Telegram                                         │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     │ POST /api/generate
                     │ GET  /api/status/{job_id}
                     ▼
┌──────────────────────────────────────────────────────────────┐
│              V2FUN BACKEND API (Port 5001)                    │
│                                                               │
│  Round-Robin Account Pool:                                    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Account 1 → Account 2 → Account 3 → ... → Account N │    │
│  │      ↑                                          ↓     │    │
│  │      └──────────────────────────────────────────┘     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
│  Model Priority:                                              │
│  1. nano-banana-pro     (best quality)                        │
│  2. gpt-image-2         (good alternative)                    │
│  3. nano-banana-2       (standard)                            │
│  4. nano-banana-2-lite  (fast)                                │
│  5. qwen-edit          (high volume 50+ images)              │
│                                                               │
│  Job Queue: Async processing                                  │
│  Telegram: Real-time notifications                            │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     │ Image generation requests
                     ▼
┌──────────────────────────────────────────────────────────────┐
│                    V2FUN.AI API                               │
│  https://api.prod.v2fun.ai                                    │
└──────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Setup Environment Variables (Optional - for Telegram)

```bash
# .env file
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

### 2. Start Backend API

```bash
python v2fun_backend_api.py
```

**Output:**
```
================================================================================
V2Fun Backend API for Hermes Agent
================================================================================

Accounts available: 5
Model priority: nano-banana-pro > gpt-image-2 > nano-banana-2 > nano-banana-2-lite > qwen-edit

API Endpoints:
  POST http://localhost:5001/api/generate
  GET  http://localhost:5001/api/status/<job_id>
  GET  http://localhost:5001/api/health
  GET  http://localhost:5001/api/accounts

Telegram notifications: Enabled

Starting server...
 * Running on http://0.0.0.0:5001
```

---

## 📡 API Endpoints

### 1. Generate Image

**Endpoint:** `POST /api/generate`

**Request Body:**
```json
{
  "prompt": "a beautiful sunset over mountains",
  "model": "nano-banana-pro",
  "quality": "medium",
  "ratio": "16:9",
  "telegram_token": "optional_bot_token",
  "telegram_chat_id": "optional_chat_id"
}
```

**Parameters:**
- `prompt` (string, **required**) - Text prompt untuk generate gambar
- `model` (string, optional) - Model name, default: `nano-banana-pro`
- `quality` (string, optional) - `low` | `medium` | `high`, default: `medium`
- `ratio` (string, optional) - `1:1` | `16:9` | `9:16`, default: `16:9`
- `telegram_token` (string, optional) - Override default Telegram bot token
- `telegram_chat_id` (string, optional) - Override default chat ID

**Response (Success):**
```json
{
  "success": true,
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "queued",
  "account": "user1@gmail.com",
  "model": "nano-banana-pro"
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": "No available accounts. Please login some accounts first."
}
```

### 2. Check Job Status

**Endpoint:** `GET /api/status/{job_id}`

**Example:** `GET /api/status/a1b2c3d4-e5f6-7890-abcd-ef1234567890`

**Response:**
```json
{
  "success": true,
  "job": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "prompt": "a beautiful sunset over mountains",
    "status": "completed",
    "account": "user1@gmail.com",
    "model": "nano-banana-pro",
    "quality": "medium",
    "ratio": "16:9",
    "created_at": "2026-08-31T05:50:00",
    "started_at": "2026-08-31T05:50:01",
    "completed_at": "2026-08-31T05:50:15",
    "task_uuid": "4597907e-d224-409b-8b13-6763d8e6e903",
    "result": {
      "success": true,
      "result": {
        "taskuuid": "4597907e-d224-409b-8b13-6763d8e6e903",
        "id": "2092628864660996098",
        "taskIds": [2092628864640024577]
      }
    },
    "error": null
  }
}
```

**Status Values:**
- `queued` - Job dalam antrian
- `processing` - Sedang di-generate
- `completed` - Berhasil
- `failed` - Gagal (ada error dari V2Fun API)
- `error` - Error sistem

### 3. Health Check

**Endpoint:** `GET /api/health`

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "accounts_available": 5,
  "active_jobs": 2
}
```

### 4. List Accounts

**Endpoint:** `GET /api/accounts`

**Response:**
```json
{
  "success": true,
  "accounts": [
    {"email": "user1@gmail.com", "status": "valid"},
    {"email": "user2@gmail.com", "status": "valid"},
    {"email": "user3@gmail.com", "status": "warning"}
  ],
  "total": 3
}
```

### 5. Reload Account Pool

**Endpoint:** `POST /api/reload-accounts`

**Purpose:** Reload account pool setelah login akun baru atau refresh token

**Response:**
```json
{
  "success": true,
  "accounts_available": 7
}
```

---

## 🤖 Integration dengan Hermes Agent

### Python Example

```python
import requests
import time

class HermesV2FunIntegration:
    def __init__(self, backend_url="http://localhost:5001"):
        self.backend_url = backend_url
        self.telegram_token = "YOUR_BOT_TOKEN"
        self.telegram_chat_id = "YOUR_CHAT_ID"
    
    def generate_image(self, prompt, model="nano-banana-pro"):
        """Submit generation request"""
        response = requests.post(
            f"{self.backend_url}/api/generate",
            json={
                "prompt": prompt,
                "model": model,
                "quality": "high",
                "ratio": "16:9",
                "telegram_token": self.telegram_token,
                "telegram_chat_id": self.telegram_chat_id
            }
        )
        return response.json()
    
    def check_status(self, job_id):
        """Check generation status"""
        response = requests.get(f"{self.backend_url}/api/status/{job_id}")
        return response.json()
    
    def wait_for_completion(self, job_id, timeout=300):
        """Wait until job completes"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            result = self.check_status(job_id)
            
            if not result.get('success'):
                return None
            
            job = result['job']
            status = job['status']
            
            if status == 'completed':
                return job
            elif status in ('failed', 'error'):
                return None
            
            time.sleep(5)  # Check every 5 seconds
        
        return None  # Timeout

# Usage in Hermes Agent
hermes = HermesV2FunIntegration()

# Generate multiple images
prompts = [
    "a red sports car in the city",
    "a cute cat playing with yarn",
    "a modern house with garden"
]

jobs = []
for prompt in prompts:
    result = hermes.generate_image(prompt)
    if result.get('success'):
        jobs.append({
            'job_id': result['job_id'],
            'prompt': prompt
        })
        print(f"✅ Submitted: {prompt}")
    else:
        print(f"❌ Failed: {prompt}")

# Wait for all to complete
for job in jobs:
    completed = hermes.wait_for_completion(job['job_id'])
    if completed:
        print(f"✅ Completed: {job['prompt']}")
        print(f"   Task UUID: {completed.get('task_uuid')}")
    else:
        print(f"❌ Failed: {job['prompt']}")
```

### cURL Examples

**Generate:**
```bash
curl -X POST http://localhost:5001/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "a beautiful sunset",
    "model": "nano-banana-pro",
    "quality": "high"
  }'
```

**Check Status:**
```bash
curl http://localhost:5001/api/status/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Health Check:**
```bash
curl http://localhost:5001/api/health
```

---

## 🔄 Round-Robin Account Selection

Backend API otomatis merotasi akun menggunakan algoritma round-robin:

```
Request 1 → Account 1
Request 2 → Account 2
Request 3 → Account 3
Request 4 → Account 1 (kembali ke awal)
Request 5 → Account 2
...
```

**Keuntungan:**
- ✅ Load distribution merata
- ✅ Avoid rate limiting per account
- ✅ Maximize quota usage
- ✅ Automatic failover (skip expired tokens)

---

## 🎯 Model Priority System

Jika model yang diminta tidak di-specify atau invalid, sistem menggunakan priority:

1. **nano-banana-pro** - Kualitas terbaik (default)
2. **gpt-image-2** - Alternatif bagus
3. **nano-banana-2** - Standard
4. **nano-banana-2-lite** - Cepat
5. **qwen-edit** - Volume tinggi (bisa 50+ gambar)

**Custom Model Selection:**
```json
{
  "prompt": "test",
  "model": "qwen-edit"  // Force specific model
}
```

---

## 📱 Telegram Notifications

Backend mengirim notifikasi otomatis ke Telegram untuk setiap event:

### Job Started:
```
🚀 New Generation Started
Job ID: `a1b2c3d4-...`
Prompt: a beautiful sunset...
Model: nano-banana-pro
Account: user1@gmail.com
```

### Job Completed:
```
✅ Generation Completed
Job ID: `a1b2c3d4-...`
Prompt: a beautiful sunset...
Model: nano-banana-pro
Account: user1@gmail.com
Task UUID: 4597907e-d224-409b-8b13-6763d8e6e903
```

### Job Failed:
```
❌ Generation Failed
Job ID: `a1b2c3d4-...`
Prompt: a beautiful sunset...
Error: Token expired
Account: user1@gmail.com
```

---

## 🛠️ Setup & Configuration

### Step 1: Pastikan Accounts Tersedia

```bash
# Login Google accounts dulu
python v2fun_scripts/v2fun_google_login.py

# Check accounts
python manage_users.py list
```

### Step 2: Setup Telegram (Optional)

```bash
# Create .env file
cat > .env << EOF
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=-1001234567890
EOF
```

### Step 3: Start Backend API

```bash
python v2fun_backend_api.py
```

### Step 4: Test API

```bash
# Health check
curl http://localhost:5001/api/health

# Test generation
curl -X POST http://localhost:5001/api/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test image"}'
```

---

## 🔍 Troubleshooting

### Problem: "No available accounts"
**Solution:**
```bash
# Login accounts first
python v2fun_scripts/v2fun_google_login.py

# Then reload API
curl -X POST http://localhost:5001/api/reload-accounts
```

### Problem: Token expired
**Solution:**
```bash
# Refresh tokens
python v2fun_scripts/token_manager.py

# Reload accounts
curl -X POST http://localhost:5001/api/reload-accounts
```

### Problem: Job stuck in "processing"
**Solution:**
- Check V2Fun.ai dashboard untuk status real
- Task UUID bisa di-track manual di https://v2fun.ai

---

## 📊 Workflow Example: Hermes Agent

```python
# Hermes Agent Workflow
class HermesContentGenerator:
    def __init__(self):
        self.v2fun = HermesV2FunIntegration()
    
    def generate_content_batch(self, topic):
        """Generate content idea and create images"""
        
        # Step 1: Generate ideas (Hermes AI logic)
        ideas = self.generate_ideas(topic)
        # Result: ["idea 1", "idea 2", "idea 3"]
        
        # Step 2: Create prompts for each idea
        prompts = []
        for idea in ideas:
            prompt = self.create_prompt(idea)
            prompts.append(prompt)
        
        # Step 3: Submit all to V2Fun Backend
        jobs = []
        for prompt in prompts:
            result = self.v2fun.generate_image(prompt)
            if result.get('success'):
                jobs.append(result['job_id'])
        
        # Step 4: Wait and collect results
        results = []
        for job_id in jobs:
            completed = self.v2fun.wait_for_completion(job_id)
            if completed:
                results.append(completed)
        
        # Step 5: Report to Telegram
        self.send_report(results)
        
        return results
```

---

## 🚀 Next Steps

1. **Start Backend API**: `python v2fun_backend_api.py`
2. **Test dengan cURL atau Postman**
3. **Integrate dengan Hermes agent**
4. **Monitor Telegram untuk notifications**
5. **Scale dengan lebih banyak accounts**

---

**Version:** 1.0.0  
**Created:** 2026-08-31  
**Status:** ✅ Ready for Integration
