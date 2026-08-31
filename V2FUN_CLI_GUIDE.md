# V2Fun CLI Tool - Documentation

**File:** `v2fun_scripts/v2fun_cli.py`  
**Purpose:** Generate AI images from V2Fun.ai via command line  
**Version:** 1.0  
**Last Updated:** 2026-08-29

---

## 📋 Apa itu V2Fun CLI?

**V2Fun CLI** adalah command-line interface untuk generate gambar AI dari V2Fun.ai langsung dari terminal, tanpa perlu membuka browser atau web UI.

### Kegunaan Utama:
- ✅ Generate images via terminal
- ✅ Automation & scripting
- ✅ Quick testing
- ✅ Batch generation
- ✅ Integration dengan tools lain

---

## 🚀 Quick Start

### Basic Generation
```bash
python v2fun_scripts/v2fun_cli.py generate --prompt "a red sports car"
```

### With Options
```bash
python v2fun_scripts/v2fun_cli.py generate \
  --prompt "cute cat playing" \
  --quality high \
  --ratio 1:1 \
  --show-info
```

### List Available Sessions
```bash
python v2fun_scripts/v2fun_cli.py list-sessions
```

---

## 📖 Commands & Parameters

### 1. Generate Command

```bash
python v2fun_cli.py generate [OPTIONS]
```

**Required Parameters:**
- `--prompt, -p` : Text prompt untuk generation (REQUIRED)

**Optional Parameters:**
- `--model, -m` : Model name (default: `nano-banana-pro`)
- `--quality, -q` : Quality level: `low` | `medium` | `high` (default: `medium`)
- `--ratio, -r` : Aspect ratio: `1:1` | `16:9` | `9:16` (default: `16:9`)
- `--num, -n` : Number of images to generate (default: `1`)
- `--image, -i` : Reference image path (optional, not yet implemented)
- `--email, -e` : Specify which account to use (optional)
- `--show-info` : Show user info and balance before generating

### 2. List Sessions Command

```bash
python v2fun_cli.py list-sessions
```

Lists all available login sessions from `v2fun_data/` folder.

---

## 💡 Usage Examples

### Example 1: Simple Generation
```bash
python v2fun_scripts/v2fun_cli.py generate --prompt "a beautiful sunset over mountains"
```

**Output:**
```
[+] Loaded session for: user@gmail.com
Submitting generation request...
Prompt: a beautiful sunset over mountains
Model: nano-banana-pro
Quality: medium
Ratio: 16:9
[+] Generation request submitted successfully!

GENERATION RESULT
═══════════════════════════════════════
Task UUID: 4597907e-d224-409b-8b13-6763d8e6e903
Work Area ID: 2092628864660996098
Status: In Progress (I)
```

### Example 2: High Quality 1:1
```bash
python v2fun_scripts/v2fun_cli.py generate \
  --prompt "portrait of a cat, oil painting style" \
  --quality high \
  --ratio 1:1
```

### Example 3: Show User Info
```bash
python v2fun_scripts/v2fun_cli.py generate \
  --prompt "cyberpunk city" \
  --show-info
```

**Output:**
```
User Info:
  Username: h2zfoAuser@gmail.com
  User ID: 2092617327473930241

Balance:
  Credits: 50

Submitting generation request...
```

### Example 4: Use Specific Account
```bash
python v2fun_scripts/v2fun_cli.py generate \
  --prompt "fantasy castle" \
  --email user2@gmail.com
```

### Example 5: List All Sessions
```bash
python v2fun_scripts/v2fun_cli.py list-sessions
```

**Output:**
```
Available Sessions:

┌────┬──────────────────────┬────────────┬──────────────────┐
│ No.│ Email                │ User ID    │ Timestamp        │
├────┼──────────────────────┼────────────┼──────────────────┤
│ 1  │ user1@gmail.com      │ N/A        │ 20260827_150255  │
│ 2  │ user2@gmail.com      │ N/A        │ 20260827_160310  │
│ 3  │ user3@gmail.com      │ N/A        │ 20260828_091520  │
└────┴──────────────────────┴────────────┴──────────────────┘
```

