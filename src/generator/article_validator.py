"""
Article Validator for Travel Content

Validates article structure, content quality, and anti-hallucination compliance.
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
from src.generator.article_contract import TravelArticle, ArticleContract

class ArticleValidator:
    """Validates travel articles against the contract"""

    # List of unsafe phrases to check for
    UNSAFE_PHRASES = [
        "completely safe",
        "100% safe",
        "totally safe",
        "I visited",
        "I went to",
        "when I was there",
        "in my experience",
        "as someone who has been",
        "must-see",
        "hidden gem"
    ]

    # Placeholder phrases for unavailable data
    UNAVAILABLE_PHRASES = ["needs verification", "unavailable", "unknown", "n/a", "not available"]

    @staticmethod
    def validate(article: TravelArticle) -> Dict[str, Any]:
        """Full validation: structure, content, anti-hallucination"""
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'total_sections': 0,       # how many of the 18 canonical sections have content
            'reported_sections': 0,   # how many are recognized as present
            'content_length': 0
        }

        # 1. Structural validation
        ArticleValidator._validate_structure(article, result)

        # 2. Content quality validation
        ArticleValidator._validate_content_quality(article, result)

        # 3. Anti-hallucination validation
        ArticleValidator._validate_anti_hallucination(article, result)

        # 4. SEO validation
        ArticleValidator._validate_seo(article, result)

        # Calculate canonical-section coverage (18 sections)
        # Count only sections that have actual content (non-None, non-empty)
        reported = 0
        for section in ArticleContract.CANONICAL_SECTIONS:
            content = getattr(article, section)
            # A section counts as "present" if it is a list with ≥1 item, or a non-empty string
            if content is not None:
                if isinstance(content, str) and content.strip():
                    reported += 1
                elif isinstance(content, list) and len(content) > 0:
                    reported += 1
                elif not isinstance(content, (list, str)):  # e.g. dataclass/SEO objects
                    reported += 1
        result['reported_sections'] = reported
        result['total_sections'] = len(ArticleContract.CANONICAL_SECTIONS)  # 18

        # The canonical count is what we report for the final result
        result['section_count'] = reported  # will be 18/18 when all present
        result['content_length'] = len(json.dumps(article.to_dict(), default=lambda o: o.__dict__))

        result['valid'] = len(result['errors']) == 0
        return result
    @staticmethod
    def _validate_structure(article: TravelArticle, result: Dict[str, Any]) -> None:
        """Validate article structure and required fields"""
        # Use contract validation
        contract_errors = ArticleContract.validate_article(article)
        result['errors'].extend(contract_errors)

        # Check for empty sections
        empty_sections = []
        for section in ArticleContract.SCHEMA['required_sections']:
            content = getattr(article, section)
            if content is None or (isinstance(content, (list, dict, str)) and len(content) == 0):
                empty_sections.append(section)

        if empty_sections:
            result['errors'].append(f"Empty sections: {', '.join(empty_sections)}")

    @staticmethod
    def _validate_content_quality(article: TravelArticle, result: Dict[str, Any]) -> None:
        """Validate content quality rules"""
        # Check title
        if article.title:
            title_lower = article.title.lower()
            generic_intros = ["welcome to", "in the heart of", "nestled in", "are you looking for"]
            for intro in generic_intros:
                if intro in title_lower:
                    result['warnings'].append(f"Title uses generic phrase: '{intro}'")

        # Check introduction
        intro_lower = article.introduction.lower() if article.introduction else ""
        generic_intros = ["welcome to", "in the heart of", "nestled in", "are you looking for"]
        for intro in generic_intros:
            if intro in intro_lower:
                result['warnings'].append(f"Introduction uses generic phrase: '{intro}'")

        # Check for repeated destination name
        if article.destination and article.introduction:
            dest_count = article.introduction.lower().count(article.destination.lower())
            if dest_count > 3:
                result['warnings'].append(f"Destination name repeated {dest_count} times in introduction")

    @staticmethod
    def _validate_anti_hallucination(article: TravelArticle, result: Dict[str, Any]) -> None:
        """Validate anti-hallucination compliance"""
        # Check for unsafe phrases in text fields
        text_fields = [
            article.title, article.introduction, article.conclusion,
            article.best_time_to_visit, article.how_to_get_there
        ]

        for field in text_fields:
            if field:
                for phrase in ArticleValidator.UNSAFE_PHRASES:
                    if phrase.lower() in field.lower():
                        result['warnings'].append(f"Unsafe phrase found: '{phrase}' in field")

        # Check activities and locations for unsafe phrases
        for activity in (article.best_things_to_do or []):
            for phrase in ArticleValidator.UNSAFE_PHRASES:
                if phrase.lower() in (activity.description or "").lower() or phrase.lower() in (activity.why_important or "").lower():
                    result['warnings'].append(f"Unsafe phrase found: '{phrase}' in activity: {activity.name}")

        for location in (article.best_places_to_visit or []):
            for phrase in ArticleValidator.UNSAFE_PHRASES:
                if phrase.lower() in (location.description or "").lower():
                    result['warnings'].append(f"Unsafe phrase found: '{phrase}' in location: {location.name}")

        # Check sources for valid URLs
        for source in (article.sources or []):
            if source.url and not ArticleValidator._is_valid_url(source.url):
                result['errors'].append(f"Invalid source URL: {source.url}")

    @staticmethod
    def _validate_seo(article: TravelArticle, result: Dict[str, Any]) -> None:
        """Validate SEO metadata"""
        if not article.seo:
            result['errors'].append("Missing SEO metadata")
            return

        if not article.seo.title:
            result['errors'].append("Missing SEO title")

        if not article.seo.meta_description:
            result['errors'].append("Missing meta description")

        if not article.seo.slug:
            result['errors'].append("Missing slug")

        if not article.seo.primary_keyword:
            result['errors'].append("Missing primary keyword")

        # Check meta description length (150-160 chars optimal)
        if article.seo.meta_description:
            desc_len = len(article.seo.meta_description)
            if desc_len > 160:
                result['warnings'].append(f"Meta description too long: {desc_len} chars")
            elif desc_len < 120:
                result['warnings'].append(f"Meta description too short: {desc_len} chars")

    @staticmethod
    def _is_valid_url(url: str) -> bool:
        """Check if URL is valid format"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
        except:
            return False

    @staticmethod
    def save_validation_report(article: TravelArticle, report_path: str) -> None:
        """Save validation report to file"""
        validation = ArticleValidator.validate(article)

        report = {
            'article_id': article.id,
            'destination': article.destination,
            'valid': validation['valid'],
            'errors': validation['errors'],
            'warnings': validation['warnings'],
            'section_count': validation['section_count'],
            'content_length': validation['content_length'],
            'generated_at': datetime.now().isoformat()
        }

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
