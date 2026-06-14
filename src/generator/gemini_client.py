import google.generativeai as genai
import os
import time
import re
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
        """Generate travel article in HTML format with plain text title"""
        
        prompt = f"""
        Write a travel article about {topic} in ENGLISH with the following requirements:

        ====== TITLE ======
        Create a plain text title (max 60 characters). NO "Title:" prefix, just the title text.
        
        ====== CONTENT FORMAT (MUST BE VALID HTML) ======
        
        Format the article using this HTML structure:
        
        1. Opening paragraph in <p> tags
        2. Section headers using <h2>
        3. Bullet points using <ul> and <li> for key attractions
        4. Use <strong> for important text, <em> for emphasis
        5. Travel tips as checklist using ✅ (unicode) inside <p> with <br> line breaks
        6. Closing paragraph in <p>
        
        Example of how your response should look:
        
        [Plain text title here without any prefix]
        
        <p>Opening paragraph about the destination...</p>
        
        <h2>Top Attractions in {topic}</h2>
        <ul>
          <li><strong>Attraction 1</strong> - Brief description</li>
          <li><strong>Attraction 2</strong> - Brief description</li>
        </ul>
        
        <h2>Travel Tips</h2>
        <p>✅ Best time to visit: Month to Month<br>
        ✅ Getting around: Transportation tips<br>
        ✅ Local customs: Important etiquette</p>
        
        <h2>Conclusion</h2>
        <p>Final thoughts and encouragement to visit...</p>
        
        IMPORTANT RULES:
        - Title must be plain text on its own line, NO HTML tags
        - Title NO "Title:" prefix, just the actual title
        - Content must be valid HTML
        - Use natural, engaging, SEO-friendly English
        - NO markdown, NO code blocks
        """
        
        if keywords:
            prompt += f"\n\nInclude these keywords naturally in the content: {', '.join(keywords)}"
        
        # Retry logic
        for attempt in range(self.max_retries):
            try:
                print(f"  🔄 Generating article (attempt {attempt + 1}/{self.max_retries})...")
                
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
                        raise Exception(f"Timeout after {self.max_retries} attempts")
                else:
                    raise e
        
        raise Exception("Unexpected error in generate_article")
    
    def generate_image_prompt(self, topic):
        """Generate prompt for image search"""
        
        prompt = f"""
        Create a short image search query (max 50 words) for a travel photo about: {topic}
        
        The query should be in English.
        Output ONLY the query, no explanations.
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
        
        return f"Beautiful travel photography of {topic}"
    
    def _parse_response(self, raw_text):
        """Parse Gemini response: extract plain text title + HTML content"""
        
        lines = raw_text.strip().split('\n')
        
        # Extract title (first non-empty line that doesn't look like HTML)
        title = ""
        for line in lines:
            clean_line = line.strip()
            if clean_line and not clean_line.startswith('<'):
                # Check if it contains any prohibited prefixes
                if not clean_line.lower().startswith(('title:', 'heading:', 'header:')):
                    title = clean_line
                    break
        
        # Fallback title if none found
        if not title:
            # Try to extract from first text before any HTML
            for line in lines:
                if line.strip() and '<' not in line:
                    title = line.strip()
                    break
        
        # Final fallback
        if not title:
            title = "Travel Guide"
        
        # Limit title to 60 characters
        title = title[:60]
        
        # Extract content: everything after the title line
        content_lines = []
        found_title = False
        
        for line in lines:
            if not found_title:
                # Skip until we pass the title line
                if line.strip() == title or (title in line and len(line) < 100):
                    found_title = True
                continue
            else:
                content_lines.append(line)
        
        content = '\n'.join(content_lines).strip()
        
        # If content is empty, use original text but remove title
        if not content:
            content = raw_text.replace(title, '', 1).strip()
        
        # Ensure content has HTML (wrap plain text in <p> if needed)
        if content and not content.startswith('<'):
            content = f"<p>{content}</p>"
        
        return {
            'title': title,
            'content': content,
            'raw_text': raw_text
        }
