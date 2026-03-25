from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

router = APIRouter()

# Mocked dependency checks (replace with actual checks)
def check_llm():
    return True  # Replace with real health logic

def check_database():
    return True  # Replace with real DB connection test

def check_tts_stt():
    return True  # Optional, non-critical

@router.get("/health")
async def health_check():
    llm_healthy = check_llm()
    db_healthy = check_database()
    tts_stt_healthy = check_tts_stt()

    critical_ok = llm_healthy and db_healthy

    status_code = status.HTTP_200_OK if critical_ok else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ok" if critical_ok else "unavailable",
            "services": {
                "llm": "ok" if llm_healthy else "down",
                "database": "ok" if db_healthy else "down",
                "tts_stt": "ok" if tts_stt_healthy else "down"
            }
        }
    )
