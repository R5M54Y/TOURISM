"""Image pipeline orchestration.

Combines Gemini Image generation + Blogger upload into one phase.
Article generation stays frozen.
"""

from typing import Optional, Dict, Any
from src.generator.image_pipeline.gemini_image_generator import GeminiImageGenerator, generate_image_from_prompt
from src.generator.image_pipeline.blogger_image_uploader import BloggerImageUploader, upload_image_to_blogger


class ImagePipeline:
    """Orchestrates the image generation and upload phase."""

    def __init__(self):
        self.image_generator = GeminiImageGenerator()
        self.image_uploader = BloggerImageUploader()

    def run(self, image_prompt: str, destination: str = "article") -> Dict[str, Any]:
        """Run the complete image pipeline.

        Args:
            image_prompt: Existing image_prompt from TravelArticle
            destination: Destination name for filename

        Returns:
            Dict with status and image_url
        """
        result = {
            'article_status': 'PASS',
            'image_generation': 'PENDING',
            'image_storage': 'PENDING',
            'image_url': None,
            'error': None
        }

        # 1. Generate image
        try:
            image_bytes = self.image_generator.generate_image(image_prompt)
            result['image_generation'] = 'PASS'

            # 2. Upload to Blogger
            filename = f"{destination.replace(' ', '_').lower()}_hero.png"
            image_url = self.image_uploader.upload_image(image_bytes, filename)

            if image_url:
                result['image_storage'] = 'PASS'
                result['image_url'] = image_url
            else:
                result['image_storage'] = 'FAIL'
                result['error'] = 'Image upload returned no URL'

        except Exception as e:
            result['image_generation'] = 'FAIL'
            result['image_storage'] = 'FAIL'
            result['error'] = str(e)

        return result


def run_image_pipeline(image_prompt: str, destination: str = "article") -> Dict[str, Any]:
    """Convenience wrapper for the image pipeline."""
    pipeline = ImagePipeline()
    return pipeline.run(image_prompt, destination)
