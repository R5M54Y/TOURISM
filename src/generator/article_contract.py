"""
Travel Article Content Contract

Standardized contract for generating structured travel articles.
Source of truth for article structure, validation, and generation.

This module defines:
1. The 18 required article sections
2. Data structure and validation rules
3. JSON schema for structured articles
4. Validation functions
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum

class ArticleStatus(str, Enum):
    DRAFT = "draft"
    VALIDATED = "validated"
    PUBLISHED = "published"
    REJECTED = "rejected"

@dataclass
class QuickFact:
    """Quick facts about a destination"""
    destination: str = ""
    country: str = ""
    region: str = ""
    continent: str = ""
    language: str = ""
    currency: str = ""
    timezone: str = ""
    recommended_trip_duration: str = ""
    best_travel_seasons: str = ""
    destination_type: str = ""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuickFact':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

@dataclass
class WhyVisit:
    """Reasons to visit a destination"""
    culture: bool = False
    history: bool = False
    nature: bool = False
    food: bool = False
    architecture: bool = False
    adventure: bool = False
    shopping: bool = False
    nightlife: bool = False
    family_travel: bool = False
    relaxation: bool = False
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WhyVisit':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

@dataclass
class Activity:
    """A travel activity"""
    name: str = ""
    description: str = ""
    why_important: str = ""
    practical_context: str = ""
    estimated_duration: Optional[str] = None
    best_time: Optional[str] = None

@dataclass
class Location:
    """A travel destination location"""
    name: str = ""
    type: str = ""  # landmark, historical site, neighborhood, museum, etc.
    description: str = ""
    best_for: str = ""
    hidden_gem: bool = False

@dataclass
class TravelOption:
    """Transportation or travel option"""
    mode: str = ""  # walking, public transit, train, bus, taxi, etc.
    description: str = ""
    practicality: Dict[str, str] = None  # trip_type: practicality

@dataclass
class Accommodation:
    """Accommodation recommendation by area"""
    area: str = ""
    characteristics: str = ""
    ideal_traveler: str = ""
    transportation_convenience: str = ""
    advantages: str = ""
    potential_drawbacks: str = ""

@dataclass
class FoodItem:
    """Local food recommendation"""
    dish: str = ""
    description: str = ""
    cultural_significance: str = ""
    where_found: str = ""

@dataclass
class BudgetRange:
    """Travel budget breakdown"""
    level: str = ""  # budget, mid-range, premium
    accommodation: str = ""
    food: str = ""
    transportation: str = ""
    attractions: str = ""
    daily_total: str = ""

@dataclass
class ItineraryDay:
    """Suggested itinerary for a specific duration"""
    duration: str = ""  # 1 day, 3 days, 5 days
    day_flow: str = ""
    highlights: str = ""
    practical_notes: str = ""

@dataclass
class LocalTip:
    """Local travel tip"""
    category: str = ""  # etiquette, payment, language, tipping, etc.
    advice: str = ""
    explanation: str = ""

@dataclass
class SafetyInfo:
    """Safety and practical information"""
    emergency_contact: str = ""
    weather_risks: str = ""
    transportation_risks: str = ""
    local_laws: str = ""
    accessibility: str = ""
    connectivity: str = ""
    sim_esim: str = ""
    insurance: str = ""

@dataclass
class FAQ:
    """Frequently asked question"""
    question: str = ""
    answer: str = ""

@dataclass
class Source:
    """Source for factual information"""
    title: str = ""
    url: str = ""
    type: str = ""  # website, book, article, etc.
    accessed_date: str = ""

@dataclass
class SEO:
    """SEO metadata"""
    title: str = ""
    meta_description: str = ""
    slug: str = ""
    primary_keyword: str = ""
    secondary_keywords: List[str] = None
    search_intent: str = ""

@dataclass
class TravelArticle:
    """Complete structured travel article"""
    # Metadata
    id: str = ""
    destination: str = ""
    country: str = ""
    generation_date: str = ""
    version: str = "1.0"
    status: ArticleStatus = ArticleStatus.DRAFT
    
    # Content sections (all 18 required sections)
    title: str = ""
    introduction: str = ""
    quick_facts: QuickFact = None
    why_visit: WhyVisit = None
    best_things_to_do: List[Activity] = None
    best_places_to_visit: List[Location] = None
    best_time_to_visit: str = ""
    how_to_get_there: str = ""
    getting_around: List[TravelOption] = None
    where_to_stay: List[Accommodation] = None
    local_food_to_try: List[FoodItem] = None
    travel_budget: List[BudgetRange] = None
    suggested_itinerary: List[ItineraryDay] = None
    local_travel_tips: List[LocalTip] = None
    safety_practical_info: SafetyInfo = None
    faq: List[FAQ] = None
    conclusion: str = ""
    sources: List[Source] = None
    
    # SEO
    seo: SEO = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization"""
        data = {}
        
        # Simple string attributes
        string_attrs = [
            'id', 'destination', 'country', 'generation_date', 'version', 'status',
            'title', 'introduction', 'conclusion', 'best_time_to_visit', 'how_to_get_there'
        ]
        for attr in string_attrs:
            data[attr] = getattr(self, attr)
        
        # Handle nested objects and complex attributes manually
        if self.quick_facts:
            data['quick_facts'] = self.quick_facts.__dict__
        if self.why_visit:
            data['why_visit'] = self.why_visit.__dict__
        if self.best_things_to_do:
            data['best_things_to_do'] = [a.__dict__ for a in self.best_things_to_do]
        if self.best_places_to_visit:
            data['best_places_to_visit'] = [l.__dict__ for l in self.best_places_to_visit]
        if self.getting_around:
            data['getting_around'] = [t.__dict__ for t in self.getting_around]
        if self.where_to_stay:
            data['where_to_stay'] = [a.__dict__ for a in self.where_to_stay]
        if self.local_food_to_try:
            data['local_food_to_try'] = [f.__dict__ for f in self.local_food_to_try]
        if self.travel_budget:
            data['travel_budget'] = [b.__dict__ for b in self.travel_budget]
        if self.suggested_itinerary:
            data['suggested_itinerary'] = [i.__dict__ for i in self.suggested_itinerary]
        if self.local_travel_tips:
            data['local_travel_tips'] = [t.__dict__ for t in self.local_travel_tips]
        if self.safety_practical_info:
            data['safety_practical_info'] = self.safety_practical_info.__dict__
        if self.faq:
            data['faq'] = [f.__dict__ for f in self.faq]
        if self.sources:
            data['sources'] = [s.__dict__ for s in self.sources]
        if self.seo:
            data['seo'] = self.seo.__dict__
        
        # Handle lists that might contain None/default values
        for key in ['best_things_to_do', 'best_places_to_visit', 'getting_around', 
                   'where_to_stay', 'local_food_to_try', 'travel_budget', 
                   'suggested_itinerary', 'local_travel_tips', 'faq', 'sources']:
            if key in data and not isinstance(data[key], list):
                del data[key]
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TravelArticle':
        """Create TravelArticle from dictionary"""
        # Convert nested dicts to objects
        if 'quick_facts' in data and isinstance(data['quick_facts'], dict):
            data['quick_facts'] = QuickFact.from_dict(data['quick_facts'])
        if 'why_visit' in data and isinstance(data['why_visit'], dict):
            data['why_visit'] = WhyVisit.from_dict(data['why_visit'])
        if 'best_things_to_do' in data and isinstance(data['best_things_to_do'], list):
            data['best_things_to_do'] = [Activity(**item) if isinstance(item, dict) else item for item in data['best_things_to_do']]
        if 'best_places_to_visit' in data and isinstance(data['best_places_to_visit'], list):
            data['best_places_to_visit'] = [Location(**item) if isinstance(item, dict) else item for item in data['best_places_to_visit']]
        if 'getting_around' in data and isinstance(data['getting_around'], list):
            data['getting_around'] = [TravelOption(**item) if isinstance(item, dict) else item for item in data['getting_around']]
        if 'where_to_stay' in data and isinstance(data['where_to_stay'], list):
            data['where_to_stay'] = [Accommodation(**item) if isinstance(item, dict) else item for item in data['where_to_stay']]
        if 'local_food_to_try' in data and isinstance(data['local_food_to_try'], list):
            data['local_food_to_try'] = [FoodItem(**item) if isinstance(item, dict) else item for item in data['local_food_to_try']]
        if 'travel_budget' in data and isinstance(data['travel_budget'], list):
            data['travel_budget'] = [BudgetRange(**item) if isinstance(item, dict) else item for item in data['travel_budget']]
        if 'suggested_itinerary' in data and isinstance(data['suggested_itinerary'], list):
            data['suggested_itinerary'] = [ItineraryDay(**item) if isinstance(item, dict) else item for item in data['suggested_itinerary']]
        if 'local_travel_tips' in data and isinstance(data['local_travel_tips'], list):
            data['local_travel_tips'] = [LocalTip(**item) if isinstance(item, dict) else item for item in data['local_travel_tips']]
        if 'safety_practical_info' in data and isinstance(data['safety_practical_info'], dict):
            data['safety_practical_info'] = SafetyInfo(**data['safety_practical_info'])
        if 'faq' in data and isinstance(data['faq'], list):
            data['faq'] = [FAQ(**item) if isinstance(item, dict) else item for item in data['faq']]
        if 'sources' in data and isinstance(data['sources'], list):
            data['sources'] = [Source(**item) if isinstance(item, dict) else item for item in data['sources']]
        if 'seo' in data and isinstance(data['seo'], dict):
            data['seo'] = SEO(**data['seo'])
            
        # Set default values for None
        data['best_things_to_do'] = data.get('best_things_to_do', [])
        data['best_places_to_visit'] = data.get('best_places_to_visit', [])
        data['getting_around'] = data.get('getting_around', [])
        data['where_to_stay'] = data.get('where_to_stay', [])
        data['local_food_to_try'] = data.get('local_food_to_try', [])
        data['travel_budget'] = data.get('travel_budget', [])
        data['suggested_itinerary'] = data.get('suggested_itinerary', [])
        data['local_travel_tips'] = data.get('local_travel_tips', [])
        data['faq'] = data.get('faq', [])
        data['sources'] = data.get('sources', [])
        data['quick_facts'] = data.get('quick_facts', QuickFact())
        data['why_visit'] = data.get('why_visit', WhyVisit())
        data['safety_practical_info'] = data.get('safety_practical_info', SafetyInfo())
        data['seo'] = data.get('seo', SEO())
        
        return cls(**data)

