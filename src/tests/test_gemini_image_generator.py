#!/usr/bin/env python3
"""Unit tests for Gemini Image generator authentication + retry logic.

Mocks HTTP to avoid requiring real credentials. Verifies:
1. Auth header is `x-goog-api-key` (not OAuth Bearer)
2. 401/403 fails immediately (no retry)
3. 429 retries with backoff
4. 5xx retries; 4xx (non-401/403) fails immediately
5. Successful image bytes are extracted
"""

import os
import sys
import json
from unittest import mock
from pathlib import Path

# Add project root (parent of src/) to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import requests


class FakeResponse:
    def __init__(self, status_code, text="", headers=None):
        self.status_code = status_code
        self._text = text
        self.headers = headers or {}

    @property
    def text(self):
        return self._text

    def json(self):
        return json.loads(self._text) if self._text else {}


def make_image_response():
    import base64
    png = base64.b64encode(b"\x89PNG\r\n\x1a\nFAKEDATA").decode()
    return FakeResponse(200, json.dumps({
        "candidates": [{
            "content": {
                "parts": [{"inlineData": {"mimeType": "image/png", "data": png}}]
            }
        }]
    }))


def test_auth_header_is_api_key():
    """Verify the request uses x-goog-api-key, not Authorization Bearer."""
    captured = {}

    def fake_post(url, json=None, headers=None, timeout=None):
        captured['headers'] = headers
        captured['url'] = url
        return make_image_response()

    with mock.patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key-123'}):
        with mock.patch('requests.post', side_effect=fake_post):
            from src.generator.image_pipeline.gemini_image_generator import generate_image_from_prompt
            data = generate_image_from_prompt("test prompt")

    assert captured['headers'].get('x-goog-api-key') == 'test-key-123', \
        f"Expected x-goog-api-key header, got: {captured['headers']}"
    assert 'Authorization' not in captured['headers'], \
        f"Must NOT use Authorization Bearer, got: {captured['headers']}"
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "Image bytes not extracted"
    print("✓ Auth header uses x-goog-api-key (not OAuth Bearer)")
    return True


def test_401_fails_immediately():
    """401 must NOT be retried — fail on first attempt."""
    calls = {'n': 0}

    def fake_post(url, json=None, headers=None, timeout=None):
        calls['n'] += 1
        return FakeResponse(401, '{"error":{"message":"Expected OAuth 2 access token"}}')

    with mock.patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key-123'}):
        with mock.patch('requests.post', side_effect=fake_post):
            from src.generator.image_pipeline.gemini_image_generator import generate_image_from_prompt
            try:
                generate_image_from_prompt("test prompt")
                print("✗ 401 should have raised")
                return False
            except Exception as e:
                pass

    assert calls['n'] == 1, f"401 retried {calls['n']} times, expected 1"
    print("✓ 401 fails immediately (no retry)")


def test_429_retries_with_backoff():
    """429 must retry (bounded) before succeeding."""
    calls = {'n': 0}

    def fake_post(url, json=None, headers=None, timeout=None):
        calls['n'] += 1
        if calls['n'] < 3:
            return FakeResponse(429, 'rate limited', headers={'Retry-After': '0'})
        return make_image_response()

    with mock.patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key-123'}):
        with mock.patch('requests.post', side_effect=fake_post):
            from src.generator.image_pipeline.gemini_image_generator import generate_image_from_prompt
            data = generate_image_from_prompt("test prompt")

    assert calls['n'] == 3, f"Expected 3 calls (2 retries + 1 success), got {calls['n']}"
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    print("✓ 429 retries with backoff then succeeds")


def test_500_retries_then_fails():
    """5xx retries but exhausts and raises."""
    calls = {'n': 0}

    def fake_post(url, json=None, headers=None, timeout=None):
        calls['n'] += 1
        return FakeResponse(500, 'server error')

    with mock.patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key-123'}):
        with mock.patch('requests.post', side_effect=fake_post):
            from src.generator.image_pipeline.gemini_image_generator import generate_image_from_prompt
            try:
                generate_image_from_prompt("test prompt")
                print("✗ 500 should have raised")
                return False
            except Exception:
                pass

    # MAX_RETRIES = 4 → 4 attempts
    assert calls['n'] == 4, f"Expected 4 attempts, got {calls['n']}"
    print("✓ 5xx retries (bounded) then fails")


def test_400_fails_immediately():
    """Other 4xx (e.g. 400) must NOT be retried."""
    calls = {'n': 0}

    def fake_post(url, json=None, headers=None, timeout=None):
        calls['n'] += 1
        return FakeResponse(400, 'bad request')

    with mock.patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key-123'}):
        with mock.patch('requests.post', side_effect=fake_post):
            from src.generator.image_pipeline.gemini_image_generator import generate_image_from_prompt
            try:
                generate_image_from_prompt("test prompt")
                print("✗ 400 should have raised")
                return False
            except Exception:
                pass

    assert calls['n'] == 1, f"400 retried {calls['n']} times, expected 1"
    print("✓ 400 fails immediately (no retry)")


if __name__ == "__main__":
    tests = [
        test_auth_header_is_api_key,
        test_401_fails_immediately,
        test_429_retries_with_backoff,
        test_500_retries_then_fails,
        test_400_fails_immediately,
    ]
    passed = 0
    for t in tests:
        try:
            t()  # assertions raise AssertionError on failure
            passed += 1
        except AssertionError as e:
            print(f"✗ {t.__name__}: {e}")
        except Exception as e:
            print(f"✗ {t.__name__} crashed: {e}")
    print(f"\n{passed}/{len(tests)} tests passed")
    sys.exit(0 if passed == len(tests) else 1)