import google.generativeai as genai
import os
import time
import re
from datetime import datetime

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
        
        prompt = f"""Write a travel article about {topic} in ENGLISH with the following requirements:

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
        
        prompt = f"""Create a short image search query (max 50 words) for a travel photo about: {topic}
        
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
        """Parse Gemini response: extract structured article data compatible with TravelArticle contract"""
        
        # Split into lines for processing
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
        
        # Initialize article data with all TravelArticle contract fields
        # (no 'content' key - mapped to structured fields instead)
        article_data = {
            'id': self._generate_article_id(),
            'destination': '',
            'country': '',
            'generation_date': datetime.now().isoformat(),
            'version': '1.0',
            'status': 'draft',
            'title': title,
            'introduction': '',
            'quick_facts': None,
            'why_visit': None,
            'best_things_to_do': [],
            'best_places_to_visit': [],
            'best_time_to_visit': '',
            'how_to_get_there': '',
            'getting_around': [],
            'where_to_stay': [],
            'local_food_to_try': [],
            'travel_budget': [],
            'suggested_itinerary': [],
            'local_travel_tips': [],
            'safety_practical_info': None,
            'faq': [],
            'conclusion': '',
            'sources': [],
            'seo': None
        }
        
        # Parse the HTML content to extract structured data
        article_data = self._parse_structured_content('\n'.join(lines), article_data)
        
        return article_data
    
    def _generate_article_id(self):
        """Generate a unique article ID"""
        # Create ID: destination_slug + date + random_suffix
        return "auto_generated_id"
    
    def _parse_structured_content(self, content, article_data):
        """Parse HTML content to extract structured article fields compatible with TravelArticle"""
        
        html_content = content
        
        # --- Extract introduction (first <p> tag content) ---
        intro_match = re.search(r'<p>(.*?)</p>', html_content, re.DOTALL)
        if intro_match:
            intro_text = re.sub(r'<[^>]+>', '', intro_match.group(1)).strip()
            if intro_text and len(intro_text) < 500:
                article_data['introduction'] = intro_text
        
        # --- Extract title if not already found from first line ---
        if not article_data['title'] or article_data['title'] == "Travel Guide":
            # Try to find plain text title (first line not starting with <)
            for line in html_content.split('\n'):
                clean = line.strip()
                if clean and not clean.startswith('<') and not clean.lower().startswith(('title:', 'heading:', 'header:')):
                    candidate = clean[:60]
                    if candidate and len(candidate) > len(article_data['title']):
                        article_data['title'] = candidate
                    break
        
        # --- Extract best_things_to_do from <ul><li><strong> patterns ---
        things_to_do = []
        for match in re.finditer(r'<li><strong>(.*?)</strong>.*?-(.*?)</li>', html_content):
            name = re.sub(r'<[^>]+>', '', match.group(1)).strip()
            desc = re.sub(r'<[^>]+>', '', match.group(2)).strip()
            if name:
                things_to_do.append({'name': name, 'description': desc})
        if things_to_do:
            article_data['best_things_to_do'] = things_to_do
        
        # --- Extract best_places_to_visit from <li> patterns with locations ---
        places = []
        for match in re.finditer(r'<li>(?:<strong>)?(.*?)(?:</strong>)?(?:-|:</strong>)(.*?)</li>', html_content, re.DOTALL):
            name = re.sub(r'<[^>]+>', '', match.group(1)).strip()
            desc = re.sub(r'<[^>]+>', '', match.group(2)).strip()
            if name:
                places.append({'name': name, 'description': desc})
        if places:
            article_data['best_places_to_visit'] = places
        
        # --- Extract why_visit from Travel Tips checklist ---
        why_visit_data = {
            'culture': False, 'history': False, 'nature': False,
            'food': False, 'architecture': False, 'adventure': False,
            'shopping': False, 'nightlife': False, 'family_travel': False, 'relaxation': False
        }
        tips_match = re.search(r'<h2>Travel Tips</h2>.*?(?=<h2>|<h2>Conclusion|$)', html_content, re.DOTALL)
        if tips_match:
            tips_text = tips_match.group(0)
            checklist_items = re.findall(r'✅\s*(.*?)(?:<br|<|$)', tips_text)
            for item in checklist_items:
                item_lower = item.strip().lower()
                if 'culture' in item_lower: why_visit_data['culture'] = True
                if 'history' in item_lower: why_visit_data['history'] = True
                if 'nature' in item_lower: why_visit_data['nature'] = True
                if 'food' in item_lower: why_visit_data['food'] = True
                if 'architecture' in item_lower: why_visit_data['architecture'] = True
                if 'adventure' in item_lower: why_visit_data['adventure'] = True
                if 'shopping' in item_lower: why_visit_data['shopping'] = True
                if 'nightlife' in item_lower: why_visit_data['nightlife'] = True
                if 'family' in item_lower: why_visit_data['family_travel'] = True
                if 'relax' in item_lower or 'leisure' in item_lower: why_visit_data['relaxation'] = True
        article_data['why_visit'] = why_visit_data
        
        # --- Extract best_time_to_visit ---
        bttv_match = re.search(r'<h2>Best Time to Visit</h2>.*?<p>(.*?)</p>', html_content, re.DOTALL)
        if bttv_match:
            text = re.sub(r'<[^>]+>', '', bttv_match.group(1)).strip()
            if text:
                article_data['best_time_to_visit'] = text[:300]
        
        # --- Extract how_to_get_there ---
        hgt_match = re.search(r'<h2>How to Get There</h2>.*?<p>(.*?)</p>', html_content, re.DOTALL)
        if hgt_match:
            text = re.sub(r'<[^>]+>', '', hgt_match.group(1)).strip()
            if text:
                article_data['how_to_get_there'] = text[:400]
        
        # --- Extract getting_around ---
        ga_match = re.search(r'<h2>Getting Around</h2>.*?<p>(.*?)</p>', html_content, re.DOTALL)
        if ga_match:
            text = re.sub(r'<[^>]+>', '', ga_match.group(1)).strip()
            if text:
                article_data['getting_around'] = [{'name': 'Transportation', 'description': text}]
        
        # --- Extract where_to_stay ---
        wt_match = re.search(r'<h2>Where to Stay</h2>.*?<p>(.*?)</p>', html_content, re.DOTALL)
        if wt_match:
            text = re.sub(r'<[^>]+>', '', wt_match.group(1)).strip()
            if text:
                article_data['where_to_stay'] = [{'area': 'General', 'characteristics': text}]
        
        # --- Extract local_food_to_try ---
        lft_match = re.search(r'<h2>Local Food to Try</h2>.*?<p>(.*?)</p>', html_content, re.DOTALL)
        if lft_match:
            text = re.sub(r'<[^>]+>', '', lft_match.group(1)).strip()
            if text:
                article_data['local_food_to_try'] = [{'dish': 'Local specialty', 'description': text}]
        
        # --- Extract travel_budget ---
        tb_match = re.search(r'<h2>Travel Budget</h2>.*?<p>(.*?)</p>', html_content, re.DOTALL)
        if tb_match:
            text = re.sub(r'<[^>]+>', '', tb_match.group(1)).strip()
            if text:
                article_data['travel_budget'] = [{'level': 'Mid-range', 'daily_total': text}]
        
        # --- Extract suggested_itinerary ---
        si_match = re.search(r'<h2>Suggested Itinerary</h2>.*?<p>(.*?)</p>', html_content, re.DOTALL)
        if si_match:
            text = re.sub(r'<[^>]+>', '', si_match.group(1)).strip()
            if text:
                article_data['suggested_itinerary'] = [{'day_flow': text, 'highlights': '', 'practical_notes': ''}]
        
        # --- Extract local_travel_tips ---
        ltt_match = re.search(r'<h2>Local Travel Tips</h2>.*?<p>(.*?)</p>', html_content, re.DOTALL)
        if ltt_match:
            text = re.sub(r'<[^>]+>', '', ltt_match.group(1)).strip()
            if text:
                article_data['local_travel_tips'] = [{'category': 'General', 'advice': text}]
        
        # --- Extract safety_practical_info ---
        spi_match = re.search(r'<h2>Safety Practical Info</h2>.*?<p>(.*?)</p>', html_content, re.DOTALL)
        if spi_match:
            text = re.sub(r'<[^>]+>', '', spi_match.group(1)).strip()
            if text:
                article_data['safety_practical_info'] = {'emergency_contact': '', 'weather_risks': text, 'transportation_risks': '', 'local_laws': '', 'connectivity': '', 'sim_esim': '', 'insurance': ''}
        
        # --- Extract conclusion ---
        concl_match = re.search(r'<h2>Conclusion</h2>.*?<p>(.*?)</p>', html_content, re.DOTALL)
        if concl_match:
            text = re.sub(r'<[^>]+>', '', concl_match.group(1)).strip()
            if text:
                article_data['conclusion'] = text[:300]
        
        # --- Extract sources ---
        # Look for URLs or reference links in the content
        url_matches = re.findall(r'(?:href="|src="|url:\s*)([^"\s>]+)', html_content)
        if url_matches:
            article_data['sources'] = [{'title': 'Travel source', 'url': url_matches[0]}]
        
        # --- Extract SEO metadata ---
        # Try to find meta description, keywords, etc.
        meta_desc_match = re.search(r'meta.*?description["\']?\s*[:]?\s*["\']?(.*?)["\']', html_content, re.IGNORECASE | re.DOTALL)
        if meta_desc_match:
            desc = re.sub(r'<[^>]+>', '', meta_desc_match.group(1)).strip()[:300]
            if desc:
                from src.generator.article_contract import SEO
                article_data['seo'] = SEO(meta_description=desc, primary_keyword=title[:40] if title else '', slug=title[:30].lower().replace(' ', '-') if title else '', secondary_keywords=[], search_intent='')
        
        return article_data