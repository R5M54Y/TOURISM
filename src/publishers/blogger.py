import requests
import os
from dotenv import load_dotenv

load_dotenv()

class BloggerPublisher:
    def __init__(self):
        self.api_key = os.getenv('BLOGGER_API_KEY')
        self.blog_id = os.getenv('BLOGGER_BLOG_ID')
        self.base_url = f"https://www.googleapis.com/blogger/v3/blogs/{self.blog_id}/posts"
    
    def publish(self, title, content, image_url=None):
        # Format HTML content with image
        html_content = f"<div class='article-content'>"
        
        if image_url:
            html_content += f"<img src='{image_url}' alt='{title}' style='width:100%; margin-bottom:20px;'/>"
        
        html_content += f"<h1>{title}</h1>"
        html_content += content
        html_content += "</div>"
        
        payload = {
            "title": title,
            "content": html_content,
            "labels": ["travel", "wisata", "auto-generated"]
        }
        
        headers = {
            "Authorization": f"Bearer {self._get_access_token()}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            self.base_url,
            json=payload,
            headers=headers
        )
        
        if response.status_code == 200:
            return {"success": True, "url": response.json().get('url')}
        else:
            return {"success": False, "error": response.text}
    
    def _get_access_token(self):
        # Lo butuh OAuth2 untuk Blogger
        # Sementara ini dummy, lo bisa implement dengan google-auth
        return os.getenv('BLOGGER_ACCESS_TOKEN')