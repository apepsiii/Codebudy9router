# Quick Reference - V2Fun Backend API for Hermes

## TL;DR

Backend API untuk Hermes agent generate gambar otomatis dengan:
- Round-robin account rotation
- Model priority (best to fallback)
- Telegram notifications
- REST API port 5001

---

## Quick Start

```bash
# 1. Start API
python v2fun_backend_api.py

# 2. Generate
curl -X POST http://localhost:5001/api/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a beautiful sunset"}'

# 3. Check status
curl http://localhost:5001/api/status/{job_id}
```

---

## Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/generate` | POST | Submit generation |
| `/api/status/{job_id}` | GET | Check status |
| `/api/health` | GET | Health check |
| `/api/accounts` | GET | List accounts |
| `/api/reload-accounts` | POST | Reload pool |

---

## Model Priority

1. `nano-banana-pro` (best) ← **default**
2. `gpt-image-2` (good)
3. `nano-banana-2` (standard)
4. `nano-banana-2-lite` (fast)
5. `qwen-edit` (volume 50+)

---

## Python Integration

```python
import requests

# Generate
response = requests.post("http://localhost:5001/api/generate", 
    json={"prompt": "sunset", "model": "nano-banana-pro"})
job_id = response.json()["job_id"]

# Check status
status = requests.get(f"http://localhost:5001/api/status/{job_id}")
print(status.json())
```

---

## Features

✅ Round-robin (Account 1→2→3→...→N→1)  
✅ Model priority system  
✅ Async processing  
✅ Telegram notifications  
✅ Auto token validation  

---

## Files

- `v2fun_backend_api.py` - Main API
- `hermes_integration_example.py` - Integration examples
- `test_backend_api.py` - Testing
- `V2FUN_BACKEND_API_GUIDE.md` - Full docs

---

**Version:** 3.2.0  
**Port:** 5001  
**Status:** ✅ Production Ready
