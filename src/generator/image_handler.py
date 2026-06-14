import cloudinary.uploader
import cloudinary.api
import requests
from io import BytesIO
from PIL import Image
import os
from dotenv import load_dotenv

load_dotenv()

class ImageHandler:
    def __init__(self):
        cloudinary.config(
            cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
            api_key=os.getenv('CLOUDINARY_API_KEY'),
            api_secret=os.getenv('CLOUDINARY_API_SECRET')
        )
        self.pexels_api_key = os.getenv('PEXELS_API_KEY')
    
    def generate_and_upload_image(self, prompt, topic):
        """Fetch image from Pexels or fallback to Unsplash, then upload to Cloudinary"""
        
        image_url = None
        
        # Try 1: Pexels API (most reliable)
        if self.pexels_api_key:
            try:
                print(f"  📸 Trying Pexels for: {topic}")
                headers = {"Authorization": self.pexels_api_key}
                search_url = f"https://api.pexels.com/v1/search?query={topic}&per_page=1"
                
                response = requests.get(search_url, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('photos') and len(data['photos']) > 0:
                        image_url = data['photos'][0]['src']['large2x']
                        print(f"  ✅ Pexels found image")
            except Exception as e:
                print(f"  ⚠️ Pexels error: {e}")
        
        # Try 2: Unsplash (fallback)
        if not image_url:
            try:
                print(f"  📸 Trying Unsplash for: {topic}")
                unsplash_url = f"https://source.unsplash.com/featured/1200x630/?{topic.replace(' ', ',')},travel"
                response = requests.get(unsplash_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
                
                if response.status_code == 200:
                    img = Image.open(BytesIO(response.content))
                    temp_path = f"/tmp/{topic.replace(' ', '_')}.jpg"
                    img.save(temp_path)
                    
                    upload_result = cloudinary.uploader.upload(temp_path)
                    os.remove(temp_path)
                    image_url = upload_result['secure_url']
                    print(f"  ✅ Unsplash found image")
            except Exception as e:
                print(f"  ⚠️ Unsplash error: {e}")
        
        # Try 3: Placeholder via Cloudinary (last resort)
        if not image_url:
            print(f"  📸 Using Cloudinary placeholder")
            image_url = f"https://res.cloudinary.com/{os.getenv('CLOUDINARY_CLOUD_NAME')}/image/upload/w_1200,h_630,c_fill/v1/travel/{topic.replace(' ', '_')}"
        
        return image_url
    
    def upload_local_image(self, image_path):
        upload_result = cloudinary.uploader.upload(image_path)
        return upload_result['secure_url']
