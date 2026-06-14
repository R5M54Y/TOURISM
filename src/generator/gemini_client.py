import google.generativeai as genai
import os
import time
from dotenv import load_dotenv

load_dotenv()

class GeminiClient:
    def __init__(self):
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        # Pake Gemini 3.5 Flash - stabil dan cepat
        self.model = genai.GenerativeModel('models/gemini-3.5-flash')
        self.max_retries = 3
        self.retry_delay = 5  # detik
    
    def generate_article(self, topic, keywords=None):
        """Generate travel article with retry logic"""
        
        prompt = f"""
        Write a comprehensive travel article about {topic} in ENGLISH with this exact structure:

        1. **Title:** An engaging, click-worthy title (max 60 characters)
        2. **Introduction:** A compelling opening paragraph (100-150 words) that hooks the reader
        3. **Top Highlights:** 3-5 key attractions or experiences at this destination (each with 1-2 sentences)
        4. **Travel Tips:** Practical advice for visitors (best time to visit, getting around, local customs)
        5. **Conclusion:** A memorable closing paragraph that encourages travel

        Requirements:
        - Use natural, conversational English
        - Include relevant SEO keywords naturally
        - Make it informative and engaging for travelers
        - Avoid markdown formatting, use plain text with line breaks
        """
        
        if keywords:
            prompt += f"\n\nIncorporate these keywords naturally: {', '.join(keywords)}"
        
        # Retry logic for timeout errors
        for attempt in range(self.max_retries):
            try:
                print(f"  🔄 Generating article (attempt {attempt + 1}/{self.max_retries})...")
                
                # Generate with timeout protection
                response = self.model.generate_content(
                    prompt,
                    generation_config={
                        'temperature': 0.7,
                        'top_p': 0.95,
                        'top_k': 40,
                    }
                )
                
                if response and response.text:
                    print(f"  ✅ Article generated successfully")
                    return self._parse_response(response.text)
                else:
                    raise Exception("Empty response from Gemini")
                    
            except Exception as e:
                error_msg = str(e)
                if "504" in error_msg or "Deadline" in error_msg or "timeout" in error_msg.lower():
                    if attempt < self.max_retries - 1:
                        wait_time = self.retry_delay * (attempt + 1)
                        print(f"  ⚠️ Timeout occurred. Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"  ❌ All retries failed for {topic}")
                        raise Exception(f"Timeout after {self.max_retries} attempts: {error_msg}")
                else:
                    # Non-timeout error, raise immediately
                    raise e
        
        raise Exception("Unexpected error in generate_article")
    
    def generate_image_prompt(self, topic):
        """Generate a prompt for image generation"""
        
        prompt = f"""
        Create a detailed image generation prompt for a travel photo about: {topic}
        
        The prompt should be in English and include:
        - Subject: The main landmark or scene
        - Style: Travel photography, vibrant colors, natural lighting
        - Mood: Inspiring, adventurous, beautiful
        - Technical details: High resolution, 4K, cinematic composition
        
        Max 100 words. Output ONLY the prompt, no explanations.
        """
        
        for attempt in range(self.max_retries):
            try:
                response = self.model.generate_content(prompt)
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                raise e
        
        # Fallback prompt if all retries fail
        return f"Beautiful travel photography of {topic}, vibrant colors, golden hour lighting, high resolution, 4K, cinematic"
    
    def _parse_response(self, raw_text):
        """Parse Gemini response into structured format"""
        
        lines = raw_text.strip().split('\n')
        
        # Try to find title (first non-empty line, often has ** or #)
        title = ""
        for line in lines:
            clean_line = line.strip().replace('**', '').replace('#', '').strip()
            if clean_line and len(clean_line) < 80:
                title = clean_line
                break
        
        # If no title found, use first line
        if not title and lines:
            title = lines[0].strip().replace('**', '').replace('#', '').strip()
        
        # Body is everything except the title line
        body_lines = []
        found_title = False
        for line in lines:
            clean_line = line.strip()
            if not found_title and (clean_line.startswith('**') or clean_line.startswith('#') or clean_line == title):
                found_title = True
                continue
            body_lines.append(line)
        
        body = '\n'.join(body_lines).strip()
        
        # Fallback if body is empty
        if not body:
            body = raw_text
        
        return {
            'title': title[:60] if title else f"Travel Guide: {topic[:40]}",  # Max 60 chars
            'content': body,
            'raw_text': raw_text
        }
