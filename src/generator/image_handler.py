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
    
    def generate_and_upload_image(self, prompt, topic):
        """
        Note: Untuk generate image dengan Gemini, lo butuh model vision.
        Sementara ini kita pake unsplash API atau placeholder.
        """
        # Kalo lo punya akses ke image generation model, panggil disini
        # Sementara kita pake unsplash API
        
        unsplash_url = f"https://source.unsplash.com/featured/?{topic.replace(' ', ',')},travel"
        
        # Download image
        response = requests.get(unsplash_url)
        img = Image.open(BytesIO(response.content))
        
        # Save temporary
        temp_path = f"/tmp/{topic.replace(' ', '_')}.jpg"
        img.save(temp_path)
        
        # Upload to cloudinary
        upload_result = cloudinary.uploader.upload(temp_path)
        
        # Cleanup
        os.remove(temp_path)
        
        return upload_result['secure_url']
    
    def upload_local_image(self, image_path):
        upload_result = cloudinary.uploader.upload(image_path)
        return upload_result['secure_url']