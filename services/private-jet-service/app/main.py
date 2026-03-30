from fastapi import FastAPI
from app.routers.private_jets import privatejet_router

app = FastAPI(title="Private Jet Service")

@app.get("/")
async def root():
    return {"message": "Private Jet Service Running"}

app.include_router(privatejet_router)
