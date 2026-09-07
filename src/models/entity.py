from typing import List, Optional
from pydantic import BaseModel, Field

class Entity(BaseModel):
    entity_id: str
    name: str
    entity_type: str = "Company"  # Company, Economy, Institution, Segment
    aliases: List[str] = Field(default_factory=list)
    description: Optional[str] = None
