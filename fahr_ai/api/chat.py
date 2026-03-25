from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import ValidationError
from orchestrator.orchestrator import Orchestrator
from orchestrator.mock_orchestrator import MockOrchestrator
from datetime import datetime
from typing import Optional, Dict, List, Any
import uuid
import asyncio
import json
import base64
from api.models import *

router = APIRouter()
# Call orchestrator
orchestrator = Orchestrator()

def transform_orchestrator_output(orchestrator_output: List[Dict], avatarId: int, conversationId: int) -> ResponseData:
    """
    Transform orchestrator output to match the expected ResponseData model
    """
    # Initialize with default values
    response_data = {
        "conversationId": conversationId,
        "messageId": int(datetime.now().timestamp()),  # Generate unique message ID
        "widgetType": "chat",
        "switchAvatar": False, 
        "avatarId": avatarId,  
        "textData": "",
        "voiceData": None,
        "widgetData": None,
        "faQsData": [],
        "referenceData": []
    }
    
    # Process each output type from orchestrator
    for output in orchestrator_output:
        output_type = output.get("type", "")
        
        if output_type == "text":
            # Extract text data
            response_data["textData"] = output.get("data", "")
            
            # Extract reference data if available
            if "referenceData" in output and output["referenceData"]:
                response_data["referenceData"] = output["referenceData"]
            
            # Extract FAQs data if available
            if "faQsData" in output and output["faQsData"]:
                response_data["faQsData"] = output["faQsData"]
                
        elif output_type == "voice":
            # Extract voice data
            voice_data = output.get("data", {})
            if isinstance(voice_data, dict):
                voice_obj = VoiceData(
                    audioBase64=voice_data.get("audio_base64", ""),
                    contentType=voice_data.get("content_type", "audio/wav")
                )
                response_data["voiceData"] = [voice_obj]
            elif isinstance(voice_data, list):
                # If already a list of voice data
                voice_objs = []
                for vd in voice_data:
                    if isinstance(vd, dict):
                        voice_objs.append(VoiceData(
                            audioBase64=vd.get("audio_base64", ""),
                            contentType=vd.get("content_type", "audio/wav")
                        ))
                response_data["voiceData"] = voice_objs
        
        elif output_type == "widget":
            # Handle widget data as list of WidgetData objects
            widget_data = output.get("data", {})
            if isinstance(widget_data, list):
                # If already a list of widget data
                widget_objs = []
                for wd in widget_data:
                    if isinstance(wd, dict):
                        widget_objs.append(WidgetData(
                            widgetType=wd.get("widgetType", "generic"),
                            data=[wd.get("data", "")]
                        ))
                response_data["widgetData"] = widget_objs
        
        # Extract avatar switching if available
        elif output_type == "avatar":
            avatar_data = output.get("data", {})
            if isinstance(avatar_data, dict):
                response_data["switchAvatar"] = avatar_data.get("switch", False)
                response_data["avatarId"] = avatar_data.get("avatarId", 1)
    
    # Create and return ResponseData model
    return ResponseData(**response_data)

def create_api_response(success: bool = True, message: str = "", status_code: int = 200, 
                       data: ResponseData = None, errors: List[str] = None) -> ChatResponseModel:
    """
    Create standardized API response using ChatResponseModel
    """
    return ChatResponseModel(
        success=success,
        message=message,
        statusCode=status_code,
        data=data,
        errors=errors or []
    )

async def mock_llm_streamer(prompt: str, rag_context: Optional[str] = None):
    """Simulate streaming output from a language model"""
    response = [
        ChatResponseChunk(type="text", data=f"Response to: {prompt}").dict(),
        ChatResponseChunk(type="text", data=f"Context: {rag_context or 'None'}").dict()
    ]
    for chunk in response:
        yield f"data: {json.dumps(chunk)}\n\n"
        await asyncio.sleep(0.05)

def problem_response(status_code: int, detail: str, instance: str = "/chat") -> JSONResponse:
    """Create problem response using ChatResponseModel"""
    response_model = ChatResponseModel(
        success=False,
        message={
            400: "Bad Request",
            401: "Authentication Failed",
            403: "Forbidden", 
            422: "Validation Error",
            500: "Internal Server Error"
        }.get(status_code, "Error"),
        statusCode=status_code,
        data=None,
        errors=[detail]
    )
    
    return JSONResponse(
        status_code=status_code,
        content=response_model.dict()
    )

@router.post("/chat", status_code=status.HTTP_200_OK)
async def chat_endpoint(payload: ChatRequest):
    """
    Endpoint to handle chat messages and orchestrate responses
    """
    print("//////////////////////////")
    print("recieved payload = ", payload)
    print("//////////////////////////")
    try:
        # Extract prompt/message
        prompt = payload.conversationMessage
        if not prompt:
            return problem_response(400, "conversationMessage is required")

        # Get or create session
        session_id = str(payload.conversationId)

        # Convert to dictionary and enrich
        data = payload.dict()
        data["sessionId"] = session_id
        data["prompt"] = prompt
        data["role"] = "admin"

        # API configuration for conversation history
        api_config = {
            "base_url": "http://10.254.115.17:8090",  # Your gateway URL
            "headers": {
                "Content-Type": "application/json"
            },
            "timeout": 30
        }

        # Get orchestrator output and transform it
        try:
            orchestrator_output = await orchestrator.run(user_input=data, api_config=api_config)
            
            # Transform orchestrator output to match expected response structure
            transformed_data = transform_orchestrator_output(orchestrator_output, 
                                                            avatarId=payload.avatarId,
                                                            conversationId=payload.conversationId
                                                             )
            
            # Create final API response using ChatResponseModel
            api_response = create_api_response(
                success=True,
                message="Chat response generated successfully",
                status_code=200,
                data=transformed_data
            )
            
            return JSONResponse(content=api_response.dict())
            
        except ValidationError as ve:
            return problem_response(422, f"Validation error: {str(ve)}")
        except Exception as orch_error:
            return problem_response(500, f"Orchestrator error: {str(orch_error)}")

    except PermissionError:
        return problem_response(403, "Insufficient permissions")
    except KeyError as ke:
        return problem_response(400, f"Missing key: {str(ke)}")
    except HTTPException as http_exc:
        return problem_response(http_exc.status_code, http_exc.detail)
    except Exception as e:
        return problem_response(500, f"Unexpected error: {str(e)}")

@router.get("/session/{session_id}")
async def get_session_endpoint(session_id: str):
    """Get session information"""
    session = get_session(session_id)
    if not session:
        return problem_response(404, "Session not found")
    
    # Return session data using ChatResponseModel
    api_response = ChatResponseModel(
        success=True,
        message="Session retrieved successfully",
        statusCode=200,
        data=session,  # Session data as string/dict for this case
        errors=[]
    )
    
    return JSONResponse(content=api_response.dict())