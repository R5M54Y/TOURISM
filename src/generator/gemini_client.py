import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

class GeminiClient:
    def __init__(self):
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-pro')
    
    def generate_article(self, topic, keywords=None):
        prompt = f"""
        Buat artikel wisata tentang {topic} dengan struktur:
        
        1. Judul yang menarik (maks 60 karakter)
        2. Paragraf pembuka (100-150 kata)
        3. 3-5 poin penting tentang destinasi
        4. Tips berkunjung
        5. Kesimpulan
        
        Gunakan bahasa Indonesia yang natural dan engaging.
        """
        
        if keywords:
            prompt += f"\nSertakan keywords: {', '.join(keywords)}"
        
        response = self.model.generate_content(prompt)
        return self._parse_response(response.text)
    
    def generate_image_prompt(self, topic):
        prompt = f"""
        Buat prompt untuk AI image generator tentang: {topic}
        Prompt harus dalam bahasa Inggris, deskriptif, style: travel photography, vibrant colors, cinematic lighting.
        Maks 100 kata.
        """
        
        response = self.model.generate_content(prompt)
        return response.text
    
    def _parse_response(self, raw_text):
        # Simple parsing - lo bisa custom sesuai kebutuhan
        lines = raw_text.strip().split('\n')
        
        # Extract title (assuming first line as title)
        title = lines[0].replace('#', '').strip()
        
        # Body is everything else
        body = '\n'.join(lines[1:])
        
        return {
            'title': title,
            'content': body,
            'raw_text': raw_text
        }