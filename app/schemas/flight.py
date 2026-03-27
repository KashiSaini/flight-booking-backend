
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# -------- FLIGHT --------
class FlightCreate(BaseModel):
    source: str
    destination: str
    stops: Optional[list[str]] = None  # List of intermediate stop locations
    # Optional per-segment pricing. Each item should describe a segment between two
    # consecutive route points (from_location -> to_location) and prices per class.
    # Example: {"from_location":"Delhi","to_location":"Jaipur","business":2500,"premium":1800,"economy":900}
    segment_prices: Optional[list[dict]] = None

    business_price: float
    premium_price: float
    economy_price: float

    business_seats: int
    premium_seats: int
    economy_seats: int

    departure_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    airline: Optional[str] = None



class FlightResponse(BaseModel):
    id: int
    source: str
    destination: str
    stops: Optional[list[str]] = None  # List of intermediate stop locations
    segment_prices: Optional[list[dict]] = None

    business_price: Optional[float] = None
    premium_price: Optional[float] = None
    economy_price: Optional[float] = None

    business_seats: Optional[int] = None
    premium_seats: Optional[int] = None
    economy_seats: Optional[int] = None

    departure_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    airline: Optional[str] = None

    class Config:
        from_attributes = True


# -------- SEAT --------
class SeatResponse(BaseModel):
    id: int
    flight_id: int
    seat_number: str
    seat_type: str
    is_booked: bool

    class Config:
        from_attributes = True