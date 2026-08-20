import google.generativeai as genai
import os
import time
import re
import json
from datetime import datetime
from dotenv import load_dotenv
from src.generator.article_contract import QuickFact, WhyVisit, SEO, ArticleContract

load_dotenv()

class GeminiClient:
    def __init__(self):
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        # Pake Gemini 3.5 Flash - stabil dan cepat
        self.model = genai.GenerativeModel('models/gemini-3.5-flash')
        self.max_retries = 3
        self.retry_delay = 5  # detik

    def generate_article(self, topic, keywords=None):
        """Generate a complete structured travel article as JSON matching TravelArticle contract."""

        destination = topic.split(',')[0].strip() if topic else ''
        country = topic.split(',')[1].strip() if ',' in topic else ''

        prompt = self._build_prompt(topic, keywords)

        for attempt in range(self.max_retries):
            try:
                print(f"  🔄 Generating article (attempt {attempt + 1}/{self.max_retries})...")

                response = self.model.generate_content(
                    prompt,
                    generation_config={
                        'temperature': 0.4,
                        'top_p': 0.95,
                        'top_k': 40,
                    }
                )

                if response and response.text:
                    print(f"  ✅ Article generated successfully")
                    data = self._parse_response(response.text)

                    # Enrich with metadata required by TravelArticle
                    data['id'] = ArticleContract.generate_article_id(destination) if destination else "auto_generated_id"
                    data['destination'] = destination
                    data['country'] = country
                    data['generation_date'] = datetime.now().isoformat()
                    data['version'] = '1.0'
                    data['status'] = 'draft'

                    return data
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

    def _build_prompt(self, topic, keywords):
        """Build the deterministic JSON-generation prompt for the given topic."""

        kw_line = ""
        if keywords:
            kw_line = f"\nInclude these keywords naturally: {', '.join(keywords)}"

        schema_block = '''Return ONLY a single valid JSON object with exactly these keys:

{
  "title": "string (max 60 chars, plain text, no prefix)",
  "introduction": "string (2-4 sentences, max 500 chars)",
  "quick_facts": {
    "destination": "string",
    "country": "string",
    "region": "string",
    "continent": "string",
    "language": "string",
    "currency": "string",
    "timezone": "string",
    "recommended_trip_duration": "string",
    "best_travel_seasons": "string",
    "destination_type": "string"
  },
  "why_visit": {
    "culture": false, "history": false, "nature": false, "food": false,
    "architecture": false, "adventure": false, "shopping": false,
    "nightlife": false, "family_travel": false, "relaxation": false
  },
  "best_things_to_do": [
    {"name": "string", "description": "string", "why_important": "string", "practical_context": "string"}
  ],
  "best_places_to_visit": [
    {"name": "string", "type": "string", "description": "string", "best_for": "string"}
  ],
  "best_time_to_visit": "string",
  "how_to_get_there": "string",
  "getting_around": [
    {"mode": "string", "description": "string"}
  ],
  "where_to_stay": [
    {"area": "string", "characteristics": "string"}
  ],
  "local_food_to_try": [
    {"dish": "string", "description": "string"}
  ],
  "travel_budget": [
    {"level": "string", "daily_total": "string"}
  ],
  "suggested_itinerary": [
    {"day_flow": "string", "highlights": "string", "practical_notes": "string"}
  ],
  "local_travel_tips": [
    {"category": "string", "advice": "string"}
  ],
  "safety_practical_info": {
    "weather_risks": "string",
    "transportation_risks": "string",
    "local_laws": "string",
    "connectivity": "string",
    "sim_esim": "string",
    "insurance": "string",
    "emergency_contact": "string"
  },
  "faq": [
    {"question": "string", "answer": "string"}
  ],
  "conclusion": "string (max 300 chars)",
  "sources": [
    {"title": "string", "url": "string (real https URL)"}
  ],
  "seo": {
    "title": "string",
    "meta_description": "string (150-160 chars)",
    "slug": "string (url-safe, hyphenated)",
    "primary_keyword": "string",
    "secondary_keywords": ["string"],
    "search_intent": "string"
  }
}'''

        prompt = f"""You are a professional travel writer. Write a complete, factual travel article about {topic} in ENGLISH.

{schema_block}

STRICT REQUIREMENTS:
- Provide at least 8 items in best_things_to_do.
- Provide at least 8 items in best_places_to_visit.
- Provide at least 5 items in faq.
- Provide at least 1 source with a real, valid https URL.
- why_visit must have at least 3 true values.
- ALL keys above must be present; do not omit any.
- Use real, factual information about {topic}. Do NOT invent prices, URLs, attractions, or statistics.
- Do NOT use phrases like "must-see", "hidden gem", "completely safe", "100% safe", or any first-person claims ("I visited", "when I was there").{kw_line}

Output ONLY the JSON object. No markdown, no code fences, no commentary before or after."""

        return prompt

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
        """Parse Gemini JSON response into a TravelArticle-compatible dict.

        Fails clearly (raises) if the response is not valid JSON or is missing
        required keys, so an invalid article never reaches the validator silently.
        """
        text = raw_text.strip()

        # Strip markdown code fences if present (defensive)
        fence = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
        if fence:
            text = fence.group(1).strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise Exception(f"Gemini did not return valid JSON: {e}")

        if not isinstance(data, dict):
            raise Exception("Gemini response JSON is not an object")

        required_keys = [
            'title', 'introduction', 'quick_facts', 'why_visit',
            'best_things_to_do', 'best_places_to_visit', 'best_time_to_visit',
            'how_to_get_there', 'getting_around', 'where_to_stay',
            'local_food_to_try', 'travel_budget', 'suggested_itinerary',
            'local_travel_tips', 'safety_practical_info', 'faq',
            'conclusion', 'sources', 'seo'
        ]
        missing = [k for k in required_keys if k not in data]
        if missing:
            raise Exception(f"Gemini JSON missing required keys: {', '.join(missing)}")

        # Normalize list fields to avoid None
        for list_key in ['best_things_to_do', 'best_places_to_visit', 'getting_around',
                         'where_to_stay', 'local_food_to_try', 'travel_budget',
                         'suggested_itinerary', 'local_travel_tips', 'faq', 'sources']:
            if data.get(list_key) is None:
                data[list_key] = []

        # Safe truncation to satisfy contract max lengths
        if isinstance(data.get('title'), str):
            data['title'] = data['title'][:60]
        if isinstance(data.get('introduction'), str):
            data['introduction'] = data['introduction'][:500]
        if isinstance(data.get('conclusion'), str):
            data['conclusion'] = data['conclusion'][:300]
        if isinstance(data.get('best_time_to_visit'), str):
            data['best_time_to_visit'] = data['best_time_to_visit'][:300]
        if isinstance(data.get('how_to_get_there'), str):
            data['how_to_get_there'] = data['how_to_get_there'][:400]

        return data
