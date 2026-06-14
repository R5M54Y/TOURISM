class PinterestPublisher:
    def __init__(self):
        self.access_token = os.getenv('PINTEREST_ACCESS_TOKEN')
        self.board_id = os.getenv('PINTEREST_BOARD_ID')
        # PAKE SANDBOX URL
        self.base_url = "https://api-sandbox.pinterest.com/v5"  # ← tambah -sandbox
    
    def publish(self, title, content, image_url, topic):
        description = f"{title[:200]}\n\nCheck out this amazing travel destination!"
        
        payload = {
            "title": title[:100],
            "description": description,
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
        
        response = requests.post(
            f"{self.base_url}/pins",
            json=payload,
            headers=headers
        )
        
        if response.status_code == 201:
            data = response.json()
            return {'success': True, 'url': data.get('link', data.get('id'))}
        else:
            return {'success': False, 'error': response.text}
