from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


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