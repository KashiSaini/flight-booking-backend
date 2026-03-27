#---------- Mongodb Schemas --------

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class ActivityLogCreate(BaseModel):
    user_id: int
    action: str  # e.g., "USER_LOGIN", "SEARCH_FLIGHTS", "BOOKED_JET"
    details: Optional[Dict[str, Any]] = None  # Flexible dictionary for extra info
    timestamp: datetime = Field(default_factory=datetime.utcnow)