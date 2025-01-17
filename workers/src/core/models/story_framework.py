from typing import List, Dict, Optional
from .story_bible import ExtensibleModel
from datetime import datetime

class StoryBeat(ExtensibleModel):
    name: str
    description: str
    characters_involved: List[str]
    location: str

class StoryArc(ExtensibleModel):
    name: str
    description: str
    beats: List[StoryBeat]
    themes: List[str]
    character_arcs: Dict[str, str]

class StoryFramework(ExtensibleModel):
    title: str
    genre: str
    created: datetime = datetime.now()
    main_conflict: str
    central_theme: str
    arcs: List[StoryArc] 