---

## 🔧 How It Works

### Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    V2Fun CLI Workflow                        │
└─────────────────────────────────────────────────────────────┘

1. User runs CLI command
   │
2. CLI loads token from session file
   └─> v2fun_data/v2fun_session_*_latest.json
   
3. Create V2FunClient with token
   │
4. Submit generation request
   │
   POST /work/external/generate/image-generate
   Headers:
     - Authorization: {JWT_TOKEN}
     - X-Access-Token: {JWT_TOKEN}
   Body:
     {
       "prompt": "...",
       "model": "nano-banana-pro",
       "quality": "medium",
       "ratio": "16:9",
       "num": 1
     }
   
5. Receive response
   │
   {
     "success": true,
     "result": {
       "taskuuid": "4597907e-...",
       "taskIds": [2092628864640024577],
       "child": [...]
     }
   }
   
6. Save result to file
   └─> v2fun_data/generations/generation_{uuid}_{timestamp}.json
   
7. Display result to user
   │
8. User checks actual image at:
   └─> https://v2fun.ai (web dashboard)
   └─> or http://localhost:5000 (local web UI)
```

---

## 📊 CLI vs Web UI Comparison

| Feature | CLI | Web UI |
|---------|-----|--------|
| **Text-to-Image** | ✅ Yes | ✅ Yes |
| **Quality Selection** | ✅ Yes | ✅ Yes |
| **Ratio Selection** | ✅ Yes | ✅ Yes |
| **Reference Images** | ❌ Not yet | ✅ Yes |
| **Real-time Progress** | ❌ No (SSE) | ✅ Yes |
| **Auto Download** | ❌ No | ✅ Yes |
| **Gallery View** | ❌ No | ✅ Yes |
| **Account Management** | ❌ No | ✅ Yes |
| **Quota Dashboard** | ❌ No | ✅ Yes |
| **Batch Processing** | ✅ Easy | ⚠️ Manual |
| **Scripting** | ✅ Easy | ❌ Hard |
| **Server (no GUI)** | ✅ Works | ❌ Needs browser |

---

## 🎯 Use Cases

### Use Case 1: Quick Testing
```bash
# Test single generation
python v2fun_cli.py generate --prompt "test image"
```

### Use Case 2: Batch Generation (Script)
```bash
#!/bin/bash
# batch_generate.sh

prompts=(
  "a red car"
  "a blue house"
  "a green tree"
)

for prompt in "${prompts[@]}"; do
  echo "Generating: $prompt"
  python v2fun_cli.py generate --prompt "$prompt"
  sleep 5
done
```

### Use Case 3: Different Quality Levels
```bash
# Generate same prompt with different qualities
python v2fun_cli.py generate --prompt "sunset" --quality low
python v2fun_cli.py generate --prompt "sunset" --quality medium
python v2fun_cli.py generate --prompt "sunset" --quality high
```

### Use Case 4: Different Ratios
```bash
# Test all ratios
python v2fun_cli.py generate --prompt "landscape" --ratio 16:9
python v2fun_cli.py generate --prompt "portrait" --ratio 9:16
python v2fun_cli.py generate --prompt "square" --ratio 1:1
```

### Use Case 5: Integration with Other Tools
```python
# Python script integration
import subprocess
import json

def generate_image(prompt):
    result = subprocess.run(
        ['python', 'v2fun_cli.py', 'generate', '--prompt', prompt],
        capture_output=True,
        text=True
    )
    return result.returncode == 0

# Use in your workflow
if generate_image("my custom prompt"):
    print("Generation successful!")
