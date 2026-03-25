from fastapi import FastAPI
from api.routers import router

app = FastAPI(title="Text to Speech Service", version="1.0.0")

@app.get("/health")
def health_check():
    return {"status": "healthy"}

app.include_router(router, prefix="/api/tts")
