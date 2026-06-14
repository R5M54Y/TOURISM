#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.generator.gemini_client import GeminiClient
from src.generator.image_handler import ImageHandler
from src.sheets.google_sheets import GoogleSheetsManager
from src.publishers.blogger import BloggerPublisher
from src.publishers.medium import MediumPublisher
import json
import time

def main():
    print("🚀 Starting Travel Article Generator...")
    
    # Initialize components
    gemini = GeminiClient()
    images = ImageHandler()
    sheets = GoogleSheetsManager()
    blogger = BloggerPublisher()
    medium = MediumPublisher()
    
    # Topics list (lo bisa ambil dari spreadsheet atau file config)
    topics = [
        "Pantai Kuta Bali",
        "Candi Borobudur Magelang",
        "Danau Toba Sumatera Utara",
        "Raja Ampat Papua",
        "Gunung Bromo Jawa Timur"
    ]
    
    for topic in topics:
        print(f"\n📝 Generating article about: {topic}")
        
        try:
            # 1. Generate article with Gemini
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
                'keywords': topic.split()
            }
            row_id = sheets.add_article(article_data)
            print(f"✓ Saved to Google Sheets (Row {row_id})")
            
            # 4. Post to Blogger
            blogger_result = blogger.publish(
                article['title'],
                article['content'],
                image_url
            )
            if blogger_result['success']:
                print(f"✓ Posted to Blogger: {blogger_result['url']}")
            else:
                print(f"✗ Blogger failed: {blogger_result['error']}")
            
            # 5. Post to Medium
            medium_result = medium.publish(
                article['title'],
                article['content'],
                image_url
            )
            if medium_result['success']:
                print(f"✓ Posted to Medium: {medium_result['url']}")
            else:
                print(f"✗ Medium failed: {medium_result['error']}")
            
            # Update status di sheets
            sheets.update_status(row_id, 'completed')
            
            # Delay to avoid rate limiting
            time.sleep(5)
            
        except Exception as e:
            print(f"❌ Error processing {topic}: {str(e)}")
            sheets.update_status(row_id, 'failed')
            continue
    
    print("\n✅ All done!")

if __name__ == "__main__":
    main()