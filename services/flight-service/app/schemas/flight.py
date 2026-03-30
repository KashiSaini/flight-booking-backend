from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict

class SegmentPrice(BaseModel):
    from_location: str
    to_location: str
    business: float
    premium: float
    economy: float

class FlightCreate(BaseModel):
    source: str
    destination: str
    stops: Optional[list[str]] = None
    segment_prices: Optional[list[SegmentPrice | dict[str, Any]]] = None
    business_price: Optional[float] = None
    premium_price: Optional[float] = None
    economy_price: Optional[float] = None
    business_seats: int = 0
    premium_seats: int = 0
    economy_seats: int = 0
    departure_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    airline: Optional[str] = None

class SeatResponse(BaseModel):
    id: int
    flight_id: int
    seat_number: str
    seat_type: str
    is_booked: bool

    model_config = ConfigDict(from_attributes=True)

class FlightResponse(BaseModel):
    id: int
    source: str
    destination: str
    stops: Optional[list[str]] = None
    segment_prices: Optional[list[dict]] = None
    business_price: Optional[float] = None
    premium_price: Optional[float] = None
    economy_price: Optional[float] = None
    business_seats: int
    premium_seats: int
    economy_seats: int
    departure_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    airline: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
