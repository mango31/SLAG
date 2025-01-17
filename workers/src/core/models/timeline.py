from typing import Union, Dict, Any
from pydantic import BaseModel

class TimelineEvent(BaseModel):
    year: str
    event: Union[str, Dict[str, Any]]  # Accept either string or structured event data
    impact: str

    def get_event_text(self) -> str:
        """Get event as a string regardless of input type"""
        if isinstance(self.event, dict):
            return self.event.get('description', str(self.event))
        return self.event 