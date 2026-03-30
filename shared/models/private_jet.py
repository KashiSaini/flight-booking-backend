from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from shared.db.postgres import Base

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
