"""
V2Fun.ai Image Downloader
Auto-download generated images to local storage
"""

import requests
import os
from pathlib import Path
from datetime import datetime
from typing import Optional


def download_image(image_url: str, generation_id: int, prompt: str = "") -> Optional[str]:
    """
    Download image from V2Fun CDN to local storage
    
    Args:
        image_url: Full URL to the generated image
        generation_id: Database generation ID
        prompt: Optional prompt text for filename
    
    Returns:
        Local file path if successful, None otherwise
    """
    try:
        # Create downloads directory
        download_dir = Path("v2fun_data/results")
        download_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Sanitize prompt for filename (max 50 chars)
        safe_prompt = "".join(c for c in prompt[:50] if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_prompt = safe_prompt.replace(' ', '_')
        
        # Get file extension from URL
        ext = '.jpg'  # default
        if '.' in image_url.split('/')[-1]:
            url_ext = image_url.split('/')[-1].split('.')[-1].lower()
            if url_ext in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
                ext = '.' + url_ext
        
        # Build filename: gen_<id>_<timestamp>_<prompt>.jpg
        if safe_prompt:
            filename = f"gen_{generation_id}_{timestamp}_{safe_prompt}{ext}"
        else:
            filename = f"gen_{generation_id}_{timestamp}{ext}"
        
        filepath = download_dir / filename
        
        # Download image
        response = requests.get(image_url, timeout=30, stream=True)
        response.raise_for_status()
        
        # Save to file
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Return relative path from project root
        return str(filepath.relative_to(Path.cwd()))
        
    except Exception as e:
        print(f"Failed to download image {image_url}: {e}")
        return None


def get_local_image_path(generation_id: int) -> Optional[str]:
    """Get local path for a generation if it exists"""
    download_dir = Path("v2fun_data/results")
    if not download_dir.exists():
        return None
    
    # Search for files matching gen_<id>_*
    pattern = f"gen_{generation_id}_*"
    matches = list(download_dir.glob(pattern))
    
    if matches:
        return str(matches[0].relative_to(Path.cwd()))
    
    return None


def cleanup_old_images(days: int = 30):
    """Delete images older than specified days"""
    from datetime import timedelta
    
    download_dir = Path("v2fun_data/results")
    if not download_dir.exists():
        return 0
    
    cutoff = datetime.now() - timedelta(days=days)
    deleted = 0
    
    for filepath in download_dir.glob("gen_*"):
        if filepath.stat().st_mtime < cutoff.timestamp():
            try:
                filepath.unlink()
                deleted += 1
            except Exception as e:
                print(f"Failed to delete {filepath}: {e}")
    
    return deleted


if __name__ == "__main__":
    # Test download
    test_url = "https://example.com/test.jpg"
    result = download_image(test_url, 123, "test prompt")
    print(f"Downloaded to: {result}")
