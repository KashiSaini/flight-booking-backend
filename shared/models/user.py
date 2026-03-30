from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from shared.db.postgres import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)

    bookings = relationship("Booking", back_populates="user", cascade="all, delete-orphan")
