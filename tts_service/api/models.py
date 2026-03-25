from pydantic import BaseModel, Field
from typing import Literal

class TTSRequest(BaseModel):
    avaterId: int = Field(default=0, example=1)
    messageId: str = Field(..., example="msg_001")
    text: str = Field(..., example="Hello world")
    language: Literal["en", "ar"]
    gender: Literal["male", "female"] = "female"

class TTSResponse(BaseModel):
    messageId: str
    audio_base64: str
    content_type: str = "wav"
