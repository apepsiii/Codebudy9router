"""
Example: Hermes Agent Integration with V2Fun Backend API

This is a sample implementation showing how Hermes agent
can integrate with V2Fun backend for automated image generation.
"""

import requests
import time
import json
from typing import List, Dict, Optional

class V2FunBackendClient:
    """Client untuk V2Fun Backend API"""
    
    def __init__(self, backend_url: str = "http://localhost:5001", 
                 telegram_token: str = None, telegram_chat_id: str = None):
        self.backend_url = backend_url
        self.telegram_token = telegram_token
        self.telegram_chat_id = telegram_chat_id
    
    def health_check(self) -> Dict:
        """Check backend health"""
        try:
            response = requests.get(f"{self.backend_url}/api/health", timeout=5)
            return response.json()
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    def generate(self, prompt: str, model: str = "nano-banana-pro", 
                quality: str = "medium", ratio: str = "16:9") -> Dict:
        """Submit generation request"""
        payload = {
            "prompt": prompt,
            "model": model,
            "quality": quality,
            "ratio": ratio
        }
        
        if self.telegram_token:
            payload["telegram_token"] = self.telegram_token
        if self.telegram_chat_id:
            payload["telegram_chat_id"] = self.telegram_chat_id
        
        try:
            response = requests.post(
                f"{self.backend_url}/api/generate",
                json=payload,
                timeout=30
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_status(self, job_id: str) -> Dict:
        """Get job status"""
        try:
            response = requests.get(
                f"{self.backend_url}/api/status/{job_id}",
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def wait_for_completion(self, job_id: str, timeout: int = 300, 
                           check_interval: int = 5) -> Optional[Dict]:
        """Wait until job completes or timeout"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            result = self.get_status(job_id)
            
            if not result.get('success'):
                print(f"[ERROR] Failed to get status: {result.get('error')}")
                return None
            
            job = result.get('job', {})
            status = job.get('status')
            
            if status == 'completed':
                return job
            elif status in ('failed', 'error'):
                print(f"[ERROR] Job failed: {job.get('error')}")
                return None
            
            time.sleep(check_interval)
        
        print(f"[TIMEOUT] Job {job_id} exceeded {timeout}s timeout")
        return None
    
    def batch_generate(self, prompts: List[str], model: str = "nano-banana-pro",
                      wait: bool = True) -> List[Dict]:
        """Generate multiple images"""
        jobs = []
        
        print(f"[BATCH] Submitting {len(prompts)} generation requests...")
        
        for i, prompt in enumerate(prompts, 1):
            print(f"[{i}/{len(prompts)}] Submitting: {prompt[:50]}...")
            
            result = self.generate(prompt, model=model)
            
            if result.get('success'):
                jobs.append({
                    'job_id': result['job_id'],
                    'prompt': prompt,
                    'account': result.get('account'),
                    'model': result.get('model'),
                    'status': 'submitted'
                })
                print(f"  ✅ Job ID: {result['job_id']}")
            else:
                print(f"  ❌ Failed: {result.get('error')}")
                jobs.append({
                    'prompt': prompt,
                    'status': 'failed',
                    'error': result.get('error')
                })
            
            # Small delay to avoid overwhelming backend
            time.sleep(1)
        
        if not wait:
            return jobs
        
        # Wait for all jobs to complete
        print(f"\n[BATCH] Waiting for {len(jobs)} jobs to complete...")
        
        results = []
        for i, job in enumerate(jobs, 1):
            if job.get('status') == 'failed':
                results.append(job)
                continue
            
            job_id = job['job_id']
            prompt = job['prompt']
            
            print(f"[{i}/{len(jobs)}] Waiting for: {prompt[:50]}...")
            
            completed = self.wait_for_completion(job_id)
            
            if completed:
                job['status'] = 'completed'
                job['task_uuid'] = completed.get('task_uuid')
                job['completed_at'] = completed.get('completed_at')
                print(f"  ✅ Completed")
            else:
                job['status'] = 'failed'
                print(f"  ❌ Failed")
            
            results.append(job)
        
        return results


class HermesAgent:
    """
    Example Hermes Agent implementation
    
    Workflow:
    1. Generate content ideas
    2. Create prompts
    3. Submit to V2Fun Backend
    4. Wait for results
    5. Report to Telegram
    """
    
    def __init__(self, v2fun_client: V2FunBackendClient):
        self.v2fun = v2fun_client
    
    def generate_ideas(self, topic: str, count: int = 5) -> List[str]:
        """
        Generate content ideas based on topic
        (This would use actual Hermes AI logic)
        """
        # Placeholder - implement actual idea generation
        ideas = [
            f"{topic} concept {i+1}"
            for i in range(count)
        ]
        return ideas
    
    def create_prompt(self, idea: str) -> str:
        """
        Convert idea to detailed prompt
        (This would use actual prompt engineering)
        """
        # Placeholder - implement actual prompt creation
        prompt = f"A stunning visual representation of {idea}, highly detailed, professional photography, 8k resolution"
        return prompt
    
    def process_topic(self, topic: str, count: int = 5) -> Dict:
        """
        Complete workflow: topic -> ideas -> prompts -> images
        """
        print("="*80)
        print(f"HERMES AGENT - Processing Topic: {topic}")
        print("="*80)
        
        # Step 1: Check backend health
        print("\n[STEP 1] Checking backend health...")
        health = self.v2fun.health_check()
        if health.get('status') != 'healthy':
            print(f"❌ Backend unhealthy: {health}")
            return {"success": False, "error": "Backend unhealthy"}
        print(f"✅ Backend healthy: {health.get('accounts_available')} accounts available")
        
        # Step 2: Generate ideas
        print(f"\n[STEP 2] Generating {count} content ideas...")
        ideas = self.generate_ideas(topic, count)
        for i, idea in enumerate(ideas, 1):
            print(f"  {i}. {idea}")
        
        # Step 3: Create prompts
        print(f"\n[STEP 3] Creating prompts...")
        prompts = []
        for idea in ideas:
            prompt = self.create_prompt(idea)
            prompts.append(prompt)
            print(f"  - {prompt[:60]}...")
        
        # Step 4: Generate images
        print(f"\n[STEP 4] Submitting to V2Fun Backend...")
        results = self.v2fun.batch_generate(prompts, wait=True)
        
        # Step 5: Summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        
        successful = len([r for r in results if r.get('status') == 'completed'])
        failed = len(results) - successful
        
        print(f"Total: {len(results)}")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        
        if successful > 0:
            print("\nCompleted Jobs:")
            for r in results:
                if r.get('status') == 'completed':
                    print(f"  - Job ID: {r['job_id']}")
                    print(f"    Prompt: {r['prompt'][:50]}...")
                    print(f"    Task UUID: {r.get('task_uuid')}")
                    print(f"    Account: {r.get('account')}")
                    print()
        
        return {
            "success": True,
            "topic": topic,
            "total": len(results),
            "successful": successful,
            "failed": failed,
            "results": results
        }


def example_simple_generation():
    """Example 1: Simple single generation"""
    print("="*80)
    print("EXAMPLE 1: Simple Generation")
    print("="*80)
    
    client = V2FunBackendClient()
    
    # Submit request
    result = client.generate("a beautiful sunset over mountains")
    
    if result.get('success'):
        job_id = result['job_id']
        print(f"✅ Job submitted: {job_id}")
        
        # Wait for completion
        completed = client.wait_for_completion(job_id)
        
        if completed:
            print(f"✅ Generation completed!")
            print(f"   Task UUID: {completed.get('task_uuid')}")
        else:
            print(f"❌ Generation failed")
    else:
        print(f"❌ Submission failed: {result.get('error')}")


def example_batch_generation():
    """Example 2: Batch generation"""
    print("="*80)
    print("EXAMPLE 2: Batch Generation")
    print("="*80)
    
    client = V2FunBackendClient()
    
    prompts = [
        "a red sports car in a city street",
        "a cute cat playing with a ball of yarn",
        "a modern minimalist house with garden",
        "a futuristic robot in a sci-fi setting",
        "a peaceful zen garden with koi fish"
    ]
    
    results = client.batch_generate(prompts, wait=True)
    
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    
    for i, result in enumerate(results, 1):
        status_icon = "✅" if result.get('status') == 'completed' else "❌"
        print(f"{status_icon} {i}. {result['prompt'][:50]}...")
        if result.get('task_uuid'):
            print(f"   Task UUID: {result['task_uuid']}")


def example_hermes_workflow():
    """Example 3: Complete Hermes workflow"""
    print("="*80)
    print("EXAMPLE 3: Hermes Agent Workflow")
    print("="*80)
    
    # Initialize
    client = V2FunBackendClient(
        telegram_token=None,  # Set your token
        telegram_chat_id=None  # Set your chat ID
    )
    
    hermes = HermesAgent(client)
    
    # Process topic
    result = hermes.process_topic("cyberpunk city", count=3)
    
    if result.get('success'):
        print("\n✅ Workflow completed successfully!")
    else:
        print(f"\n❌ Workflow failed: {result.get('error')}")


def example_with_different_models():
    """Example 4: Using different models"""
    print("="*80)
    print("EXAMPLE 4: Different Models")
    print("="*80)
    
    client = V2FunBackendClient()
    
    models = [
        "nano-banana-pro",
        "gpt-image-2",
        "nano-banana-2",
        "qwen-edit"
    ]
    
    prompt = "a beautiful landscape"
    
    jobs = []
    for model in models:
        print(f"\nSubmitting with model: {model}")
        result = client.generate(prompt, model=model)
        
        if result.get('success'):
            jobs.append({
                'job_id': result['job_id'],
                'model': model
            })
            print(f"  ✅ Job ID: {result['job_id']}")
        else:
            print(f"  ❌ Failed: {result.get('error')}")
    
    # Wait for all
    print("\nWaiting for all jobs...")
    for job in jobs:
        completed = client.wait_for_completion(job['job_id'])
        if completed:
            print(f"✅ {job['model']}: Completed")
        else:
            print(f"❌ {job['model']}: Failed")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python hermes_integration_example.py simple")
        print("  python hermes_integration_example.py batch")
        print("  python hermes_integration_example.py hermes")
        print("  python hermes_integration_example.py models")
        sys.exit(1)
    
    mode = sys.argv[1].lower()
    
    if mode == "simple":
        example_simple_generation()
    elif mode == "batch":
        example_batch_generation()
    elif mode == "hermes":
        example_hermes_workflow()
    elif mode == "models":
        example_with_different_models()
    else:
        print(f"Unknown mode: {mode}")
