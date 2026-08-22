#!/usr/bin/env python3
"""
image_worker.py
Minimal standalone worker to populate image_url for articles
that have an image_prompt but no image_url yet.

Idempotent: skips rows where image_url is already set.
Bounded retry: Gemini 429/5xx handled via existing retry logic.
Does NOT publish or modify article content beyond image_url.
"""

import sys
import os
sys.path.insert(0, '/d/tourism')

# ---- dependencies -----------------------------------------------------------
from src.sheets.google_sheets import GoogleSheetsManager
from src.generator.image_pipeline.gemini_image_generator import generate_image_from_prompt
from src.generator.image_pipeline.blogger_image_uploader import upload_image_to_blogger

# ---- entry point ------------------------------------------------------------
def processMissingImages():
    """
    Entry point callable from Apps Script time-driven triggers.
    Processes the first eligible article found.
    """
    print("[worker] Starting image_url population worker")
    
    # 1. Open Sheets manager
    sheets = GoogleSheetsManager()
    
    # 2. Fetch pending articles (status == 'pending')
    pending_rows = sheets.get_pending_articles(limit=10)
    
    processed_any = False
    
    for row in pending_rows:
        article_id = row['id']
        title = row['title']
        image_prompt = row.get('image_prompt', '').strip()
        image_url = row.get('image_url', '').strip()
        
        print(f"[worker] Examining article '{title}' (ID: {article_id})")
        print(f"[worker] image_prompt present: {bool(image_prompt)}")
        print(f"[worker] image_url empty: {not image_url}")
        
        # ---- eligibility check ------------------------------------------------
        if not image_prompt:
            print(f"[worker] SKIP: image_prompt empty")
            continue
        if image_url:
            print(f"[worker] SKIP: image_url already set")
            continue
            
        # ---- 1. Generate image from Gemini ------------------------------------
        try:
            print("[worker] Generating image via Gemini...")
            image_bytes = generate_image_from_prompt(image_prompt)
        except Exception as e:
            print(f"[worker] Gemini generation failed: {e}")
            continue  # skip to next article
        
        # ---- 2. Upload to Blogger ---------------------------------------------
        try:
            print("[worker] Uploading image to Blogger...")
            blogger_url = upload_image_to_blogger(image_bytes, filename='hero_image.png')
        except Exception as e:
            print(f"[worker] Blogger upload failed: {e}")
            continue
        
        if not blogger_url:
            print("[worker] SKIP: No image URL returned from Blogger")
            continue
        
        # ---- 3. Write image_url back to sheet ---------------------------------
        try:
            print(f"[worker] Writing image_url to row {row['row_id']}")
            sheets.set_image_url(row['row_id'], blogger_url)
            print(f"[worker] SUCCESS: {title} -> {blogger_url}")
            processed_any = True
        except Exception as e:
            print(f"[worker] FAILED to write image_url: {e}")
            continue
        
        # After processing one article, stop – idempotent & bounded work
        break
    
    if not processed_any:
        print("[worker] No eligible articles found – exiting")
    
    print("[worker] Finished")
    return processed_any


# Allow direct execution for testing
if __name__ == "__main__":
    processMissingImages()