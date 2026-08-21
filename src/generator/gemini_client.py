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
        self.model = genai.GenerativeModel('models/gemini-3.5-flash')
        self.max_retries = 3
        self.retry_delay = 5

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
                        'max_output_tokens': 16384,
                    }
                )

                # Check for truncation via finish reason
                if response.candidates:
                    finish = response.candidates[0].finish_reason
                    if finish and finish.name != 'STOP':
                        raise Exception(f"Response truncated (finish_reason={finish.name})")

                if response and response.text:
                    data = self._parse_response(response.text)
                    print(f"  ✅ Article generated: {data.get('title', '?')[:50]}")

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
                is_transient = (
                    "504" in error_msg or "Deadline" in error_msg or "timeout" in error_msg.lower()
                    or "truncated" in error_msg.lower()
                    or "missing required" in error_msg.lower()
                    or "empty required" in error_msg.lower()
                    or "Gemini did not return valid JSON" in error_msg
                    or "not an object" in error_msg
                )
                if is_transient and attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (attempt + 1)
                    print(f"  ⚠️ Attempt failed ({error_msg[:80]}). Retry {attempt+2}/{self.max_retries} in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"  ❌ Failed: {error_msg[:120]}")
                    raise

        raise Exception("Unexpected error in generate_article")

    def _build_prompt(self, topic, keywords):
        """Build the complete structured JSON-generation prompt."""

        kw_line = ""
        if keywords:
            kw_line = f"\nInclude these keywords naturally: {', '.join(keywords)}"

        schema_block = '''{
  "title": "string (max 60 chars, article title about the destination)",
  "introduction": "string (2-4 sentences, max 500 chars)",
  "quick_facts": {
    "destination": "string — destination name",
    "country": "string — country name",
    "region": "string — region within country",
    "continent": "string — continent",
    "language": "string — primary language(s) spoken",
    "currency": "string — currency name and code",
    "timezone": "string — timezone with UTC offset",
    "recommended_trip_duration": "string — e.g. '3-5 days'",
    "best_travel_seasons": "string — seasons or months",
    "destination_type": "string — e.g. 'Historic City', 'Coastal Town'"
  },
  "why_visit": {
    "culture": true/false, "history": true/false, "nature": true/false,
    "food": true/false, "architecture": true/false, "adventure": true/false,
    "shopping": true/false, "nightlife": true/false, "family_travel": true/false,
    "relaxation": true/false
  },
  "best_things_to_do": [
    {
      "name": "string — activity or attraction name",
      "description": "string — 1-2 sentences about what it is",
      "why_important": "string — why travelers should do this",
      "practical_context": "string — cost, booking info, or logistics",
      "estimated_duration": "string — e.g. '2-3 hours', 'Half day', 'Full day'",
      "best_time": "string — e.g. 'Early morning', 'Sunset', 'Weekday mornings'"
    }
  ],
  "best_places_to_visit": [
    {
      "name": "string — place name",
      "type": "string — landmark, neighborhood, temple, museum, market, etc.",
      "description": "string — 1-2 sentences",
      "best_for": "string — who should visit this",
      "hidden_gem": true/false
    }
  ],
  "best_time_to_visit": "string — 2-3 sentences covering weather, seasons, and crowd levels",
  "how_to_get_there": "string — 2-3 sentences about arrival (airport, train, bus)",
  "getting_around": [
    {
      "mode": "string — walking, tuk-tuk, metro, bus, taxi, bicycle, etc.",
      "description": "string — how this mode works, costs, tips"
    }
  ],
  "where_to_stay": [
    {
      "area": "string — neighborhood or district name",
      "characteristics": "string — what this area is like",
      "ideal_traveler": "string — who this area suits best",
      "transportation_convenience": "string — getting around from here",
      "advantages": "string — key advantages of staying here",
      "potential_drawbacks": "string — any downsides"
    }
  ],
  "local_food_to_try": [
    {
      "dish": "string — dish or food name",
      "description": "string — what it is and how it tastes",
      "cultural_significance": "string — tradition or context behind the dish",
      "where_found": "string — best places to try it"
    }
  ],
  "travel_budget": [
    {
      "level": "string — 'Budget', 'Mid-range', or 'Premium'",
      "accommodation": "string — nightly cost range",
      "food": "string — daily food cost range",
      "transportation": "string — daily transport cost range",
      "attractions": "string — daily activity cost range",
      "daily_total": "string — total daily cost range"
    }
  ],
  "suggested_itinerary": [
    {
      "duration": "string — e.g. 'Day 1', 'Days 2-3'",
      "day_flow": "string — morning, afternoon, evening activities",
      "highlights": "string — key experiences",
      "practical_notes": "string — timing, transport, or booking tips"
    }
  ],
  "local_travel_tips": [
    {
      "category": "string — etiquette, payment, language, health, packing, etc.",
      "advice": "string — the specific tip",
      "explanation": "string — why this matters, with practical context"
    }
  ],
  "safety_practical_info": {
    "emergency_contact": "string — local emergency number(s)",
    "weather_risks": "string — weather-related risks and preparation",
    "transportation_risks": "string — transport safety considerations",
    "local_laws": "string — important laws or customs",
    "accessibility": "string — accessibility for travelers with disabilities",
    "connectivity": "string — WiFi and internet availability",
    "sim_esim": "string — SIM card or eSIM options",
    "insurance": "string — recommended insurance considerations"
  },
  "faq": [
    {
      "question": "string — common traveler question",
      "answer": "string — specific, helpful answer"
    }
  ],
  "conclusion": "string — 2-3 sentences wrapping up (max 300 chars)",
  "sources": [
    {
      "title": "string — source name",
      "url": "string — real https:// URL"
    }
  ],
  "seo": {
    "title": "string — SEO-optimized title",
    "meta_description": "string — 150-160 char summary",
    "slug": "string — URL-friendly lowercase hyphenated slug",
    "primary_keyword": "string — main keyword phrase",
    "secondary_keywords": ["string", "string", "string"],
    "search_intent": "string — 'informational', 'commercial', or 'transactional'"
  }
}'''

        prompt = f"""You are a professional travel writer. Create a complete, factual travel guide about {topic} in ENGLISH.

Return ONLY a single valid JSON object matching this EXACT schema:

{schema_block}

CRITICAL RULES — violations will cause generation failure:
1. Every string field MUST contain real, specific information about {topic}.
2. NEVER return "" (empty string) or null for ANY string field.
3. NEVER use filler: "N/A", "varies", "see local sources", "information unavailable".
4. estimated_duration must be specific: "1-2 hours", "Half day", "Full day".
5. best_time must be specific to the activity and destination.
6. Every accommodation area: populate ALL 6 fields (area, characteristics, ideal_traveler, transportation_convenience, advantages, potential_drawbacks).
7. Every food item: populate ALL 4 fields including cultural_significance and where_found.
8. Every budget level: populate ALL 6 fields including accommodation, food, transportation, attractions separately.
9. Every itinerary entry: populate ALL 4 fields including duration.
10. Every travel tip: populate ALL 3 fields including explanation.
11. safety_practical_info: populate ALL 8 sub-fields.
12. FAQ answers: specific to {topic}, not generic.
13. All source URLs: real, valid https:// URLs from known websites.
14. NEVER truncate mid-sentence. Complete every field.

MINIMUM COUNTS:
- best_things_to_do: >= 8 items
- best_places_to_visit: >= 8 items
- where_to_stay: >= 2 areas
- local_food_to_try: >= 4 items
- travel_budget: exactly 3 levels (Budget, Mid-range, Premium)
- suggested_itinerary: >= 3 entries
- local_travel_tips: >= 4 items
- faq: >= 5 items
- sources: >= 2 items
- why_visit: >= 3 true values

BANNED PHRASES: "must-see", "hidden gem", "completely safe", "100% safe", first-person claims.

Output ONLY the complete JSON object. No markdown fences, no commentary before or after.{kw_line}"""

        return prompt

    def generate_image_prompt(self, topic):
        """Generate prompt for image search"""
        prompt = f"""Create a short image search query (max 50 words) for a travel photo about: {topic}
The query should be in English.
Output ONLY the query, no explanations."""

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
        """Parse Gemini JSON response and validate nested field completeness."""
        text = raw_text.strip()

        # Strip markdown code fences if present
        fence = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
        if fence:
            text = fence.group(1).strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise Exception(f"Gemini did not return valid JSON: {e}")

        if not isinstance(data, dict):
            raise Exception("Gemini response JSON is not an object")

        # ── Top-level key check ──────────────────────────────────────
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

        # ── Normalize None lists ─────────────────────────────────────
        for list_key in ['best_things_to_do', 'best_places_to_visit', 'getting_around',
                         'where_to_stay', 'local_food_to_try', 'travel_budget',
                         'suggested_itinerary', 'local_travel_tips', 'faq', 'sources']:
            if data.get(list_key) is None:
                data[list_key] = []

        # ── Safe truncation for max-length fields ────────────────────
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

        # ── Nested field completeness check ──────────────────────────
        errors = self._check_completeness(data)
        if errors:
            raise Exception(
                "Incomplete article — missing required content: " + "; ".join(errors[:5])
                + (f" (+{len(errors)-5} more)" if len(errors) > 5 else "")
            )

        return data

    @staticmethod
    def _check_completeness(data):
        """Validate that every nested required field has meaningful content.
        Returns a list of human-readable error descriptions."""

        errors = []

        def _req_str(obj, path):
            """Check that a field is a non-empty, non-filler string."""
            if not isinstance(obj, dict):
                return
            val = obj.get(path)
            if val is None:
                errors.append(f"{path} is null")
            elif isinstance(val, str):
                stripped = val.strip()
                if stripped == "":
                    errors.append(f"{path} is empty")
                elif stripped.lower() in ("n/a", "na", "varies", "tbd", "unknown",
                                           "information unavailable", "see local sources",
                                           "not available", "none"):
                    errors.append(f"{path} is filler: '{stripped}'")

        def _req_bool(obj, path):
            """Check that a boolean field is present."""
            if not isinstance(obj, dict):
                return
            if path not in obj or obj[path] is None:
                errors.append(f"{path} is missing/null")

        def _req_list(obj, path, item_checks, min_count=1):
            """Check a list of objects."""
            val = obj.get(path, [])
            if not val:
                errors.append(f"{path} is empty (need >= {min_count})")
                return
            if len(val) < min_count:
                errors.append(f"{path} has {len(val)} items (need >= {min_count})")
            for i, item in enumerate(val):
                if not isinstance(item, dict):
                    errors.append(f"{path}[{i}] is not an object")
                    continue
                for check in item_checks:
                    check(item, f"{path}[{i}]")

        # quick_facts
        qf = data.get('quick_facts', {})
        if isinstance(qf, dict):
            for f in ['destination', 'country', 'region', 'continent', 'language',
                       'currency', 'timezone', 'recommended_trip_duration',
                       'best_travel_seasons', 'destination_type']:
                _req_str(qf, f)

        # why_visit
        wv = data.get('why_visit', {})
        if isinstance(wv, dict):
            true_count = sum(1 for v in wv.values() if v is True)
            if true_count < 3:
                errors.append(f"why_visit has only {true_count} true values (need >= 3)")

        # best_things_to_do
        _req_list(data, 'best_things_to_do', [
            lambda o, p: _req_str(o, 'name'),
            lambda o, p: _req_str(o, 'description'),
            lambda o, p: _req_str(o, 'why_important'),
            lambda o, p: _req_str(o, 'practical_context'),
            lambda o, p: _req_str(o, 'estimated_duration'),
            lambda o, p: _req_str(o, 'best_time'),
        ], min_count=8)

        # best_places_to_visit
        _req_list(data, 'best_places_to_visit', [
            lambda o, p: _req_str(o, 'name'),
            lambda o, p: _req_str(o, 'type'),
            lambda o, p: _req_str(o, 'description'),
            lambda o, p: _req_str(o, 'best_for'),
        ], min_count=8)

        # best_time_to_visit (string)
        bttv = data.get('best_time_to_visit', '')
        if isinstance(bttv, str) and len(bttv.strip()) < 20:
            errors.append(f"best_time_to_visit too short ({len(bttv.strip())} chars)")
        elif not bttv:
            errors.append("best_time_to_visit is empty")

        # how_to_get_there (string)
        htgt = data.get('how_to_get_there', '')
        if isinstance(htgt, str) and len(htgt.strip()) < 20:
            errors.append(f"how_to_get_there too short ({len(htgt.strip())} chars)")
        elif not htgt:
            errors.append("how_to_get_there is empty")

        # getting_around
        _req_list(data, 'getting_around', [
            lambda o, p: _req_str(o, 'mode'),
            lambda o, p: _req_str(o, 'description'),
        ], min_count=1)

        # where_to_stay
        _req_list(data, 'where_to_stay', [
            lambda o, p: _req_str(o, 'area'),
            lambda o, p: _req_str(o, 'characteristics'),
            lambda o, p: _req_str(o, 'ideal_traveler'),
            lambda o, p: _req_str(o, 'transportation_convenience'),
            lambda o, p: _req_str(o, 'advantages'),
            lambda o, p: _req_str(o, 'potential_drawbacks'),
        ], min_count=2)

        # local_food_to_try
        _req_list(data, 'local_food_to_try', [
            lambda o, p: _req_str(o, 'dish'),
            lambda o, p: _req_str(o, 'description'),
            lambda o, p: _req_str(o, 'cultural_significance'),
            lambda o, p: _req_str(o, 'where_found'),
        ], min_count=4)

        # travel_budget
        _req_list(data, 'travel_budget', [
            lambda o, p: _req_str(o, 'level'),
            lambda o, p: _req_str(o, 'accommodation'),
            lambda o, p: _req_str(o, 'food'),
            lambda o, p: _req_str(o, 'transportation'),
            lambda o, p: _req_str(o, 'attractions'),
            lambda o, p: _req_str(o, 'daily_total'),
        ], min_count=3)

        # suggested_itinerary
        _req_list(data, 'suggested_itinerary', [
            lambda o, p: _req_str(o, 'duration'),
            lambda o, p: _req_str(o, 'day_flow'),
            lambda o, p: _req_str(o, 'highlights'),
            lambda o, p: _req_str(o, 'practical_notes'),
        ], min_count=3)

        # local_travel_tips
        _req_list(data, 'local_travel_tips', [
            lambda o, p: _req_str(o, 'category'),
            lambda o, p: _req_str(o, 'advice'),
            lambda o, p: _req_str(o, 'explanation'),
        ], min_count=4)

        # safety_practical_info
        si = data.get('safety_practical_info', {})
        if isinstance(si, dict):
            for f in ['emergency_contact', 'weather_risks', 'transportation_risks',
                       'local_laws', 'accessibility', 'connectivity', 'sim_esim', 'insurance']:
                _req_str(si, f)
        else:
            errors.append("safety_practical_info is not an object")

        # faq
        _req_list(data, 'faq', [
            lambda o, p: _req_str(o, 'question'),
            lambda o, p: _req_str(o, 'answer'),
        ], min_count=5)

        # conclusion (string)
        conc = data.get('conclusion', '')
        if isinstance(conc, str) and len(conc.strip()) < 20:
            errors.append(f"conclusion too short ({len(conc.strip())} chars)")
        elif not conc:
            errors.append("conclusion is empty")

        # sources
        _req_list(data, 'sources', [
            lambda o, p: _req_str(o, 'title'),
            lambda o, p: _req_str(o, 'url'),
        ], min_count=2)

        # Check source URLs are real https
        for i, src in enumerate(data.get('sources', [])):
            if isinstance(src, dict):
                url = src.get('url', '')
                if isinstance(url, str) and not url.startswith('https://'):
                    errors.append(f"sources[{i}] url not https: {url[:60]}")

        # seo
        seo = data.get('seo', {})
        if isinstance(seo, dict):
            for f in ['title', 'meta_description', 'slug', 'primary_keyword',
                       'search_intent']:
                _req_str(seo, f)
            # secondary_keywords
            sk = seo.get('secondary_keywords')
            if not sk or not isinstance(sk, list) or len(sk) < 1:
                errors.append("seo.secondary_keywords is empty")
        else:
            errors.append("seo is not an object")

        return errors
