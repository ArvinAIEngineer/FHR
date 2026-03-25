from fastapi import APIRouter, HTTPException
from api.models import TTSRequest, TTSResponse
from core.tts_voice import TTSVoiceProcessor

router = APIRouter()
tts_processor = TTSVoiceProcessor()

@router.post("/convert", response_model=TTSResponse)
async def synthesize_audio(payload: TTSRequest):
    result = tts_processor.run(
        text=payload.text,
        avatarId=payload.avaterId
    )
    if result["status"] == "success":
        return TTSResponse(
            messageId=payload.messageId,
            audio_base64=result["output"]["audio_base64"],
            content_type=result["output"]["content_type"]
        )
    else:
        raise HTTPException(status_code=500, detail=result["message"])