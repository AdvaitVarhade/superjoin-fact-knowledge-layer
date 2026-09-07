from typing import Optional
from pydantic import BaseModel

class Entity(BaseModel):
    entity_id: str  # e.g., 'delhivery_limited', 'apple_inc', 'tesla_inc', 'rbi'
    name: str
    sector: Optional[str] = None
    country: Optional[str] = 'IN'
    description: Optional[str] = None
