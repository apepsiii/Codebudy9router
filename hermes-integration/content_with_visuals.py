#!/usr/bin/env python3
"""
Integration: Content Ideation + UGC Visual Generator
Generate content ideas with visual assets (photos/storyboards)
"""

import sys
sys.path.insert(0, '/home/ubuntu')

from content_ideation import ContentIdeationAgent
from ugc_generator_client import UGCGeneratorClient
from affiliate_helper import AffiliateTracker
import json
from typing import Dict, List, Optional

class ContentWithVisuals:
    """
    Enhanced content ideation with visual asset generation
    """
    
    def __init__(
        self, 
        ugc_api_url: Optional[str] = None,
        ugc_api_key: Optional[str] = None
    ):
        self.idea_agent = ContentIdeationAgent()
        self.ugc_client = None
        
        if ugc_api_url and ugc_api_key:
            self.ugc_client = UGCGeneratorClient(ugc_api_url, ugc_api_key)
    
    def generate_with_visuals(
        self,
        product_info: str,
        product_name: str,
        generate_visuals: bool = False
    ) -> List[Dict]:
        """
        Generate content ideas with optional visual assets
        
        Args:
            product_info: Raw product information
            product_name: Product name
            generate_visuals: Whether to generate visual assets
        
        Returns:
            List of content ideas with visual assets
        """
        print("🤔 Analyzing product...")
        analysis = self.idea_agent.analyze_product(product_info)
        
        print(f"📊 Category: {analysis['category']}")
        print(f"🎯 Target: {', '.join(analysis['target_audience'])}")
        
        print("\n💡 Generating content ideas...")
        ideas = self.idea_agent.generate_content_ideas(product_name, analysis)
        
        print(f"✅ Generated {len(ideas)} content ideas!")
        
        # Generate visuals if enabled and client available
        if generate_visuals and self.ugc_client:
            print("\n🎨 Generating visual assets...")
            ideas = self._add_visual_assets(
                ideas, 
                product_name, 
                analysis['category'],
                product_info[:200]
            )
        
        return ideas, analysis
    
    def _add_visual_assets(
        self,
        ideas: List[Dict],
        product_name: str,
        category: str,
        description: str
    ) -> List[Dict]:
        """Add visual assets to content ideas"""
        
        for i, idea in enumerate(ideas):
            print(f"  Generating visuals for idea {i+1}/{len(ideas)}...")
            
            try:
                # Determine visual type based on content type
                if idea['type'] in ['reel', 'video']:
                    # Generate storyboard for video content
                    content_type = f"{idea['platform']}_reel"
                    
                    result = self.ugc_client.generate_video_storyboard(
                        product_name=product_name,
                        content_type=content_type,
                        video_concept=idea['title'][:50],
                        duration_seconds=30 if idea['platform'] == 'tiktok' else 60,
                        num_scenes=5
                    )
                    
                    if result.get('status') == 'success':
                        idea['visual_assets'] = {
                            'type': 'storyboard',
                            'storyboard_id': result.get('storyboard_id'),
                            'scenes': result.get('scenes', [])
                        }
                        print(f"    ✓ Storyboard generated ({len(result.get('scenes', []))} scenes)")
                    else:
                        print(f"    ✗ Storyboard failed: {result.get('message')}")
                
                elif idea['type'] in ['post', 'article']:
                    # Generate single photo for posts/articles
                    scene_type = "flat_lay" if idea['platform'] == 'instagram' else "lifestyle_indoor"
                    
                    result = self.ugc_client.generate_ugc_photo(
                        product_name=product_name,
                        product_category=category,
                        product_description=description,
                        scene_type=scene_type,
                        style="ugc_casual",
                        aspect_ratio="4:5" if idea['platform'] == 'instagram' else "16:9"
                    )
                    
                    if result.get('status') == 'success':
                        idea['visual_assets'] = {
                            'type': 'photo',
                            'images': result.get('images', [])
                        }
                        print(f"    ✓ Photo generated")
                    else:
                        print(f"    ✗ Photo failed: {result.get('message')}")
            
            except Exception as e:
                print(f"    ✗ Error: {str(e)}")
                idea['visual_assets'] = None
        
        return ideas
    
    def save_to_database(
        self,
        product_id: int,
        ideas: List[Dict],
        link_id: Optional[int] = None
    ) -> List[int]:
        """
        Save content ideas with visual assets to database
        
        Args:
            product_id: Product ID
            ideas: List of content ideas with visuals
            link_id: Optional affiliate link ID to associate
        
        Returns:
            List of created content IDs
        """
        print("\n💾 Saving to database...")
        
        content_ids = []
        
        with AffiliateTracker() as tracker:
            for idea in ideas:
                # Map type to valid DB type
                type_mapping = {
                    'video': 'video',
                    'reel': 'reel',
                    'carousel': 'post',
                    'short video': 'reel',
                    'hack': 'reel',
                    'article': 'article',
                    'listicle': 'article',
                    'thread': 'thread',
                    'post': 'post'
                }
                db_type = type_mapping.get(idea['type'], 'post')
                
                # Build description with visual asset info
                description = f"Hook: {idea['hook']}\n\n"
                
                if idea.get('visual_assets'):
                    va = idea['visual_assets']
                    if va['type'] == 'storyboard':
                        description += f"Storyboard ID: {va.get('storyboard_id')}\n"
                        description += f"Scenes: {len(va.get('scenes', []))}\n"
                        for scene in va.get('scenes', [])[:3]:
                            description += f"- {scene.get('description')}\n"
                    elif va['type'] == 'photo':
                        images = va.get('images', [])
                        if images:
                            description += f"Image URL: {images[0].get('url')}\n"
                
                # Save content
                content_id = tracker.add_content(
                    title=idea['title'],
                    content_type=db_type,
                    platform=idea['platform'],
                    description=description,
                    status='draft'
                )
                
                content_ids.append(content_id)
                
                # Link to affiliate link if provided
                if link_id:
                    tracker.link_content_to_link(content_id, link_id, 'description')
                
                print(f"  ✓ #{content_id}: {idea['title'][:50]}...")
        
        return content_ids


