from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    password = Column(String, nullable=False)

    is_admin = Column(Boolean, default=False)

    bookings = relationship("Booking",back_populates="user",cascade="all, delete-orphan")

class Flight(Base):
    __tablename__ = "flights"

    id = Column(Integer, primary_key=True)
    source = Column(String)
    destination = Column(String)
    stops = Column(JSON, default=None)  # List of intermediate stop locations
    segment_prices = Column(JSON, default=None)  # List of per-segment pricing dicts

    # Prices per class
    business_price = Column(Float, nullable=True)
    premium_price = Column(Float, nullable=True)
    economy_price = Column(Float, nullable=True)

    # Seat counts per class
    business_seats = Column(Integer, default=0)
    premium_seats = Column(Integer, default=0)
    economy_seats = Column(Integer, default=0)

    departure_time = Column(DateTime, nullable=True)
    arrival_time = Column(DateTime, nullable=True)
    airline = Column(String, nullable=True)

    # relationship to seat records
    seats = relationship("Seat", back_populates="flight", cascade="all, delete-orphan")

    bookings = relationship("Booking", back_populates="flight")


class Seat(Base):
    __tablename__ = "seats"

    id = Column(Integer, primary_key=True)
    flight_id = Column(Integer, ForeignKey("flights.id"))
    seat_number = Column(String, nullable=False)
    seat_type = Column(String, nullable=False)  # business / premium / economy
    is_booked = Column(Boolean, default=False)

    flight = relationship("Flight", back_populates="seats")
    bookings = relationship("Booking", back_populates="seat")


class PrivateJet(Base):
    __tablename__ = "private_jets"

    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    price_per_hour = Column(Float, nullable=False)
    is_available = Column(Boolean, default=True)
    available_from = Column(DateTime, nullable=True)
    available_to = Column(DateTime, nullable=True)

    bookings = relationship("PrivateJetBooking", back_populates="private_jet", cascade="all, delete-orphan")


class PrivateJetBooking(Base):
    __tablename__ = "private_jet_bookings"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    private_jet_id = Column(Integer, ForeignKey("private_jets.id"))

    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    price_paid = Column(Float, nullable=True)
    status = Column(String, default="confirmed")
    booked_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    private_jet = relationship("PrivateJet", back_populates="bookings")


#     id = Column(Integer, primary_key=True)



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

