from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr

class PassengerBooking(BaseModel):
    passenger_name: str
    destination: str
    seat_type: str
    seat_number: str

class BookingCreate(BaseModel):
    contact_email: EmailStr | None = None
    passengers: list[PassengerBooking]

class BookingResponse(BaseModel):
    id: int
    user_id: int
    flight_id: int
    seat_id: int | None = None
    seat_number: str | None = None
    seat_type: str
    price_paid: float
    passenger_name: str | None = None
    destination: str | None = None
    booking_reference: str
    status: str
    booked_at: datetime

    model_config = ConfigDict(from_attributes=True)
