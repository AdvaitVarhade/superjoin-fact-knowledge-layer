from typing import Optional
from pydantic import BaseModel

class Period(BaseModel):
    period_id: str  # e.g., 'FY24', 'Q1_FY24', '2024-25', 'FY23'
    label: str
    period_type: str  # 'FiscalYear', 'Quarter', 'CalendarYear', 'PointInTime'
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_restated: bool = False
    restatement_note: Optional[str] = None
