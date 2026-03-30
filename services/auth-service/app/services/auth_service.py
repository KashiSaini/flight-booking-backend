from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.core.config import ADMIN_EMAIL
from shared.db.redis import redis_client
from shared.models.user import User
from shared.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.schemas.auth import LoginRequest, UserCreate

async def register_user(user: UserCreate, db: AsyncSession):
    result = await db.execute(select(User).where(User.email == user.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        name=user.name,
        email=user.email,
        password=hash_password(user.password),
        is_admin=(str(user.email).lower() == str(ADMIN_EMAIL).lower()),
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

async def login_user(data: LoginRequest, db: AsyncSession):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    payload = {"sub": str(user.id), "email": user.email, "is_admin": user.is_admin}
    access_token = create_access_token(payload)
    refresh_token = create_refresh_token(payload)

    await redis_client.setex(f"refresh_token:{user.id}", 60 * 60 * 24 * 7, refresh_token)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

async def refresh_access_token(refresh_token: str):
    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")

        user_id = payload.get("sub")
        stored_token = await redis_client.get(f"refresh_token:{user_id}")

        if stored_token != refresh_token:
            raise HTTPException(status_code=401, detail="Token revoked")

        new_access_token = create_access_token(
            {
                "sub": payload["sub"],
                "email": payload["email"],
                "is_admin": payload["is_admin"],
            }
        )
        return {"access_token": new_access_token, "token_type": "bearer"}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

async def logout_user(current_user: User, token: str):
    await redis_client.delete(f"refresh_token:{current_user.id}")
    await redis_client.setex(f"blacklist:{token}", 1800, "true")
    return {"message": "Logged out successfully and access token revoked"}

async def promote_user_to_admin(user_id: int, db: AsyncSession):
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

async def get_all_users(db: AsyncSession):
    result = await db.execute(select(User))
    return result.scalars().all()
