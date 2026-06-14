import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

class GeminiClient:
    def __init__(self):
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        # PAKE MODEL GEMINI 3.5 FLASH - Paling OK buat artikel
        self.model = genai.GenerativeModel('models/gemini-3.5-flash')
    
    def generate_article(self, topic, keywords=None):
        prompt = f"""
        Write a travel article about {topic} in ENGLISH with this structure:
        
        1. Engaging title (max 60 characters)
        2. Opening paragraph (100-150 words)
        3. 3-5 key highlights of the destination
        4. Travel tips
        5. Conclusion
        
        Use natural, engaging, and SEO-friendly English.
        """
        
        if keywords:
            prompt += f"\nInclude these keywords: {', '.join(keywords)}"
        
        response = self.model.generate_content(prompt)
        return self._parse_response(response.text)
    
    def generate_image_prompt(self, topic):
        prompt = f"""
        Create an image generation prompt (in English) for: {topic}
        Style: travel photography, vibrant colors, cinematic lighting, high resolution.
        Max 100 words.
        """
        
        response = self.model.generate_content(prompt)
        return response.text
    
    def _parse_response(self, raw_text):
        lines = raw_text.strip().split('\n')
        
        title = lines[0].replace('#', '').strip()
        body = '\n'.join(lines[1:])
        
        return {
            'title': title,
            'content': body,
            'raw_text': raw_text
        }
