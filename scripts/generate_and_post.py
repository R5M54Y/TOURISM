#!/usr/bin/env python3
import sys
import os
import random
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.generator.gemini_client import GeminiClient
from src.generator.image_handler import ImageHandler
from src.sheets.google_sheets import GoogleSheetsManager
from src.publishers.tumblr import TumblrPublisher
from src.publishers.pinterest import PinterestPublisher

def main():
    print("🚀 Starting Travel Article Generator (English)...")
    
    # Initialize components
    gemini = GeminiClient()
    images = ImageHandler()
    sheets = GoogleSheetsManager()
    tumblr = TumblrPublisher()
    pinterest = PinterestPublisher()
    
    # List of international travel topics
    topics_list = [
        "Bali, Indonesia",
        "Santorini, Greece",
        "Machu Picchu, Peru",
        "Kyoto, Japan",
        "Paris, France",
        "Rome, Italy",
        "Bangkok, Thailand",
        "New York City, USA",
        "Cappadocia, Turkey",
        "Banff National Park, Canada",
        "Queenstown, New Zealand",
        "Cape Town, South Africa",
        "Dubai, UAE",
        "London, UK",
        "Barcelona, Spain",
        "Phuket, Thailand",
        "Halong Bay, Vietnam",
        "Siem Reap, Cambodia",
        "Hong Kong, China",
        "Singapore, Singapore"
    ]
    
    # Pick 3 random topics
    topics = random.sample(topics_list, 3)
    print(f"📋 Selected topics: {', '.join(topics)}")
    
    for topic in topics:
        print(f"\n📝 Generating article about: {topic}")
        row_id = None
        
        try:
            # 1. Generate article with Gemini (English)
            article = gemini.generate_article(topic)
            print(f"✓ Article generated: {article['title']}")
            
            # 2. Generate image prompt & get image
            image_prompt = gemini.generate_image_prompt(topic)
            image_url = images.generate_and_upload_image(image_prompt, topic)
            print(f"✓ Image uploaded: {image_url}")
            
            # 3. Save to Google Sheets
            article_data = {
                'title': article['title'],
                'content': article['content'],
                'image_url': image_url,
                'keywords': topic.split(',')[0].strip()
            }
            row_id = sheets.add_article(article_data)
            print(f"✓ Saved to Google Sheets (Row {row_id})")
            
            # 4. Post to Tumblr
            tumblr_result = tumblr.publish(
                article['title'],
                article['content'],
                image_url
            )
            if tumblr_result['success']:
                print(f"✓ Posted to Tumblr: {tumblr_result['url']}")
            else:
                print(f"✗ Tumblr failed: {tumblr_result.get('error', 'Unknown error')}")
            
            # 5. Post to Pinterest
            pinterest_result = pinterest.publish(
                article['title'],
                article['content'],
                image_url,
                topic
            )
            if pinterest_result['success']:
                print(f"✓ Posted to Pinterest: {pinterest_result['url']}")
            else:
                print(f"✗ Pinterest failed: {pinterest_result.get('error', 'Unknown error')}")
            
            # Update status di sheets
            sheets.update_status(row_id, 'completed')
            print(f"✅ Done with: {topic}")
            
        except Exception as e:
            print(f"❌ Error processing {topic}: {str(e)}")
            if row_id:
                sheets.update_status(row_id, 'failed')
            continue
    
    print("\n🎉 All articles generated and published!")

if __name__ == "__main__":
    main()
