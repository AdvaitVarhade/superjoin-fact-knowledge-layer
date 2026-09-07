from typing import Optional
from pydantic import BaseModel, Field

class Period(BaseModel):
    period_id: str
    label: str  # e.g. "FY24", "Q4 FY24", "2024-25"
    period_type: str = "FiscalYear"  # FiscalYear, Quarter, CalendarYear, PointInTime
    start_date: Optional[str] = None  # ISO format "YYYY-MM-DD"
    end_date: Optional[str] = None    # ISO format "YYYY-MM-DD"
    is_restated: bool = False
