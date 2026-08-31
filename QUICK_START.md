# 🚀 Quick Start - Enhanced Backend API

## Starting the Server

```bash
cd C:\laragon\www\v2fun
python v2fun_backend_api.py
```

Server starts on: `http://localhost:5001`

---

## 📱 Web Dashboard

### Access Points
- Main: `http://localhost:5001/`
- Alternative: `http://localhost:5001/ui`

### Pages
1. **Dashboard** - Overview and stats
2. **Generate** - Create new images (High quality default)
3. **Jobs** - Track all generation jobs
4. **Gallery** - View and manage completed images
5. **Accounts** - V2Fun account pool status
6. **API Docs** - Endpoint documentation

---

## 🔥 New Features Demo

### 1. Generate with Auto Fallback

**Via Web UI:**
1. Go to Generate page
2. Enter prompt
3. Click "Generate Image"
4. If quota exceeded, automatically tries next model
5. View real-time progress in Jobs page

**Via API:**
```bash
curl -X POST http://localhost:5001/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "a cat on the moon",
    "model": "nano-banana-pro"
  }'
```

Response:
```json
{
  "success": true,
  "job_id": "abc-123-def-456",
  "status": "queued",
  "account": "user@gmail.com",
  "model": "nano-banana-pro",
  "quality": "high"
}
```

---

### 2. Check Job Status (with new fields)

```bash
curl http://localhost:5001/api/status/abc-123-def-456
```

Response:
```json
{
  "success": true,
  "job": {
    "id": "abc-123-def-456",
    "prompt": "a cat on the moon",
    "status": "completed",
    "source": "api",
    "progress": 100,
    "local_path": "v2fun_data/results/gen_abc-123_20260831_a_cat_on_the_moon.jpg",
    "work_url": "https://asset.v2fun.ai/...",
    "fallback_attempts": [],
    "model": "nano-banana-pro",
    "quality": "high",
    "created_at": "2026-08-31T09:00:00",
    "completed_at": "2026-08-31T09:02:30"
  }
}
```

---

### 3. View Gallery

```bash
curl http://localhost:5001/api/gallery
```

Response:
```json
{
  "success": true,
  "total": 15,
  "images": [
    {
      "id": "abc-123",
      "prompt": "a cat on the moon",
      "status": "completed",
      "work_url": "https://...",
      "local_path": "v2fun_data/results/...",
      "model": "nano-banana-pro",
      "completed_at": "2026-08-31T09:02:30"
    }
  ]
}
```

---

### 4. View Downloaded Image

**In Browser:**
```
http://localhost:5001/api/image/abc-123-def-456
```

**Download via curl:**
```bash
curl http://localhost:5001/api/image/abc-123-def-456 -o image.jpg
```

---

### 5. Real-time Progress (SSE)

**JavaScript Example:**
```javascript
const eventSource = new EventSource('/api/stream/abc-123-def-456');

eventSource.onmessage = function(e) {
    const job = JSON.parse(e.data);
    console.log('Status:', job.status);
    console.log('Progress:', job.progress + '%');
    
    if (job.status === 'completed') {
        console.log('Image URL:', job.work_url);
        eventSource.close();
    }
};
```

**curl Example:**
```bash
curl -N http://localhost:5001/api/stream/abc-123-def-456
```

Output:
```
data: {"id":"abc-123","status":"processing","progress":30}

data: {"id":"abc-123","status":"rendering","progress":60}

data: {"id":"abc-123","status":"completed","progress":100,"work_url":"..."}
```

---

### 6. List All Jobs

```bash
# All jobs
curl http://localhost:5001/api/jobs

# Completed only
curl http://localhost:5001/api/jobs?status=completed

# Limit results
curl http://localhost:5001/api/jobs?limit=10
```

---

### 7. Delete from Gallery

```bash
curl -X DELETE http://localhost:5001/api/gallery/abc-123-def-456
```

Response:
```json
{
  "success": true,
  "message": "Job and image deleted"
}
```

---

## 🎯 Model Fallback Examples

### Example 1: Successful Fallback
```
1. Start: nano-banana-pro
   Status: Quota exceeded
   
2. Fallback: gpt-image-2
   Status: Success!
   
3. Result: Image generated with gpt-image-2
   Notification: "⚠️ Fallback used (original: nano-banana-pro)"
```

