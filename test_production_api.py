"""
Test Production Backend API
"""
import requests
import json

BASE_URL = "https://image-gen-v2.gxa.my.id"

def test_accounts():
    """Test accounts endpoint"""
    print("\n" + "="*60)
    print("TEST: Get Accounts")
    print("="*60)
    try:
        r = requests.get(f"{BASE_URL}/api/accounts", timeout=10)
        print(f"Status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            print(f"Total accounts: {len(data.get('accounts', []))}")
            for i, acc in enumerate(data.get('accounts', [])[:5]):
                print(f"  {i+1}. {acc['email']} - {acc['status']}")
            return True
        else:
            print(f"Error: {r.text[:200]}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_generate_simple():
    """Test simple generation"""
    print("\n" + "="*60)
    print("TEST: Simple Generation")
    print("="*60)
    
    payload = {
        "prompt": "a red apple on a white table"
    }
    
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        r = requests.post(
            f"{BASE_URL}/api/generate",
            json=payload,
            timeout=30
        )
        
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text[:500]}")
        
        if r.status_code == 200:
            data = r.json()
            if data.get('success'):
                print(f"SUCCESS!")
                print(f"Job ID: {data.get('job_id')}")
                print(f"Account: {data.get('account')}")
                print(f"Model: {data.get('model')}")
                return data.get('job_id')
        
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_generate_with_model():
    """Test generation with specific model"""
    print("\n" + "="*60)
    print("TEST: Generation with Model nano-banana-pro")
    print("="*60)
    
    payload = {
        "prompt": "a cute cat sitting on the moon",
        "model": "nano-banana-pro",
        "quality": "medium",
        "ratio": "16:9"
    }
    
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        r = requests.post(
            f"{BASE_URL}/api/generate",
            json=payload,
            timeout=30
        )
        
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text}")
        
        if r.status_code == 200:
            data = r.json()
            if data.get('success'):
                print(f"SUCCESS!")
                return data.get('job_id')
        
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_status(job_id):
    """Test status check"""
    if not job_id:
        print("\nSkipping status test (no job_id)")
        return
    
    print("\n" + "="*60)
    print(f"TEST: Check Status for {job_id}")
    print("="*60)
    
    try:
        r = requests.get(f"{BASE_URL}/api/status/{job_id}", timeout=10)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("="*60)
    print("PRODUCTION API TEST")
    print(f"Target: {BASE_URL}")
    print("="*60)
    
    # Test 1: Check accounts
    accounts_ok = test_accounts()
    
    if not accounts_ok:
        print("\nAccounts endpoint failed. Cannot proceed.")
        exit(1)
    
    # Test 2: Simple generation
    job_id = test_generate_simple()
    
    if job_id:
        test_status(job_id)
    
    # Test 3: Generation with model
    job_id2 = test_generate_with_model()
    
    if job_id2:
        test_status(job_id2)
    
    print("\n" + "="*60)
    print("TESTS COMPLETED")
    print("="*60)