```

---

## ⚠️ Limitations

### Current Limitations:

1. **No Real-time Monitoring**
   - CLI submits request but doesn't monitor progress
   - Need to check web dashboard for completion
   - No SSE (Server-Sent Events) support yet

2. **No Image Upload**
   - Reference image parameter exists but not implemented
   - `upload_reference_image()` function is TODO
   - Cannot upload to Alibaba Cloud OSS yet

3. **No Auto Download**
   - Result is saved as JSON metadata only
   - Actual image URL is in response but not downloaded
   - Need to manually download from V2Fun dashboard

4. **Limited User Info**
   - Can show basic info but limited detail
   - Token expiry check not shown
   - Quota details limited

### Workarounds:

**For Real-time Monitoring:**
```bash
# Submit via CLI, monitor via Web UI
python v2fun_cli.py generate --prompt "test"
# Then open: http://localhost:5000
```

**For Reference Images:**
```bash
# Use Web UI instead for now
# http://localhost:5000 -> Upload Image -> Generate
```

---

## 🔍 Troubleshooting

### Problem: "No session files found"
**Solution:**
```bash
# Login first to get tokens
python v2fun_scripts/v2fun_google_login.py
```

### Problem: "No token found in session"
**Solution:**
```bash
# Re-login to refresh token
python v2fun_scripts/v2fun_google_login.py
```

### Problem: "Request failed: 401 Unauthorized"
**Solution:**
```bash
# Token expired, refresh it
python v2fun_scripts/token_manager.py
# Or re-login
python v2fun_scripts/v2fun_google_login.py
```

### Problem: Generation submitted but no image
**Solution:**
- Check V2Fun web dashboard: https://v2fun.ai
- Or check local web UI: http://localhost:5000
- Look in Gallery for completed generations

---

## 📂 Output Files

### Generation Result JSON
**Location:** `v2fun_data/generations/generation_{uuid}_{timestamp}.json`

**Content:**
```json
{
  "taskuuid": "4597907e-d224-409b-8b13-6763d8e6e903",
  "taskIds": [2092628864640024577],
  "id": "2092628864660996098",
  "userId": "2092617327473930241",
  "areaType": "1",
  "createTime": "2026-08-29 10:30:00",
  "child": [
    {
      "id": "2092628864673579009",
      "workAreaId": "2092628864660996098",
      "prompt": "a red sports car",
      "generateStatus": "I",
      "model": "nano-banana-pro",
      "quality": "medium",
      "ratio": "16:9",
      "progress": 0
    }
  ]
}
```

---

## 🚀 Future Improvements

### Planned Features:

1. **Real-time Progress Monitoring**
   ```bash
   python v2fun_cli.py generate --prompt "test" --watch
   # Shows live progress: 0% -> 25% -> 50% -> 100%
   ```

2. **Auto Download Results**
   ```bash
   python v2fun_cli.py generate --prompt "test" --download
   # Automatically downloads completed image
   ```

3. **Reference Image Upload**
   ```bash
   python v2fun_cli.py generate --prompt "test" --image ref.jpg
   # Uploads to OSS and uses as reference
   ```

4. **Batch Generation from File**
   ```bash
   python v2fun_cli.py batch --file prompts.txt
   # Reads prompts from file and generates all
   ```

5. **Token Status Check**
   ```bash
   python v2fun_cli.py status
   # Shows token validity, expiry, credits
   ```

---

## 🔗 Related Tools

- **v2fun_google_login.py** - Login & get tokens
- **v2fun_web_v2.py** - Full-featured web UI
- **token_manager.py** - Token refresh & monitoring
- **capture_generation_flow.py** - API debugging

---

## 📚 See Also

- **CHEATSHEET.md** - Quick commands reference
- **API_GENERATION_ANALYSIS.md** - API documentation
- **README.md** - Project overview

---

**Last Updated:** 2026-08-29 10:36 WIB  
**Status:** ✅ Production Ready (with limitations)  
**Maintainer:** apepsiii
