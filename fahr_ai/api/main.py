from fastapi import FastAPI
from api import chat, health

app = FastAPI(root_path="/chat")

app.include_router(chat.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")