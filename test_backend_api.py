"""
Test Script for V2Fun Backend API
Quick testing untuk semua endpoints
"""

import requests
import time
import sys

BASE_URL = "http://localhost:5001"

def test_health():
    """Test health check endpoint"""
    print("\n" + "="*60)
    print("TEST 1: Health Check")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        result = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {result}")
        
        if result.get('status') == 'healthy':
            print("✅ Health check PASSED")
            return True
        else:
            print("❌ Health check FAILED")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_accounts():
    """Test list accounts endpoint"""
    print("\n" + "="*60)
    print("TEST 2: List Accounts")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/accounts", timeout=5)
        result = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Total Accounts: {result.get('total', 0)}")
        
        accounts = result.get('accounts', [])
        for acc in accounts:
            print(f"  - {acc['email']}: {acc['status']}")
        
        if result.get('success') and result.get('total', 0) > 0:
            print("✅ List accounts PASSED")
            return True
        else:
            print("⚠️  No accounts available")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_generate():
    """Test generate endpoint"""
    print("\n" + "="*60)
    print("TEST 3: Generate Image")
    print("="*60)
    
    payload = {
        "prompt": "a beautiful sunset over mountains (test image)",
        "model": "nano-banana-pro",
        "quality": "medium",
        "ratio": "16:9"
    }
    
    print(f"Prompt: {payload['prompt']}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/generate",
            json=payload,
            timeout=30
        )
        result = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {result}")
        
        if result.get('success'):
            job_id = result['job_id']
            print(f"✅ Generate PASSED")
            print(f"   Job ID: {job_id}")
            return job_id
        else:
            print(f"❌ Generate FAILED: {result.get('error')}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_status(job_id):
    """Test status endpoint"""
    print("\n" + "="*60)
    print("TEST 4: Check Status")
    print("="*60)
    
    print(f"Job ID: {job_id}")
    
    try:
        response = requests.get(f"{BASE_URL}/api/status/{job_id}", timeout=5)
        result = response.json()
        
        print(f"Status Code: {response.status_code}")
        
        if result.get('success'):
            job = result.get('job', {})
            print(f"Job Status: {job.get('status')}")
            print(f"Account: {job.get('account')}")
            print(f"Model: {job.get('model')}")
            print(f"Created: {job.get('created_at')}")
            
            print("✅ Status check PASSED")
            return True
        else:
            print(f"❌ Status check FAILED")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_wait_completion(job_id, timeout=60):
    """Test waiting for job completion"""
    print("\n" + "="*60)
    print("TEST 5: Wait for Completion")
    print("="*60)
    
    print(f"Job ID: {job_id}")
    print(f"Timeout: {timeout}s")
    
    start_time = time.time()
    
    try:
        while time.time() - start_time < timeout:
            response = requests.get(f"{BASE_URL}/api/status/{job_id}", timeout=5)
            result = response.json()
            
            if not result.get('success'):
                print(f"❌ Failed to get status")
                return False
            
            job = result.get('job', {})
            status = job.get('status')
            
            elapsed = int(time.time() - start_time)
            print(f"[{elapsed}s] Status: {status}")
            
            if status == 'completed':
                print(f"✅ Job completed!")
                print(f"   Task UUID: {job.get('task_uuid')}")
                return True
            elif status in ('failed', 'error'):
                print(f"❌ Job failed: {job.get('error')}")
                return False
            
            time.sleep(5)
        
        print(f"⚠️  Timeout after {timeout}s (job still processing)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_batch_generate():
    """Test batch generation"""
    print("\n" + "="*60)
    print("TEST 6: Batch Generation")
    print("="*60)
    
    prompts = [
        "test image 1: red car",
        "test image 2: blue house",
        "test image 3: green tree"
    ]
    
    jobs = []
    
    for i, prompt in enumerate(prompts, 1):
        print(f"\n[{i}/{len(prompts)}] Submitting: {prompt}")
        
        payload = {"prompt": prompt, "quality": "low"}  # Use low quality for faster testing
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/generate",
                json=payload,
                timeout=30
            )
            result = response.json()
            
            if result.get('success'):
                job_id = result['job_id']
                jobs.append(job_id)
                print(f"  ✅ Job ID: {job_id}")
            else:
                print(f"  ❌ Failed: {result.get('error')}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        time.sleep(1)
    
    print(f"\n✅ Batch generation: {len(jobs)}/{len(prompts)} submitted")
    return len(jobs) == len(prompts)


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*80)
    print("V2FUN BACKEND API - AUTOMATED TESTS")
    print("="*80)
    print(f"Target: {BASE_URL}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # Test 1: Health Check
    results['health'] = test_health()
    
    if not results['health']:
        print("\n❌ Backend not healthy. Stopping tests.")
        return results
    
    # Test 2: List Accounts
    results['accounts'] = test_accounts()
    
    if not results['accounts']:
        print("\n⚠️  No accounts available. Some tests may fail.")
    
    # Test 3: Generate
    job_id = test_generate()
    results['generate'] = job_id is not None
    
    if job_id:
        # Test 4: Status
        results['status'] = test_status(job_id)
        
        # Test 5: Wait Completion (skip untuk save time)
        # Uncomment jika mau test full workflow
        # results['completion'] = test_wait_completion(job_id, timeout=60)
    
    # Test 6: Batch Generation
    results['batch'] = test_batch_generate()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test, result in results.items():
        icon = "✅" if result else "❌"
        print(f"{icon} {test.upper()}")
    
    print(f"\nTotal: {passed}/{total} passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
    
    return results


if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_name = sys.argv[1].lower()
        
        if test_name == "health":
            test_health()
        elif test_name == "accounts":
            test_accounts()
        elif test_name == "generate":
            job_id = test_generate()
            if job_id:
                test_status(job_id)
        elif test_name == "batch":
            test_batch_generate()
        else:
            print(f"Unknown test: {test_name}")
            print("Available tests: health, accounts, generate, batch")
    else:
        run_all_tests()
