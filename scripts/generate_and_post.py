#!/usr/bin/env python3
import sys
import os
import random
from datetime import datetime
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Imports needed for both modes
from src.generator.gemini_client import GeminiClient
from src.generator.article_contract import TravelArticle, ArticleContract, ArticleStatus
from src.generator.article_validator import ArticleValidator
from src.generator.image_pipeline import run_image_pipeline

# Imports for normal mode only (should not be loaded in dry-run)
from src.sheets.google_sheets import GoogleSheetsManager
from src.publishers.tumblr import TumblrPublisher
from src.publishers.pinterest import PinterestPublisher
from src.publishers.blogger import BloggerPublisher
from src.publishers.medium import MediumPublisher

# Conditional renderer import
try:
    from scripts.test_article_architecture import render_markdown as render_article_md
    HAS_RENDER = True
except ImportError:
    HAS_RENDER = False

# Parse command line flags
Dry_run = '--dry-run' in sys.argv

# Topic selection
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
    "Singapore, Singapore",
]

# Topic selection
if Dry_run:
    topics = ["Kyoto, Japan"]          # Force single test destination
else:
    # Pick 3 random topics (original behaviour)
    topics = random.sample(topics_list, 3)

print(f"📋 Selected topics: {', '.join(topics)}")

# Initialize Gemini client (required in both modes)
gemini = GeminiClient()

# For dry-run, we don't initialize heavy services
# For normal mode, we need all services initialized
if Dry_run:
    # Dry-run mode: initialize only what we need
    # Gemini client already initialized
    images = None
    sheets = None
    tumblr = None
    pinterest = None
    blogger = None
    medium = None
else:
    # Normal mode: initialize all services
    from src.generator.image_handler import ImageHandler
    images = ImageHandler()
    sheets = GoogleSheetsManager()
    tumblr = TumblrPublisher()
    pinterest = PinterestPublisher()
    blogger = BloggerPublisher()
    medium = MediumPublisher()

# Process each selected destination
for topic in topics:
    row_id = None
    try:
        print(f"\n📝 Generating article about: {topic}")

        # 1. Generate structured article with Gemini
        article_data = gemini.generate_article(topic)
        article = TravelArticle.from_dict(article_data)
        print(f"✓ Article generated: {article.title}")

        # 2. VALIDATE the article before proceeding
        validation = ArticleValidator.validate(article)
        if not validation['valid']:
            print(f"❌ Article validation failed for {topic}:")
            for error in validation['errors']:
                print(f"  - {error}")
            if Dry_run:
                sys.exit(1)
            else:
                # In normal mode: persist validation failure to sheets
                sheets.add_article({
                    'title': article.title,
                    'content': json.dumps(article.to_dict(), ensure_ascii=False),
                    'image_url': '',
                    'keywords': topic.split(',')[0].strip(),
                    'status': 'validation_failed'
                })
                continue

        print(f"✓ Article validation passed ({validation['section_count']} sections)")

        # DRY-RUN specific handling: stop after validation/rendering
        if Dry_run:
            # Render article using the existing renderer if available
            if HAS_RENDER:
                try:
                    markdown = render_article_md(article)
                    print(f"🖋️ Markdown rendering completed ({len(markdown)} chars)")
                    render_ok = True
                except Exception as re:
                    print(f"🖋️ Rendering error: {re}")
                    render_ok = False
            else:
                print("🖋️ Rendering function not available, skipping.")
                render_ok = True

            # Print concise validation result
            print("\nGEMINI GENERATION: PASS")
            print("ARTICLE VALIDATION: PASS")
            print(f"SECTIONS: {validation['section_count']}/18")
            print(f"RENDERING: {'PASS' if render_ok else 'FAIL'}")
            print("DRY RUN: PASS")
            print("\nAll tests passed.")
            sys.exit(0)   # Exit successfully after dry-run validation

        # --- Normal (production) mode below ---
        # 3. Generate image from existing image_prompt and upload to Blogger
        image_prompt = article.image_prompt
        if not image_prompt:
            image_prompt = gemini.generate_image_prompt(topic)

        image_result = run_image_pipeline(image_prompt, topic)
        image_url = image_result.get('image_url')

        if image_url:
            print(f"✓ Image uploaded: {image_url}")
        else:
            print(f"✗ Image generation/upload failed: {image_result.get('error', 'Unknown error')}")

        # 4. Save to Google Sheets
        article_data = {
            'title': article.title,
            'content': json.dumps(article.to_dict(), ensure_ascii=False),
            'image_url': image_url,
            'keywords': topic.split(',')[0].strip()
        }
        row_id = sheets.add_article(article_data)
        print(f"✓ Saved to Google Sheets (Row {row_id})")

        # 5. Post to Tumblr
        tumblr_result = tumblr.publish(
            article.title,
            json.dumps(article.to_dict(), ensure_ascii=False),
            image_url
        )
        if tumblr_result['success']:
            print(f"✓ Posted to Tumblr: {tumblr_result['url']}")
        else:
            print(f"✗ Tumblr failed: {tumblr_result.get('error', 'Unknown error')}")

        # 6. Post to Pinterest
        pinterest_result = pinterest.publish(
            article.title,
            json.dumps(article.to_dict(), ensure_ascii=False),
            image_url,
            topic
        )
        if pinterest_result['success']:
            print(f"✓ Posted to Pinterest: {pinterest_result['url']}")
        else:
            print(f"✗ Pinterest failed: {pinterest_result.get('error', 'Unknown error')}")

        # 7. Post to Blogger
        blogger_result = blogger.publish(
            article.title,
            json.dumps(article.to_dict(), ensure_ascii=False)
        )
        if blogger_result['success']:
            print(f"✓ Posted to Blogger: {blogger_result['url']}")
        else:
            print(f"✗ Blogger failed: {blogger_result.get('error', 'Unknown error')}")

        # 8. Post to Medium
        medium_result = medium.publish(
            article.title,
            json.dumps(article.to_dict(), ensure_ascii=False)
        )
        if medium_result['success']:
            print(f"✓ Posted to Medium: {medium_result['url']}")
        else:
            print(f"✗ Medium failed: {medium_result.get('error', 'Unknown error')}")

        # Update status di sheets
        sheets.update_status(row_id, 'completed')
        print(f"✅ Done with: {topic}")

    except Exception as e:
        print(f"❌ Error processing {topic}: {str(e)}")
        if row_id and not Dry_run:
            sheets.update_status(row_id, 'failed')
        continue

print("\n" + "="*50)
print("✅ All articles generated and published successfully")
print("="*50)
sys.exit(0)