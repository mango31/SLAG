from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Extra
from src.core.utils.logging_config import setup_logging
from .location import Location  # Make sure we're importing our updated Location model
from .timeline import TimelineEvent
from datetime import datetime

# Initialize logger
logger = setup_logging("story_bible", "story_bible.log")

# Make base models extensible
class ExtensibleModel(BaseModel):
    model_config = {
        'extra': 'allow',
        'arbitrary_types_allowed': True
    }

    def model_dump(self, **kwargs):
        """Custom dump method to ensure proper serialization"""
        data = super().model_dump(**kwargs)
        # Convert any nested models to dicts
        for key, value in data.items():
            if isinstance(value, list):
                data[key] = [
                    item.model_dump() if isinstance(item, BaseModel) else item 
                    for item in value
                ]
            elif isinstance(value, datetime):
                data[key] = value.isoformat()  # Convert datetime to ISO format string
        return data

class Universe(ExtensibleModel):
    setting: str
    era: str
    environment: Optional[Dict[str, Any]] = None
    infrastructure: Optional[Dict[str, Any]] = None

class Character(ExtensibleModel):
    name: str
    role: str
    description: str
    traits: Optional[List[str]] = None
    background: Optional[str] = None
    relationships: Optional[Dict[str, Union[str, Dict[str, str]]]] = None  # Allow both string and dict relationships
    arc: Optional[Dict[str, Any]] = None

class Location(ExtensibleModel):
    name: str
    description: str
    significance: Optional[Union[str, List[str]]] = None
    features: Optional[List[str]] = None
    hazards: Optional[List[str]] = None
    infrastructure: Optional[Dict[str, Any]] = None

    def get_significance(self) -> str:
        """Get significance as a string if needed"""
        if isinstance(self.significance, list):
            return "; ".join(self.significance)
        return self.significance or ""

class Faction(ExtensibleModel):
    name: str
    description: str
    goals: Optional[List[str]] = None
    relationships: Optional[Dict[str, str]] = None
    resources: Optional[Dict[str, Any]] = None
    territory: Optional[List[str]] = None

class Technology(ExtensibleModel):
    name: str
    description: str
    limitations: Optional[List[str]] = None
    requirements: Optional[Dict[str, Any]] = None
    risks: Optional[List[str]] = None
    development_stage: Optional[str] = None

class TimelineEvent(BaseModel):
    year: str
    event: str
    details: Optional[str] = None
    impact: Optional[str] = None
    key_figures: Optional[List[str]] = None

class SocialStructure(ExtensibleModel):
    governance: Dict[str, Any]
    economy: Dict[str, Any]
    culture: Dict[str, Any]
    education: Optional[Dict[str, Any]] = None
    healthcare: Optional[Dict[str, Any]] = None

class StoryBible(ExtensibleModel):
    title: str
    genre: str
    created: datetime = datetime.now()
    universe: Dict[str, str]
    characters: List[Character]
    locations: List[Location]
    factions: List[Faction]
    technology: List[Technology]
    timeline: Dict[str, List[TimelineEvent]]
    themes: List[str]
    notes: List[str]
    social_structure: Optional[SocialStructure] = None
    infrastructure: Optional[Dict[str, Any]] = None
    environmental_systems: Optional[Dict[str, Any]] = None
    resource_management: Optional[Dict[str, Any]] = None
    transportation_network: Optional[Dict[str, Any]] = None
    
    def add_expansion(self, expansion: Dict[str, Any]) -> None:
        """Merge expansion content into existing bible"""
        # Convert any timeline events before merging
        expansion = self.convert_timeline_events(expansion)
        
        # ... rest of merge logic ...

    @classmethod
    def convert_timeline_events(cls, data: dict) -> dict:
        """Convert timeline dictionary events to TimelineEvent objects"""
        if "timeline" in data:
            for period, events in data["timeline"].items():
                if isinstance(events, list):
                    data["timeline"][period] = [
                        TimelineEvent(**event) if isinstance(event, dict) else event
                        for event in events
                    ]
        return data 