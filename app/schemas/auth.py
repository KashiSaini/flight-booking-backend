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