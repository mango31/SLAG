from typing import List, Union, Optional
from pydantic import BaseModel

class Location(BaseModel):
    name: str
    type: str
    description: str
    significance: Optional[Union[str, List[str]]] = None
    features: List[str]

    def get_significance(self) -> str:
        """Get significance as a string regardless of input type"""
        if isinstance(self.significance, list):
            return "; ".join(self.significance)
        return self.significance or "" 