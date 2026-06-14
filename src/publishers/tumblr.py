import pytumblr
import os
from dotenv import load_dotenv

load_dotenv()

class TumblrPublisher:
    def __init__(self):
        self.client = pytumblr.TumblrRestClient(
            os.getenv('TUMBLR_CONSUMER_KEY'),
            os.getenv('TUMBLR_CONSUMER_SECRET'),
            os.getenv('TUMBLR_TOKEN'),
            os.getenv('TUMBLR_TOKEN_SECRET')
        )
        self.blog_name = os.getenv('TUMBLR_BLOG_NAME')
    
    def publish(self, title, content, image_url=None):
        # Format HTML content
        html_content = f"<h1>{title}</h1>"
        if image_url:
            html_content += f"<img src='{image_url}' alt='{title}' style='width:100%;'/><br/><br/>"
        html_content += content
        
        result = self.client.create_text(
            self.blog_name,
            title=title,
            body=html_content,
            tags=['travel', 'wanderlust', 'adventure']
        )
        
        if 'id' in result:
            post_url = f"https://{self.blog_name}.tumblr.com/post/{result['id']}"
            return {'success': True, 'url': post_url}
        else:
            return {'success': False, 'error': result}
