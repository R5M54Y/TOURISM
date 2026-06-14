import requests
import os
from dotenv import load_dotenv

load_dotenv()

class MediumPublisher:
    def __init__(self):
        self.token = os.getenv('MEDIUM_TOKEN')
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Get user ID
        user_response = requests.get(
            "https://api.medium.com/v1/me",
            headers=self.headers
        )
        self.user_id = user_response.json().get('data', {}).get('id')
    
    def publish(self, title, content, image_url=None):
        # Medium pake format markdown
        markdown_content = f"![{title}]({image_url})\n\n{content}" if image_url else content
        
        payload = {
            "title": title,
            "contentFormat": "markdown",
            "content": markdown_content,
            "tags": ["travel", "wisata", "indonesia"],
            "publishStatus": "public"
        }
        
        response = requests.post(
            f"https://api.medium.com/v1/users/{self.user_id}/posts",
            json=payload,
            headers=self.headers
        )
        
        if response.status_code == 201:
            return {"success": True, "url": response.json().get('data', {}).get('url')}
        else:
            return {"success": False, "error": response.text}