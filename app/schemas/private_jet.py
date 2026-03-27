from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# -------- PRIVATE JET --------
class PrivateJetCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price_per_hour: float
    available_from: Optional[datetime] = None
    available_to: Optional[datetime] = None


class PrivateJetResponse(BaseModel):
    id: int
    owner_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    price_per_hour: float
    is_available: bool
    available_from: Optional[datetime] = None
    available_to: Optional[datetime] = None

    class Config:
        from_attributes = True


class PrivateJetBookingCreate(BaseModel):
    start_time: datetime
    end_time: datetime


class PrivateJetBookingResponse(BaseModel):
    id: int
    user_id: int
    private_jet_id: int
    start_time: datetime
    end_time: datetime
    price_paid: Optional[float] = None
    status: Optional[str] = None
    booked_at: Optional[datetime] = None

    class Config:
        from_attributes = True