### Example 2: All Models Failed
```
1. nano-banana-pro → Quota exceeded
2. gpt-image-2 → Quota exceeded
3. nano-banana-2 → Quota exceeded
4. nano-banana-2-lite → Quota exceeded
5. qwen-edit → Quota exceeded

Result: Failed with "All models failed (quota exhausted)"
```

---

## 📊 Quality Settings

| Quality | File Size | Speed | Use Case |
|---------|-----------|-------|----------|
| **high** | 2-5 MB | Slower | **Default** - Best results |
| medium | 1-2 MB | Medium | Balanced |
| low | 500KB-1MB | Fast | Quick previews |

---

## 🔔 Telegram Notifications

Set environment variables:
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
```

You'll receive:
- 🚀 Generation started
- ✅ Generation completed (with fallback info if used)
- ❌ Generation failed
- ⚠️ Timeout or errors

---

## 📁 File Structure

```
v2fun_data/
├── results/
│   ├── gen_abc123_20260831_123045_a_cat.jpg
│   ├── gen_def456_20260831_123120_sunset.jpg
│   └── ...
└── v2fun.db
```

Filename format: `gen_{job_id}_{timestamp}_{prompt}.jpg`

---

## 🧪 Testing

Run the test suite:
```bash
python test_backend_enhancements.py
```

Expected output:
```
============================================================
Backend API Enhancement Tests
============================================================

[TEST 1] Health Check
  Status: healthy
  Accounts: 5
  Active Jobs: 2
  ✓ Health check passed

[TEST 2] Generate Image (High Quality Default)
  Job ID: abc-123-def-456
  Model: nano-banana-pro
  Quality: high
  ✓ Generation started with high quality

[TEST 3] Job Status for abc-123-def-456
  Status: processing
  Progress: 50%
  Source: api
  Fallback Attempts: 0
  ✓ Job status retrieved

...

============================================================
✓ All tests completed!
============================================================
```

---

## 🐛 Troubleshooting

### Issue: Image not found (404)
**Cause:** Image not downloaded yet or download failed  
**Solution:** Check job status, wait for completion

### Issue: All models failed
**Cause:** All accounts quota exhausted  
**Solution:** Wait for quota reset or add more accounts

### Issue: SSE stream not working
**Cause:** Firewall or proxy blocking  
**Solution:** Test with curl first, check server logs

### Issue: Dashboard not loading
**Cause:** Server not running or port conflict  
**Solution:** Check `http://localhost:5001/api/health`

---

## 📈 Monitoring

### Check Health
```bash
curl http://localhost:5001/api/health
```

### View Active Jobs
```bash
curl http://localhost:5001/api/jobs?status=processing
```

### View Failed Jobs
```bash
curl http://localhost:5001/api/jobs?status=failed
```

---

## 💡 Pro Tips

1. **Fallback Strategy:** Start with best model, system auto-downgrades
2. **Quality:** Use "high" for final outputs, "low" for testing
3. **Monitoring:** Use SSE for real-time updates instead of polling
4. **Storage:** Clean up old images regularly (they accumulate fast)
5. **Accounts:** Rotate multiple accounts for high volume work

---

## 🔗 Integration Examples

### Node.js
```javascript
const axios = require('axios');

async function generateImage(prompt) {
    const response = await axios.post('http://localhost:5001/api/generate', {
        prompt: prompt,
        model: 'nano-banana-pro'
    });
    
    const jobId = response.data.job_id;
    console.log('Job started:', jobId);
    
    // Poll for result
    while (true) {
        const status = await axios.get(`http://localhost:5001/api/status/${jobId}`);
        const job = status.data.job;
        
        if (job.status === 'completed') {
            console.log('Image URL:', job.work_url);
            break;
        }
        
        await new Promise(r => setTimeout(r, 5000));
    }
}
```

### Python
```python
import requests
import time

def generate_image(prompt):
    # Start generation
    response = requests.post('http://localhost:5001/api/generate', json={
        'prompt': prompt,
        'model': 'nano-banana-pro'
    })
    
    job_id = response.json()['job_id']
    print(f'Job started: {job_id}')
    
    # Wait for completion
    while True:
        status = requests.get(f'http://localhost:5001/api/status/{job_id}')
        job = status.json()['job']
        
        if job['status'] == 'completed':
            print(f"Image URL: {job['work_url']}")
            print(f"Local path: {job['local_path']}")
            if job['fallback_attempts']:
                print(f"Used fallback: {len(job['fallback_attempts'])} attempts")
            break
        
        time.sleep(5)
```

---

**Ready to use!** 🎉

Start the server and open `http://localhost:5001` to try the enhanced features.
