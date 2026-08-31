#!/usr/bin/env python3
"""
UGC Generator API Client
Integrates with your backend for generating UGC-style photos and video storyboards
"""

import requests
import json
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
import yaml
import os

@dataclass
class UGCPhoto:
    """Single UGC photo result"""
    url: str
    prompt: str
    seed: int
    width: int
    height: int

@dataclass
class VideoScene:
    """Single scene in video storyboard"""
    scene_number: int
    timestamp: str
    description: str
    image_url: str
    prompt_used: str
    shot_type: str
    text_overlay: Optional[str] = None

@dataclass
class VideoStoryboard:
    """Complete video storyboard"""
    storyboard_id: str
    scenes: List[VideoScene]
    audio_suggestion: Optional[str] = None
    hashtags: List[str] = None


class UGCGeneratorClient:
    """
    Client for UGC content generation API
    
    Usage:
        client = UGCGeneratorClient(api_base_url, api_key)
        photo = client.generate_ugc_photo(...)
        storyboard = client.generate_video_storyboard(...)
    """
    
    def __init__(
        self, 
        api_base_url: str = None, 
        api_key: str = None,
        config_path: str = None
    ):
        """
        Initialize UGC Generator client
        
        Args:
            api_base_url: Base URL of your backend API
            api_key: Your API key for authentication
            config_path: Path to YAML config file (optional)
        """
        if config_path and os.path.exists(config_path):
            config = self._load_config(config_path)
            self.base_url = config.get('api_base_url')
            self.api_key = config.get('api_key')
            self.timeout = config.get('timeout_seconds', 60)
        else:
            self.base_url = api_base_url.rstrip('/') if api_base_url else None
            self.api_key = api_key
            self.timeout = 60
        
        if not self.base_url or not self.api_key:
            raise ValueError("API base URL and API key are required")
        
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'Hermes-UGC-Client/1.0'
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def generate_ugc_photo(
        self,
        product_name: str,
        product_category: str,
        product_description: str,
        scene_type: str = "lifestyle_indoor",
        style: str = "ugc_casual",
        aspect_ratio: str = "1:1",
        num_images: int = 1,
        seed: Optional[int] = None,
        negative_prompt: Optional[str] = None
    ) -> Dict:
        """
        Generate UGC-style product photo
        
        Args:
            product_name: Name of the product
            product_category: Category (Fashion, Electronics, etc)
            product_description: Description of the product
            scene_type: Type of scene (lifestyle_indoor, unboxing, on_feet, flat_lay)
            style: Style of photo (ugc_casual, ugc_professional, influencer_style)
            aspect_ratio: Image aspect ratio (1:1, 9:16, 16:9, 4:5)
            num_images: Number of images to generate (default 1)
            seed: Random seed for reproducibility (optional)
            negative_prompt: Things to avoid in generation (optional)
        
        Returns:
            Dict with status, job_id, images list
        """
        payload = {
            "product_name": product_name,
            "product_category": product_category,
            "product_description": product_description,
            "scene_type": scene_type,
            "style": style,
            "aspect_ratio": aspect_ratio,
            "num_images": num_images
        }
        
        if seed is not None:
            payload['seed'] = seed
        
        if negative_prompt:
            payload['negative_prompt'] = negative_prompt
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/generate-ugc-photo",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "message": f"Request timed out after {self.timeout}s"
            }
        except requests.exceptions.HTTPError as e:
            return {
                "status": "error",
                "message": f"HTTP error: {e.response.status_code}",
                "details": e.response.text
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def generate_video_storyboard(
        self,
        product_name: str,
        content_type: str,
        video_concept: str,
        duration_seconds: int = 30,
        num_scenes: int = 5,
        style: str = "ugc_casual"
    ) -> Dict:
        """
        Generate video storyboard with scene images
        
        Args:
            product_name: Name of the product
            content_type: Platform type (tiktok_reel, instagram_reel, youtube_short)
            video_concept: Concept (POV unboxing, lifestyle_day_in_life, product_review)
            duration_seconds: Total video duration (default 30)
            num_scenes: Number of scenes to generate (default 5)
            style: Visual style (ugc_casual, ugc_professional)
        
        Returns:
            Dict with status, storyboard_id, scenes list
        """
        payload = {
            "product_name": product_name,
            "content_type": content_type,
            "video_concept": video_concept,
            "duration_seconds": duration_seconds,
            "num_scenes": num_scenes,
            "style": style
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/generate-video-storyboard",
                json=payload,
                timeout=self.timeout * 2  # Longer timeout for multiple images
            )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "message": f"Request timed out after {self.timeout * 2}s"
            }
        except requests.exceptions.HTTPError as e:
            return {
                "status": "error",
                "message": f"HTTP error: {e.response.status_code}",
                "details": e.response.text
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def check_job_status(self, job_id: str) -> Dict:
        """
        Check status of async job
        
        Args:
            job_id: Job ID returned from initial request
        
        Returns:
            Dict with status and result (if completed)
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/jobs/{job_id}",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def wait_for_job(
        self, 
        job_id: str, 
        max_wait_seconds: int = 300,
        poll_interval: int = 5
    ) -> Dict:
        """
        Wait for async job to complete
        
        Args:
            job_id: Job ID to wait for
            max_wait_seconds: Maximum time to wait (default 300s)
            poll_interval: Seconds between status checks (default 5s)
        
        Returns:
            Final job result
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait_seconds:
            result = self.check_job_status(job_id)
            
            if result.get('status') in ['success', 'error', 'failed']:
                return result
            
            time.sleep(poll_interval)
        
        return {
            "status": "error",
            "message": f"Job did not complete within {max_wait_seconds}s"
        }
    
    def health_check(self) -> bool:
        """
        Check if API is reachable and authenticated
        
        Returns:
            True if API is healthy, False otherwise
        """
        try:
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False


# Prompt templates for different scene types
PROMPT_TEMPLATES = {
    "lifestyle_indoor": """
A casual, authentic user-generated content style photo of {product_name}.
Scene: Natural home setting, person casually using/wearing the product.
Lighting: Soft natural window light, slightly warm tone.
Angle: Slightly from above, iPhone camera perspective.
Quality: Smartphone photo quality, authentic feel, not professional studio.
Details: Visible texture of {product_description}.
Style: Real person, lived-in space, comfortable atmosphere.
NO watermarks, NO studio lighting, NO commercial feel.
    """,
    
    "unboxing": """
Unboxing moment photo of {product_name}, UGC style.
Scene: Hands opening package on wooden table or bed.
Items: Package, product, maybe phone visible in frame.
Lighting: Natural indoor light, authentic colors.
Angle: Top-down or 45-degree angle, smartphone perspective.
Emotion: Excitement, genuine reaction.
Quality: iPhone/Android camera, real unboxing moment.
NO professional product photography, NO studio setup.
    """,
    
    "on_feet": """
Authentic photo of {product_name} being worn, UGC style.
Scene: Real environment - sidewalk, home, cafe.
Subject: Natural pose, feet/product in focus.
Background: Slightly blurred real-world setting.
Lighting: Natural daylight or indoor ambient.
Angle: Low angle, person taking photo of their own feet/product.
Quality: Smartphone camera, authentic moment.
NO professional model shoot, NO studio background.
    """,
    
    "flat_lay": """
Flat lay arrangement of {product_name}, Instagram UGC style.
Scene: Clean surface - white bed, wooden table, marble counter.
Composition: Product centered, maybe phone/keys/coffee as props.
Lighting: Natural overhead light, soft shadows.
Angle: Directly from above, grid composition.
Colors: Natural, slightly saturated Instagram aesthetic.
Quality: Smartphone photo, planned but not professional.
NO commercial product shot, NO perfect studio lighting.
    """,
    
    "lifestyle_outdoor": """
Outdoor lifestyle photo of {product_name}, UGC style.
Scene: Natural outdoor setting - park, street, beach, city.
Subject: Person naturally interacting with product.
Lighting: Natural daylight, golden hour preferred.
Angle: Eye level or slightly below, smartphone camera.
Background: Real environment, slightly out of focus.
Quality: Smartphone photo, candid authentic moment.
NO posed fashion shoot, NO professional backdrop.
    """,
    
    "review_setup": """
Product review setup photo of {product_name}, UGC style.
Scene: Desk or table with product and review props.
Items: Product, notebook, phone, coffee, natural arrangement.
Lighting: Natural window light from side, soft shadows.
Angle: 45-degree from above, blogger perspective.
Quality: Smartphone or entry camera, intentional composition.
Style: Organized but casual, honest reviewer aesthetic.
NO overly staged, NO commercial advertising look.
    """
}


def build_prompt(
    product_name: str,
    product_description: str,
    scene_type: str
) -> str:
    """
    Build full prompt from template
    
    Args:
        product_name: Name of product
        product_description: Description
        scene_type: Scene type key
    
    Returns:
        Formatted prompt string
    """
    template = PROMPT_TEMPLATES.get(scene_type, PROMPT_TEMPLATES['lifestyle_indoor'])
    return template.format(
        product_name=product_name,
        product_description=product_description
    ).strip()


if __name__ == '__main__':
    # Test the client
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python ugc_generator_client.py <api_url> <api_key>")
        print("Example: python ugc_generator_client.py https://api.example.com sk_test123")
        sys.exit(1)
    
    api_url = sys.argv[1]
    api_key = sys.argv[2]
    
    print("🧪 Testing UGC Generator Client\n")
    
    client = UGCGeneratorClient(api_url, api_key)
    
    # Test health check
    print("1. Health Check...")
    if client.health_check():
        print("   ✅ API is reachable\n")
    else:
        print("   ❌ API is not reachable\n")
        sys.exit(1)
    
    # Test photo generation
    print("2. Testing Photo Generation...")
    result = client.generate_ugc_photo(
        product_name="Sandal Baim Unisex",
        product_category="Fashion",
        product_description="Sandal stylish dari EVA, anti-slip, 10 warna",
        scene_type="lifestyle_indoor",
        style="ugc_casual",
        aspect_ratio="1:1"
    )
    
    if result.get('status') == 'success':
        print(f"   ✅ Photo generated!")
        print(f"   Job ID: {result.get('job_id')}")
        if result.get('images'):
            print(f"   Image URL: {result['images'][0]['url']}")
    else:
        print(f"   ❌ Error: {result.get('message')}")
    
    print("\n✅ Client test complete!")
