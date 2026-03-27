from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship
from app.db.postgres import Base
from datetime import datetime


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    flight_id = Column(Integer, ForeignKey("flights.id"))

    # new reference to a specific seat
    seat_id = Column(Integer, ForeignKey("seats.id"), nullable=True)
    seat_number = Column(String, nullable=True)  # copy of seat number for easy lookup

    seat_type = Column(String)  # business / premium / economy
    price_paid = Column(Float)

    passenger_name = Column(String, nullable=True)
    destination = Column(String, nullable=True)
    booking_reference = Column(String, unique=True, index=True)
    status = Column(String, default="confirmed")
    booked_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="bookings")
    flight = relationship("Flight", back_populates="bookings")
    seat = relationship("Seat", back_populates="bookings")