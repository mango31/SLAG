from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
from pathlib import Path

class Story(BaseModel):
    title: str
    author: str = "AI Story Engine"
    genre: str
    content: str
    word_count: int
    framework_id: str  # reference to framework used
    bible_id: str     # reference to story bible used 
    file_paths: Optional[Dict[str, str]] = None
    created: datetime = datetime.now()

    def model_dump(self, **kwargs):
        """Custom dump method to ensure proper serialization"""
        data = super().model_dump(**kwargs)
        # Convert datetime to string
        data['created'] = self.created.isoformat()
        return data

    def to_dict(self) -> dict:
        """Convert to a plain dictionary for JSON serialization"""
        return {
            "title": self.title,
            "author": self.author,
            "genre": self.genre,
            "content": self.content,
            "word_count": self.word_count,
            "framework_id": self.framework_id,
            "bible_id": self.bible_id,
            "file_paths": self.file_paths,
            "created": self.created.isoformat()
        } 