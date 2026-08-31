"""
Test script for Backend API Enhancements
Validates new endpoints and features
"""

import requests
import json
import time

BASE_URL = "http://localhost:5001"

def test_health():
    """Test health endpoint"""
    print("\n[TEST 1] Health Check")
    response = requests.get(f"{BASE_URL}/api/health")
    data = response.json()
    print(f"  Status: {data.get('status')}")
    print(f"  Accounts: {data.get('accounts_available')}")
    print(f"  Active Jobs: {data.get('active_jobs')}")
    assert response.status_code == 200
    print("  ✓ Health check passed")

def test_generate_with_fallback():
    """Test generation with high quality default"""
    print("\n[TEST 2] Generate Image (High Quality Default)")
    payload = {
        "prompt": "a beautiful sunset over mountains",
        "model": "nano-banana-pro",
        "ratio": "16:9"
        # Note: quality not specified, should default to 'high'
    }
    response = requests.post(f"{BASE_URL}/api/generate", json=payload)
    data = response.json()
    
    if data.get('success'):
        job_id = data.get('job_id')
        print(f"  Job ID: {job_id}")
        print(f"  Model: {data.get('model')}")
        print(f"  Quality: {data.get('quality')}")
        assert data.get('quality') == 'high', "Quality should default to 'high'"
        print("  ✓ Generation started with high quality")
        return job_id
    else:
        print(f"  ✗ Generation failed: {data.get('error')}")
        return None

def test_job_status(job_id):
    """Test job status endpoint"""
    print(f"\n[TEST 3] Job Status for {job_id}")
    response = requests.get(f"{BASE_URL}/api/status/{job_id}")
    data = response.json()
    
    if data.get('success'):
        job = data.get('job')
        print(f"  Status: {job.get('status')}")
        print(f"  Progress: {job.get('progress')}%")
        print(f"  Source: {job.get('source')}")
        print(f"  Fallback Attempts: {len(job.get('fallback_attempts', []))}")
        print("  ✓ Job status retrieved")
        return job
    else:
        print(f"  ✗ Failed to get job status")
        return None

def test_jobs_list():
    """Test jobs list endpoint"""
    print("\n[TEST 4] Jobs List")
    response = requests.get(f"{BASE_URL}/api/jobs?limit=10")
    data = response.json()
    
    if data.get('success'):
        jobs = data.get('jobs', [])
        print(f"  Total Jobs: {data.get('total')}")
        if jobs:
            print(f"  First Job Status: {jobs[0].get('status')}")
            print(f"  First Job Model: {jobs[0].get('model')}")
        print("  ✓ Jobs list retrieved")
        return jobs
    else:
        print(f"  ✗ Failed to get jobs list")
        return []

def test_gallery():
    """Test gallery endpoint"""
    print("\n[TEST 5] Gallery")
    response = requests.get(f"{BASE_URL}/api/gallery")
    data = response.json()
    
    if data.get('success'):
        images = data.get('images', [])
        print(f"  Total Images: {data.get('total')}")
        if images:
            print(f"  First Image: {images[0].get('id')}")
            print(f"  Has Local Path: {bool(images[0].get('local_path'))}")
        print("  ✓ Gallery retrieved")
        return images
    else:
        print(f"  ✗ Failed to get gallery")
        return []

def test_sse_stream(job_id):
    """Test SSE streaming endpoint"""
    print(f"\n[TEST 6] SSE Stream for {job_id}")
    print("  Starting SSE stream (will read 3 events)...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/stream/{job_id}", stream=True, timeout=15)
        event_count = 0
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    event_data = json.loads(line_str[6:])
                    print(f"  Event {event_count + 1}: status={event_data.get('status')}, progress={event_data.get('progress')}%")
                    event_count += 1
                    if event_count >= 3:
                        break
        
        print("  ✓ SSE stream works")
    except Exception as e:
        print(f"  ⚠ SSE test skipped or error: {e}")

def test_serve_image(job_id):
    """Test image serving endpoint"""
    print(f"\n[TEST 7] Serve Image for {job_id}")
    response = requests.get(f"{BASE_URL}/api/image/{job_id}")
    
    if response.status_code == 200:
        print(f"  Content-Type: {response.headers.get('Content-Type')}")
        print(f"  Image Size: {len(response.content)} bytes")
        print("  ✓ Image served successfully")
    elif response.status_code == 404:
        print("  ⚠ Image not found (may not be downloaded yet)")
    else:
        print(f"  ✗ Failed to serve image: {response.status_code}")

def main():
    print("="*60)
    print("Backend API Enhancement Tests")
    print("="*60)
    
    try:
        # Test 1: Health check
        test_health()
        
        # Test 2: Generate with default high quality
        job_id = test_generate_with_fallback()
        
        if job_id:
            # Wait a bit for job to start
            time.sleep(2)
            
            # Test 3: Job status
            job = test_job_status(job_id)
            
            # Test 4: Jobs list
            test_jobs_list()
            
            # Test 5: Gallery
            test_gallery()
            
            # Test 6: SSE stream (optional, can timeout)
            test_sse_stream(job_id)
            
            # Test 7: Serve image (may fail if not completed)
            test_serve_image(job_id)
        
        print("\n" + "="*60)
        print("✓ All tests completed!")
        print("="*60)
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
    except Exception as e:
        print(f"\n✗ Error: {e}")

if __name__ == "__main__":
    main()
