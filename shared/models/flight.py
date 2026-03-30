from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship
from shared.db.postgres import Base

class Flight(Base):
    __tablename__ = "flights"

    id = Column(Integer, primary_key=True)
    source = Column(String)
    destination = Column(String)
    stops = Column(JSON, default=None)
    segment_prices = Column(JSON, default=None)

    business_price = Column(Float, nullable=True)
    premium_price = Column(Float, nullable=True)
    economy_price = Column(Float, nullable=True)

    business_seats = Column(Integer, default=0)
    premium_seats = Column(Integer, default=0)
    economy_seats = Column(Integer, default=0)

    departure_time = Column(DateTime, nullable=True)
    arrival_time = Column(DateTime, nullable=True)
    airline = Column(String, nullable=True)

    seats = relationship("Seat", back_populates="flight", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="flight")

class Seat(Base):
    __tablename__ = "seats"

    id = Column(Integer, primary_key=True)
    flight_id = Column(Integer, ForeignKey("flights.id"))
    seat_number = Column(String, nullable=False)
    seat_type = Column(String, nullable=False)
    is_booked = Column(Boolean, default=False)

    flight = relationship("Flight", back_populates="seats")
    bookings = relationship("Booking", back_populates="seat")
