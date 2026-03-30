from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

class PrivateJetCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price_per_hour: float
    is_available: bool = True
    available_from: Optional[datetime] = None
    available_to: Optional[datetime] = None

class PrivateJetResponse(BaseModel):
    id: int
    owner_id: int | None = None
    name: str
    description: str | None = None
    price_per_hour: float
    is_available: bool
    available_from: datetime | None = None
    available_to: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

class PrivateJetBookingCreate(BaseModel):
    start_time: datetime
    end_time: datetime

class PrivateJetBookingResponse(BaseModel):
    id: int
    user_id: int
    private_jet_id: int
    start_time: datetime
    end_time: datetime
    price_paid: float | None = None
    status: str
    booked_at: datetime

    model_config = ConfigDict(from_attributes=True)
