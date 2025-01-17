from pydantic import BaseModel
from typing import List, Optional
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
    file_path: Optional[Path] = None 
    created: datetime = datetime.now()  # Timestamp for file naming and tracking 