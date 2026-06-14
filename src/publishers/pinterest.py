import os
import requests
from dotenv import load_dotenv

load_dotenv()

class PinterestPublisher:
    def __init__(self):
        self.access_token = os.getenv('PINTEREST_ACCESS_TOKEN')
        self.board_id = os.getenv('PINTEREST_BOARD_ID')
        self.base_url = "https://api.pinterest.com/v5"
    
    def strip_html(self, html_text):
        """Remove HTML tags for Pinterest description"""
        import re
        clean = re.compile('<.*?>')
        text_without_tags = re.sub(clean, '', html_text)
        # Clean up extra whitespace
        return ' '.join(text_without_tags.split())[:500]  # Max 500 chars
    
    def publish(self, title, content, image_url, topic):
        """Post to Pinterest"""
        
        # Convert HTML to plain text for Pinterest
        plain_description = self.strip_html(content)
        
        # Short description for pin
        description = f"{plain_description[:450]}...\n\nCheck out this amazing travel destination!"
        
        payload = {
            "title": title[:100],  # Max 100 chars
            "description": description[:500],  # Max 500 chars
            "link": image_url,
            "board_id": self.board_id,
            "media_source": {
                "source_type": "image_url",
                "url": image_url
            }
        }
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/pins",
                json=payload,
                headers=headers
            )
            
            if response.status_code == 201:
                data = response.json()
                return {'success': True, 'url': data.get('link', data.get('id'))}
            else:
                error_detail = response.text
                # Cek apakah trial access error
                if "trial" in error_detail.lower():
                    return {'success': False, 'error': "Trial access - perlu upgrade ke Standard Access"}
                return {'success': False, 'error': error_detail}
        except Exception as e:
            return {'success': False, 'error': str(e)}
