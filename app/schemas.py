from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# -------- USER --------
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


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


# -------- BOOKING --------
class BookingResponse(BaseModel):
    id: int
    user_id: int
    flight_id: int
    seat_number: Optional[str] = None
    passenger_name: Optional[str] = None
    destination: Optional[str] = None
    price_paid: Optional[float] = None
    seat_type: Optional[str] = None
    booking_reference: Optional[str] = None
    status: Optional[str] = None
    booked_at: Optional[datetime] = None

    class Config:
        from_attributes = True


from typing import Literal

class PassengerBooking(BaseModel):
    passenger_name: str
    seat_type: Literal["business", "premium", "economy"]
    destination: str
    seat_number: str


class BookingCreate(BaseModel):
    passengers: list[PassengerBooking]


# -------- SEAT --------
class SeatResponse(BaseModel):
    id: int
    flight_id: int
    seat_number: str
    seat_type: str
    is_booked: bool

    class Config:
        from_attributes = True


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

#---------- Mongodb Schemas --------

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class ActivityLogCreate(BaseModel):
    user_id: int
    action: str  # e.g., "USER_LOGIN", "SEARCH_FLIGHTS", "BOOKED_JET"
    details: Optional[Dict[str, Any]] = None  # Flexible dictionary for extra info
    timestamp: datetime = Field(default_factory=datetime.utcnow)

