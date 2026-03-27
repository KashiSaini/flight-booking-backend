from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.routers.auth import router as auth_router
from app.routers.flights import router as flights_router
from app.routers.bookings import bookings_router
from app.routers.private_jets import privatejet_router
from app.routers.admin import admin_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    return {"Message": "Backend is Working"}


app.include_router(auth_router)
app.include_router(flights_router)
app.include_router(bookings_router)
app.include_router(privatejet_router)
app.include_router(admin_router)


# from contextlib import asynccontextmanager
# from fastapi import FastAPI
# from app import auth, booking, admin

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     yield

# app = FastAPI(lifespan=lifespan,
#               )
# @app.get("/")
# async def root():
#     return {"Message":"Backend is Working"}


# app.include_router(auth.router)
# app.include_router(booking.router)
# app.include_router(booking.bookings_router)
# app.include_router(booking.privatejet_router)
# app.include_router(admin.admin_router)