def main():
    """CLI interface"""
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║  💡 Content Ideation + UGC Visual Generator                  ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print()
    
    # Check if UGC API is configured
    import os
    ugc_url = os.getenv('UGC_API_URL')
    ugc_key = os.getenv('UGC_API_KEY')
    
    if ugc_url and ugc_key:
        print(f"🎨 UGC API configured: {ugc_url}")
        print()
    else:
        print("⚠️  UGC API not configured (visuals disabled)")
        print("   Set UGC_API_URL and UGC_API_KEY env vars to enable")
        print()
    
    # Interactive mode
    print("📝 Paste raw product info (press Enter twice when done):")
    lines = []
    empty_count = 0
    while True:
        try:
            line = input()
            if line == "":
                empty_count += 1
                if empty_count >= 2:
                    break
            else:
                empty_count = 0
            lines.append(line)
        except EOFError:
            break
    
    product_info = "\n".join(lines).strip()
    
    if not product_info:
        print("❌ No product info provided")
        return
    
    print("\n📦 Product name:")
    product_name = input().strip()
    
    if not product_name:
        print("❌ Product name required")
        return
    
    print()
    
    # Generate content
    generator = ContentWithVisuals(ugc_url, ugc_key)
    
    generate_visuals = False
    if ugc_url and ugc_key:
        print("🎨 Generate visual assets? (y/n): ", end='')
        response = input().strip().lower()
        generate_visuals = response == 'y'
        print()
    
    ideas, analysis = generator.generate_with_visuals(
        product_info,
        product_name,
        generate_visuals=generate_visuals
    )
    
    # Display ideas
    print("\n" + "="*70)
    print("💡 CONTENT IDEAS")
    print("="*70)
    
    grouped = {}
    for idea in ideas:
        platform = idea['platform']
        if platform not in grouped:
            grouped[platform] = []
        grouped[platform].append(idea)
    
    for platform, platform_ideas in grouped.items():
        print(f"\n📱 {platform.upper()} ({len(platform_ideas)} ideas)")
        print("-" * 70)
        for i, idea in enumerate(platform_ideas, 1):
            print(f"\n  {i}. {idea['title']}")
            print(f"     Hook: {idea['hook']}")
            
            if idea.get('visual_assets'):
                va = idea['visual_assets']
                if va['type'] == 'storyboard':
                    print(f"     ✓ Storyboard: {len(va.get('scenes', []))} scenes")
                elif va['type'] == 'photo':
                    print(f"     ✓ Photo generated")
    
    # Save option
    print("\n" + "="*70)
    print("💾 Save to database?")
    print("  1. Yes, create product + save ideas")
    print("  2. Yes, link to existing product")
    print("  3. No, just show ideas")
    print()
    
    choice = input("Choice (1/2/3): ").strip()
    
    if choice == '1':
        print("\n📦 Creating product...")
        print("Price (IDR): ", end='')
        price_str = input().strip()
        price = float(price_str) if price_str else None
        
        print("Commission rate (%): ", end='')
        comm_str = input().strip()
        commission = float(comm_str) if comm_str else None
        
        with AffiliateTracker() as tracker:
            product_id = tracker.add_product(
                name=product_name,
                category=analysis['category'],
                price=price,
                commission_rate=commission,
                description=product_info[:500]
            )
            print(f"✅ Product created! ID: {product_id}")
            
            content_ids = generator.save_to_database(product_id, ideas)
            
            print(f"\n✅ Saved {len(content_ids)} content ideas!")
            print(f"   IDs: {', '.join(f'#{id}' for id in content_ids)}")
    
    elif choice == '2':
        print("\nExisting product ID: ", end='')
        product_id = int(input().strip())
        
        content_ids = generator.save_to_database(product_id, ideas)
        
        print(f"\n✅ Saved {len(content_ids)} content ideas!")
        print(f"   IDs: {', '.join(f'#{id}' for id in content_ids)}")
    
    else:
        print("\n✅ Ideas generated! Not saved to database.")
    
    print("\n🎉 Done!")


if __name__ == '__main__':
    main()
