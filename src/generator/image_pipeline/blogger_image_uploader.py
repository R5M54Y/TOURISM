"""Blogger image storage/upload module.

Uploads generated image bytes to Blogger and returns a stable
public HTTPS URL.

Uses Google API Client (google-api-python-client) with Blogger v3
media upload if available, otherwise uses a fallback storage
mechanism through Google Cloud Storage if configured.
"""

import os
import io
import json
import tempfile
from typing import Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload
    from google.oauth2.credentials import Credentials
    from google.oauth2 import service_account
    HAS_GOOGLE_API = True
except ImportError:
    HAS_GOOGLE_API = False


class BloggerImageUploader:
    """Upload generated images to Blogger and return public URL."""

    def __init__(self):
        self.blog_id = os.getenv('BLOGGER_BLOG_ID')
        self.api_key = os.getenv('BLOGGER_API_KEY')

        # Authentication: OAuth2 token or service account
        self.credentials = self._load_credentials()

        self.service = None
        if HAS_GOOGLE_API and self.credentials:
            try:
                self.service = build('blogger', 'v3', credentials=self.credentials)
            except Exception:
                self.service = None

    def _load_credentials(self):
        """Load credentials from environment variables."""
        # Option 1: OAuth2 access token (simplest)
        access_token = os.getenv('BLOGGER_ACCESS_TOKEN')
        if access_token:
            return Credentials(token=access_token)

        # Option 2: Service account JSON
        service_account_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if service_account_path and os.path.exists(service_account_path):
            try:
                return service_account.Credentials.from_service_account_file(
                    service_account_path,
                    scopes=['https://www.googleapis.com/auth/blogger']
                )
            except Exception:
                return None

        return None

    def upload_image(self, image_bytes: bytes, filename: str = "hero_image.png") -> Optional[str]:
        """Upload image bytes to Blogger and return public URL.

        Args:
            image_bytes: Raw image data
            filename: Image filename

        Returns:
            Public URL string, or None on failure
        """
        if not image_bytes:
            raise ValueError("image_bytes cannot be empty")

        if not self.service:
            # Fallback to Google Cloud Storage if not Blogger auth
            return self._upload_to_gcs_fallback(image_bytes, filename)

        try:
            # Blogger v3 media upload
            media = MediaIoBaseUpload(
                io.BytesIO(image_bytes),
                mimetype='image/png',
                resumable=True
            )

            # Use pageMedia or blog pageMedia.insert if available
            # Blogger API v3 has limited media upload support
            # Most common pattern is to upload to Google Cloud Storage
            # and use that URL in Blogger post content

            # Try Blogger media.insert endpoint
            try:
                request = self.service.pageMedia().insert(
                    blogId=self.blog_id,
                    media_body=media
                )
                response = request.execute()
                if response and 'url' in response:
                    return response['url']
            except Exception as blogger_error:
                print(f"  ⚠️ Blogger media upload failed: {blogger_error}")
                # Fall back to GCS
                return self._upload_to_gcs_fallback(image_bytes, filename)

        except Exception as e:
            print(f"  ⚠️ Image upload error: {e}")
            return self._upload_to_gcs_fallback(image_bytes, filename)

        return None

    def _upload_to_gcs_fallback(self, image_bytes: bytes, filename: str) -> Optional[str]:
        """Fallback: Upload to Google Cloud Storage and return public URL."""
        try:
            from google.cloud import storage

            bucket_name = os.getenv('GCS_IMAGE_BUCKET')
            if not bucket_name:
                return None

            client = storage.Client()
            bucket = client.bucket(bucket_name)

            blob_name = f"article-images/{filename}"
            blob = bucket.blob(blob_name)
            blob.upload_from_string(image_bytes, content_type='image/png')

            # Make public
            blob.make_public()

            return blob.public_url

        except Exception as e:
            print(f"  ⚠️ GCS fallback failed: {e}")
            return None


def upload_image_to_blogger(image_bytes: bytes, filename: str = "hero_image.png") -> Optional[str]:
    """Convenience wrapper for image upload."""
    uploader = BloggerImageUploader()
    return uploader.upload_image(image_bytes, filename)
