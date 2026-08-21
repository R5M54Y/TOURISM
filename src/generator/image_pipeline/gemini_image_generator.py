"""Gemini Image generation module.

Implements isolated image-generation phase:
- Takes existing image_prompt
- Calls Gemini Image API
- Returns image bytes
- Handles 429 with bounded backoff
"""

import os
import time
import random
import requests
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

# Supported image-generation model in Google Generative AI
GEMINI_IMAGE_MODEL = "gemini-2.0-flash-exp"
GEMINI_IMAGE_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

# Retry configuration for 429 handling
MAX_RETRIES = 4
BASE_DELAY = 2.0
MAX_DELAY = 60.0
JITTER = 0.5


class GeminiImageGenerator:
    """Dedicated image-generation client for Gemini Image API."""

    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")

        self.model = GEMINI_IMAGE_MODEL
        self.max_retries = MAX_RETRIES
        self.base_delay = BASE_DELAY
        self.max_delay = MAX_DELAY

    def generate_image(self, image_prompt: str) -> bytes:
        """Generate image from prompt.

        Args:
            image_prompt: Existing image_prompt from TravelArticle

        Returns:
            Raw image bytes (PNG/JPEG)

        Raises:
            Exception: On failure after retries exhausted
        """
        if not image_prompt or not image_prompt.strip():
            raise ValueError("image_prompt cannot be empty")

        url = GEMINI_IMAGE_API_URL.format(model=self.model)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "contents": [{
                "parts": [{
                    "text": image_prompt
                }]
            }],
            "generationConfig": {
                "responseModalities": ["IMAGE", "TEXT"],
                "temperature": 0.4
            }
        }

        last_error = None

        for attempt in range(self.max_retries):
            try:
                print(f"  🔄 Generating image (attempt {attempt + 1}/{self.max_retries})...")

                response = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=120
                )

                # Handle 429 with Retry-After
                if response.status_code == 429:
                    retry_after = response.headers.get('Retry-After')
                    if retry_after:
                        try:
                            wait_time = float(retry_after)
                        except (ValueError, TypeError):
                            wait_time = self._calculate_backoff(attempt)
                    else:
                        wait_time = self._calculate_backoff(attempt)

                    print(f"  ⚠️ Rate limited (429). Waiting {wait_time:.1f}s before retry...")
                    time.sleep(wait_time)
                    last_error = Exception("Rate limit (429) after retries")
                    continue

                # Other error status
                if response.status_code != 200:
                    error_msg = f"Gemini Image API error {response.status_code}: {response.text[:200]}"
                    if attempt < self.max_retries - 1:
                        wait_time = self._calculate_backoff(attempt)
                        print(f"  ⚠️ {error_msg}. Retry in {wait_time:.1f}s...")
                        time.sleep(wait_time)
                        last_error = Exception(error_msg)
                        continue
                    else:
                        raise Exception(error_msg)

                # Success - extract image bytes
                data = response.json()
                image_bytes = self._extract_image_bytes(data)

                if image_bytes:
                    print(f"  ✅ Image generated ({len(image_bytes)} bytes)")
                    return image_bytes
                else:
                    raise Exception("No image data in Gemini Image response")

            except requests.exceptions.Timeout:
                if attempt < self.max_retries - 1:
                    wait_time = self._calculate_backoff(attempt)
                    print(f"  ⚠️ Timeout. Retry in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    last_error = Exception("Timeout")
                    continue
                else:
                    raise Exception("Gemini Image generation timeout after retries")

            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait_time = self._calculate_backoff(attempt)
                    print(f"  ⚠️ Error: {str(e)[:100]}. Retry in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    last_error = e
                    continue
                else:
                    raise e

        raise last_error or Exception("Image generation failed")

    def _calculate_backoff(self, attempt: int) -> float:
        """Bounded exponential backoff with jitter."""
        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
        jitter = random.uniform(0, JITTER)
        return delay + jitter

    @staticmethod
    def _extract_image_bytes(data: dict) -> bytes:
        """Extract image bytes from Gemini Image API response."""
        try:
            candidates = data.get('candidates', [])
            if not candidates:
                return b""

            content = candidates[0].get('content', {})
            parts = content.get('parts', [])

            for part in parts:
                if 'inlineData' in part:
                    inline_data = part['inlineData']
                    if inline_data.get('mimeType', '').startswith('image/'):
                        import base64
                        return base64.b64decode(inline_data['data'])

            return b""

        except Exception:
            return b""


def generate_image_from_prompt(image_prompt: str) -> bytes:
    """Convenience wrapper for image generation."""
    generator = GeminiImageGenerator()
    return generator.generate_image(image_prompt)
