import sys
# Add the current directory to sys.path
sys.path.append("./")

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager
import logging
from AIAgents.SuggestionAgent import SuggestionService
from langchain_core.language_models import BaseChatModel

# Pydantic models for request/response
class SuggestionRequest(BaseModel):
    """Request model for suggestion generation"""
    messages: List[str] = Field(..., description="List of conversation messages")
    ticket_summaries: Optional[str] = Field(None, description="Optional ticket summaries for context")
    user_id: Optional[str] = Field(None, description="Optional user identifier")
    session_id: Optional[str] = Field(None, description="Optional session identifier")
    
    class Config:
        json_schema_extra = {
            "example": {
                "messages": [
                    "Hello, I need help with my payslip",
                    "I want to check my leave balance"
                ],
                "ticket_summaries": "User has previous tickets about payroll issues",
                "user_id": "user123",
                "session_id": "session456"
            }
        }


class SuggestionInfo(BaseModel):
    """Information about a suggestion"""
    category: str = Field(..., description="Category of the suggestion")
    confidence: float = Field(..., description="Confidence score (0.0-1.0)")
    is_context_based: bool = Field(..., description="Whether suggestion is based on context")


class SuggestionResponse(BaseModel):
    """Response model for suggestion generation"""
    suggestions: List[str] = Field(..., description="List of generated suggestions")
    suggestion_info: Dict[str, SuggestionInfo] = Field(..., description="Additional info about each suggestion")
    status: str = Field(default="success", description="Status of the request")
    message: Optional[str] = Field(None, description="Optional status message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "suggestions": [
                    "Check your latest payslip",
                    "View remaining vacation days",
                    "Submit time off request"
                ],
                "suggestion_info": {
                    "Check your latest payslip": {
                        "category": "HR",
                        "confidence": 0.9,
                        "is_context_based": True
                    }
                },
                "status": "success",
                "message": "Suggestions generated successfully"
            }
        }


class ErrorResponse(BaseModel):
    """Error response model"""
    status: str = Field(default="error", description="Status of the request")
    message: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Optional error code")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "error",
                "message": "Failed to generate suggestions",
                "error_code": "GENERATION_FAILED"
            }
        }


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(default="healthy", description="Service health status")
    service_name: str = Field(..., description="Name of the service")
    version: str = Field(default="1.0.0", description="Service version")


# Global service instance
suggestion_service: Optional[SuggestionService] = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifespan events"""
    # Startup
    logger.info("Starting Suggestion Generation API")
    global suggestion_service
    suggestion_service = SuggestionService(
        config_path="./configs/agents_config.yaml",
        llm_model=None,  # Replace with your LLM model instance
        service_name="SuggestionService"
    )
    logger.info("Service initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Suggestion Generation API")
    suggestion_service = None


# FastAPI app with lifespan
app = FastAPI(
    title="Suggestion Generation API",
    description="API for generating contextual suggestions based on conversation messages",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)


async def get_suggestion_service() -> SuggestionService:
    """Dependency to get the suggestion service instance"""
    global suggestion_service
    if suggestion_service is None:
        raise HTTPException(
            status_code=503,
            detail="Service not initialized. Please try again later."
        )
    return suggestion_service


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        service_name="Suggestion Generation API",
        version="1.0.0"
    )


@app.post(
    "/generate-suggestions",
    response_model=SuggestionResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)
async def generate_suggestions(
    request: SuggestionRequest,
    service: SuggestionService = Depends(get_suggestion_service)
):
    """
    Generate suggestions based on conversation messages
    
    This endpoint analyzes the provided conversation messages and generates
    contextually relevant suggestions for the user.
    
    - **messages**: List of conversation messages to analyze
    - **ticket_summaries**: Optional additional context from support tickets
    - **user_id**: Optional user identifier for logging/analytics
    - **session_id**: Optional session identifier for tracking
    """
    try:
        logger.info(f"Generating suggestions for {len(request.messages)} messages")
        
        # Validate input
        if not request.messages:
            raise HTTPException(
                status_code=400,
                detail="At least one message is required"
            )
        
        # Generate suggestions
        result = await service.generate_suggestions(
            messages=request.messages,
            ticket_summaries=request.ticket_summaries
        )
        
        # Convert suggestion_info to proper format
        suggestion_info_response = {}
        for suggestion, info in result["suggestion_info"].items():
            suggestion_info_response[suggestion] = SuggestionInfo(
                category=info["category"],
                confidence=info["confidence"],
                is_context_based=info["is_context_based"]
            )
        
        return SuggestionResponse(
            suggestions=result["suggestions"],
            suggestion_info=suggestion_info_response,
            status="success",
            message="Suggestions generated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating suggestions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate suggestions: {str(e)}"
        )


@app.get("/service-state", response_model=Dict[str, Any])
async def get_service_state(
    service: SuggestionService = Depends(get_suggestion_service)
):
    """
    Get the current state of the suggestion service
    
    Returns information about the service's current state and configuration.
    """
    try:
        state = service.get_state()
        return {
            "service_name": service.name,
            "state": state,
            "status": "active"
        }
    except Exception as e:
        logger.error(f"Error getting service state: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get service state: {str(e)}"
        )


@app.get("/categories", response_model=Dict[str, List[str]])
async def get_available_categories(
    service: SuggestionService = Depends(get_suggestion_service)
):
    """
    Get all available suggestion categories and their keywords
    
    Returns a dictionary of categories and their associated keywords.
    """
    try:
        return {
            "categories": list(service.default_suggestions.keys()),
            "domain_keywords": service.domain_keywords
        }
    except Exception as e:
        logger.error(f"Error getting categories: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get categories: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.suggestion:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )