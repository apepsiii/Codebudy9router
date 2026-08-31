# 📋 Backend API Enhancement Plan

**Date:** 2026-08-31  
**Priority:** High  
**Status:** Ready for Implementation

---

## 🎯 Goals

1. **Model Fallback Mechanism** - Auto-retry dengan model lain jika akun kena limit
2. **Default Quality High** - Set semua generation ke quality="high"
3. **Image Preview** - Tampilkan hasil generate di dashboard
4. **Real-time Progress** - Live progress tracking untuk active jobs
5. **Job Management UI** - List jobs dengan expand/collapse detail
6. **Job Metadata** - Track source (API/Manual) dan timestamp
7. **Gallery Manager** - Manage hasil generate yang sudah complete

---

## 🔧 Technical Implementation

### 1. Model Fallback Mechanism

**Location:** `v2fun_backend_api.py` - `process_generation_job()`

**Logic:**
```python
def process_generation_job_with_fallback(job_id, prompt, account, model, quality, ratio):
    """Process with model fallback on quota limit"""
    
    # Try models in priority order
    models_to_try = [model] + [m for m in MODEL_PRIORITY if m != model]
    
    for attempt_model in models_to_try:
        result = client.generate_image(prompt, attempt_model, quality, ratio)
        
        if result.get('success'):
            # Success! Proceed with polling
            return process_normally(result, attempt_model)
        
        # Check if error is quota limit
        error = result.get('message', '').lower()
        if 'quota' in error or 'limit' in error or 'insufficient' in error:
            print(f"[FALLBACK] Model {attempt_model} quota exceeded, trying next model...")
            with jobs_lock:
                jobs[job_id]['fallback_attempts'].append({
                    'model': attempt_model,
                    'error': error,
                    'timestamp': datetime.now().isoformat()
                })
            continue  # Try next model
        else:
            # Non-quota error, fail immediately
            return handle_error(result)
    
    # All models failed
    return handle_all_models_failed()
```

**Changes Required:**
- Add `fallback_attempts` list to job structure
- Implement fallback loop in `process_generation_job()`
- Log each fallback attempt
- Update Telegram notifications to mention fallback

---

### 2. Default Quality = High

**Location:** `v2fun_backend_api.py` - Line 506

**Change:**
```python
# Before:
quality = data.get('quality', 'medium')

# After:
quality = data.get('quality', 'high')  # Default to high quality
```

**Impact:**
- Larger file sizes
- Better image quality
- Slightly longer generation time

---

### 3. Job Structure Enhancement

**Add new fields:**
```python
jobs[job_id] = {
    "id": job_id,
    "prompt": prompt,
    "status": "queued",  # queued, processing, rendering, completed, failed, timeout, error
    "source": "api",  # "api" or "manual"
    "account": account['email'],
    "model": model,
    "quality": quality,
    "ratio": ratio,
    "created_at": datetime.now().isoformat(),
    "started_at": None,
    "completed_at": None,
    "task_uuid": None,
    "work_url": None,
    "thumb": None,
    "local_path": None,  # NEW: downloaded image path
    "progress": 0,  # NEW: 0-100%
    "poll_attempts": 0,
    "fallback_attempts": [],  # NEW: list of fallback attempts
    "result": None,
    "error": None
}
```

---

### 4. Image Download Integration

**Add download function in background worker:**
```python
if poll_result.get('success'):
    work_url = poll_result.get('workUrl')
    
    # Download image to local storage
    from image_downloader import download_image
    local_path = download_image(work_url, job_id, prompt)
    
    with jobs_lock:
        jobs[job_id]['status'] = 'completed'
        jobs[job_id]['work_url'] = work_url
        jobs[job_id]['local_path'] = local_path  # Save local path
        jobs[job_id]['completed_at'] = datetime.now().isoformat()
```

**Add route to serve images:**
```python
@app.route('/api/image/<job_id>', methods=['GET'])
def serve_job_image(job_id):
    """Serve downloaded image for a job"""
    job = jobs.get(job_id)
    if not job or not job.get('local_path'):
        return jsonify({"error": "Image not found"}), 404
    
    return send_file(job['local_path'], mimetype='image/jpeg')
```

---

### 5. Dashboard UI Enhancements

**Add Jobs List Section:**
```html
<div id="jobs-section" class="card">
    <h2>Recent Jobs</h2>
    <div id="jobs-list">
        <!-- Jobs will be populated here -->
    </div>
</div>
```

**Job Item Template:**
```html
<div class="job-item" data-job-id="{job_id}">
    <div class="job-header" onclick="toggleJob('{job_id}')">
        <span class="job-prompt">{prompt}</span>
        <span class="job-status badge-{status}">{status}</span>
        <span class="job-time">{created_at}</span>
        <span class="job-source">{source}</span>
    </div>
    <div class="job-details" id="job-{job_id}" style="display:none">
        <div class="job-meta">
            <p>Model: {model}</p>
            <p>Account: {account}</p>
            <p>Quality: {quality}</p>
        </div>
        {if completed}
        <div class="job-result">
            <img src="/api/image/{job_id}" alt="Result" />
            <button onclick="downloadImage('{job_id}')">Download</button>
        </div>
        {/if}
        {if processing}
        <div class="job-progress">
            <div class="progress-bar">
                <div class="progress-fill" style="width:{progress}%"></div>
            </div>
            <span>{progress}%</span>
        </div>
        {/if}
    </div>
</div>
```

---

### 6. Real-time Progress Updates

**Add SSE endpoint:**
```python
@app.route('/api/stream/<job_id>')
def stream_job_progress(job_id):
    """SSE endpoint for real-time job updates"""
    def event_stream():
        last_status = None
        while True:
            job = jobs.get(job_id)
            if not job:
                yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
                break
            
            if job['status'] != last_status:
                yield f"data: {json.dumps(job)}\n\n"
                last_status = job['status']
            
            if job['status'] in ['completed', 'failed', 'timeout', 'error']:
                break
            
            time.sleep(2)  # Poll every 2 seconds
    
    return Response(event_stream(), mimetype='text/event-stream')
```

**Client-side JavaScript:**
```javascript
function watchJobProgress(jobId) {
    const eventSource = new EventSource(`/api/stream/${jobId}`);
    
    eventSource.onmessage = function(e) {
        const job = JSON.parse(e.data);
        updateJobUI(job);
        
        if (job.status === 'completed') {
            showJobResult(job);
            eventSource.close();
        }
    };
}
```

---

### 7. Gallery Manager

**New Route:**
```python
@app.route('/api/gallery', methods=['GET'])
def get_gallery():
    """Get all completed jobs with images"""
    completed = [j for j in jobs.values() 
                 if j['status'] == 'completed' and j.get('work_url')]
    
    # Sort by completion time
    completed.sort(key=lambda x: x['completed_at'], reverse=True)
    
    return jsonify({
        "success": True,
        "total": len(completed),
        "images": completed
    })

@app.route('/api/gallery/<job_id>/delete', methods=['DELETE'])
def delete_from_gallery(job_id):
    """Delete job and its image"""
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Not found"}), 404
    
    # Delete local file if exists
    if job.get('local_path'):
        try:
            os.remove(job['local_path'])
        except:
            pass
    
    # Remove from jobs dict
    del jobs[job_id]
    
    return jsonify({"success": True})
```

**Gallery UI:**
```html
<div id="gallery-page" class="page">
    <h1>Image Gallery</h1>
    <div class="gallery-grid">
        <!-- Images in grid layout -->
    </div>
</div>
```

---

## 📊 Database Schema (Optional - for persistence)

**Add jobs table:**
```sql
CREATE TABLE jobs (
    id TEXT PRIMARY KEY,
    prompt TEXT NOT NULL,
    status TEXT NOT NULL,
    source TEXT DEFAULT 'api',
    account TEXT,
    model TEXT,
    quality TEXT,
    ratio TEXT,
    work_url TEXT,
    local_path TEXT,
    progress INTEGER DEFAULT 0,
    task_uuid TEXT,
    error TEXT,
    created_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

---

## 🧪 Testing Checklist

- [ ] Test fallback mechanism dengan akun yang sudah limit
- [ ] Verify default quality = high
- [ ] Test image preview di dashboard
- [ ] Verify real-time progress updates
- [ ] Test expand/collapse job details
- [ ] Test gallery view dan delete
- [ ] Test source tracking (API vs Manual)
- [ ] Load testing dengan multiple concurrent jobs

---

## 📦 Files to Modify

1. `v2fun_backend_api.py` - Main logic
2. Dashboard HTML (embedded) - UI enhancements
3. `image_downloader.py` - Integration (already exists)
4. Test scripts - Update for new features

---

## 🚀 Deployment Steps

1. Implement changes locally
2. Test thoroughly
3. Commit and push to GitHub
4. Pull on VPS
5. Restart backend API service
6. Monitor logs for errors
7. Test production endpoints

---

## 📝 Notes

- **File Size Impact:** High quality akan membuat file lebih besar (~2-5MB per image)
- **Storage:** Monitor disk space untuk downloaded images
- **Performance:** Fallback mechanism akan slow down jika banyak model yang fail
- **UI/UX:** Pastikan loading states clear dan responsive

---

**Status:** Ready to implement  
**Estimated Time:** 3-4 hours  
**Priority:** High
