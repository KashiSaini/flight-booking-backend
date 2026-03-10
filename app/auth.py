from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.dependencies import get_current_logged_user, get_admin_user
from app.redis_client import redis_client
from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse, LoginRequest
from app.utils import hash_password, verify_password, create_access_token, create_refresh_token
import os
from dotenv import load_dotenv

load_dotenv()
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(User).where(User.email == user.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        name=user.name,
        email=user.email,
        password=hash_password(user.password),
        is_admin=(user.email == ADMIN_EMAIL)
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


""" {
  "name": "nishant",
  "email": "nishant@admin.com",
  "password": "1234"
} """

@router.post("/login")
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    payload = {
    "sub": str(user.id),
    "email": user.email,
    "is_admin": user.is_admin
    }

    access_token = create_access_token(payload)
    refresh_token = create_refresh_token(payload)

    await redis_client.setex(
    f"refresh_token:{user.id}",
    60 * 60 * 24 * 7,
    refresh_token
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

from fastapi import Body
from app.utils import decode_token

@router.post("/refresh")
async def refresh_token(refresh_token: str = Body(...)):
    try:
        payload = decode_token(refresh_token)

        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")

        user_id = payload.get("sub")

        stored_token = await redis_client.get(f"refresh_token:{user_id}")

        if stored_token != refresh_token:
            raise HTTPException(status_code=401, detail="Token revoked")

        new_access_token = create_access_token({
            "sub": payload["sub"],
            "email": payload["email"],
            "is_admin": payload["is_admin"]
        })

        return {"access_token": new_access_token, "token_type": "bearer"}

    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
@router.post("/logout")
async def logout(current_user: User = Depends(get_current_logged_user)):
    await redis_client.delete(f"refresh_token:{current_user.id}")
    return {"message": "Logged out successfully"}


@router.post("/promote-admin/{user_id}", response_model=UserResponse)
async def promote_to_admin(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Promote a user to admin status. Only admins can perform this action.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()

    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    if target_user.is_admin:
        raise HTTPException(status_code=400, detail="User is already an admin")

    target_user.is_admin = True
    await db.commit()
    await db.refresh(target_user)

    return target_user


@router.get("/get_users", response_model=list[UserResponse])
async def get_users(current_user: User = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users