class ArticleContract:
    """Validation and schema for travel articles"""
    
    # Schema definition for validation
    # The 18 canonical content sections. SEO metadata, the article container, and
    # other metadata are NOT counted as content sections.
    CANONICAL_SECTIONS = [
        'title', 'introduction',
        'quick_facts', 'why_visit', 'best_things_to_do', 'best_places_to_visit',
        'best_time_to_visit', 'how_to_get_there', 'getting_around', 'where_to_stay',
        'local_food_to_try', 'travel_budget', 'suggested_itinerary',
        'local_travel_tips', 'safety_practical_info', 'faq', 'conclusion', 'sources',
    ]
    SCHEMA = {
        'required_fields': [
            'title', 'introduction', 'conclusion'
        ],
        'required_sections': [
            'quick_facts', 'why_visit', 'best_things_to_do',
            'best_places_to_visit', 'best_time_to_visit', 'how_to_get_there',
            'getting_around', 'where_to_stay', 'local_food_to_try',
            'travel_budget', 'suggested_itinerary', 'local_travel_tips',
            'safety_practical_info', 'faq', 'sources'
        ],
        'max_lengths': {
            'title': 60,
            'introduction': 500,
            'conclusion': 300,
            'best_time_to_visit': 300,
            'how_to_get_there': 400,
            'getting_around_description': 200,
            'where_to_stay_description': 500,
            'local_food_description': 200,
            'suggested_itinerary': 1000,
            'faq_answer': 300
        },
        'min_counts': {
            'best_things_to_do': 8,
            'best_places_to_visit': 8,
            'faq': 5
        }
    }
    
    @staticmethod
    def validate_article(article: TravelArticle) -> List[str]:
        """Validate an article against the contract. Returns list of errors."""
        errors = []
        
        # Check required fields
        for field in ArticleContract.SCHEMA['required_fields']:
            if not getattr(article, field):
                errors.append(f"Missing required field: {field}")
        
        # Check required sections are present
        for section in ArticleContract.SCHEMA['required_sections']:
            if not getattr(article, section):
                errors.append(f"Missing required section: {section}")
        
        # Check title length
        if len(article.title) > ArticleContract.SCHEMA['max_lengths']['title']:
            errors.append(f"Title exceeds {ArticleContract.SCHEMA['max_lengths']['title']} characters")
        
        # Check section content lengths
        if article.introduction and len(article.introduction) > ArticleContract.SCHEMA['max_lengths']['introduction']:
            errors.append("Introduction exceeds maximum length")
        
        # Check minimum counts
        things_to_do = article.best_things_to_do or []
        places_to_visit = article.best_places_to_visit or []
        faq_items = article.faq or []

        if len(things_to_do) < ArticleContract.SCHEMA['min_counts']['best_things_to_do']:
            errors.append(f"Must have at least {ArticleContract.SCHEMA['min_counts']['best_things_to_do']} best things to do")

        if len(places_to_visit) < ArticleContract.SCHEMA['min_counts']['best_places_to_visit']:
            errors.append(f"Must have at least {ArticleContract.SCHEMA['min_counts']['best_places_to_visit']} best places to visit")

        if len(faq_items) < ArticleContract.SCHEMA['min_counts']['faq']:
            errors.append(f"Must have at least {ArticleContract.SCHEMA['min_counts']['faq']} FAQ items")

        # Check for duplicate items
        if things_to_do:
            activities = [a.name.lower() for a in things_to_do if a.name]
            duplicates = set([x for x in activities if activities.count(x) > 1])
            if duplicates:
                errors.append(f"Duplicate activities found: {', '.join(duplicates)}")

        if places_to_visit:
            locations = [l.name.lower() for l in places_to_visit if l.name]
            duplicates = set([x for x in locations if locations.count(x) > 1])
            if duplicates:
                errors.append(f"Duplicate locations found: {', '.join(duplicates)}")
        
        return errors
    
    @staticmethod
    def generate_article_id(destination: str, date: datetime = None) -> str:
        """Generate a unique article ID"""
        if date is None:
            date = datetime.now()
        
        # Create ID: destination_slug + date + random_suffix
        destination_slug = re.sub(r'[^a-zA-Z0-9\s]', '', destination).strip().replace(' ', '_').lower()
        date_str = date.strftime('%Y%m%d')
        random_suffix = datetime.now().strftime('%H%M%S')
        
        return f"{destination_slug}_{date_str}_{random_suffix}"
    
    @staticmethod
    def create_default_article(destination_info: Dict[str, str]) -> TravelArticle:
        """Create a skeleton travel article with destination information"""
        # Extract destination info
        destination = destination_info.get('destination', '')
        country = destination_info.get('country', '')
        
        # Generate ID
        article_id = ArticleContract.generate_article_id(destination)
        
        # Create default article with empty sections
        article = TravelArticle(
            id=article_id,
            destination=destination,
            country=country,
            generation_date=datetime.now().isoformat(),
            status=ArticleStatus.DRAFT
        )
        
        return article