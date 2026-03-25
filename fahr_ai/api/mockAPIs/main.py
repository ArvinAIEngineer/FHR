from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import yaml
import uvicorn
from datetime import datetime

# Initialize FastAPI app
app = FastAPI(
    title="Bayanati API",
    description="FastAPI implementation of selected Bayanati endpoints",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load mock data from YAML file
def load_mock_data():
    try:
        with open('mock_data.yaml', 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        return {}

mock_data = load_mock_data()

# Pydantic models for requests and responses

# Payslip models
class PayslipRequest(BaseModel):
    i_SESSION_ID: Optional[str] = None
    i_PERSON_ID: int
    i_PERIOD_MONTH: Optional[str] = None
    i_PERIOD_YEAR: Optional[str] = None
    i_LANG: Optional[str] = "US"

class PayslipItem(BaseModel):
    employee_number: Optional[str] = None
    person_id: Optional[str] = None
    full_name: Optional[str] = None
    effectivE_DATE: Optional[str] = None
    perioD_NAME: Optional[str] = None
    element_name: Optional[str] = None
    element_value: Optional[str] = None
    classification_name: Optional[str] = None
    costinG_DEBIT_OR_CREDIT: Optional[str] = None

class PayslipResponse(BaseModel):
    o_PAYSLIP: Optional[List[PayslipItem]] = None
    o_ERROR_CODE: int = 0
    o_ERROR_DESC: Optional[str] = None

# Employee Profile models
class EmployeeProfileRequest(BaseModel):
    i_SESSION_ID: Optional[str] = None
    i_PERSON_ID: int
    i_LANG: Optional[str] = "US"

class EmployeeProfileResponse(BaseModel):
    o_CURSOR_DET: Optional[List[Dict[str, Any]]] = None
    o_ERROR_CODE: int = 0
    o_ERROR_DESC: Optional[str] = None

# Annual Leave Balance models
class AnnualLeaveBalanceRequest(BaseModel):
    i_SESSION_ID: str
    i_ASSIGNMENT_ID: int
    i_EFFECTIVE_DATE: Optional[str] = None

class AnnualLeaveBalanceResponse(BaseModel):
    o_ACCRUED_DAYS: float
    o_TAKEN_DAYS: float
    o_REMAINING_DAYS: float
    o_ERROR_CODE: int = 0
    o_ERROR_DESC: Optional[str] = None

# Profile Completion models
class ProfileCompletionRequest(BaseModel):
    i_SESSION_ID: Optional[str] = None
    i_LANG: Optional[str] = "US"
    i_PERSON_ID: int
    i_YEAR: Optional[str] = None

class ProfileCompletionResponse(BaseModel):
    o_PROFILE_COMPLETION: Optional[List[Dict[str, Any]]] = None
    o_ERROR_CODE: int = 0
    o_ERROR_DESC: Optional[str] = None

# Helper function to get mock data by endpoint and person_id
def get_mock_response(endpoint: str, person_id: int, **kwargs):
    """Get mock response from YAML data"""
    if endpoint not in mock_data:
        return {"error": f"No mock data found for endpoint: {endpoint}"}
    
    # Try to find person-specific data first
    person_data = mock_data[endpoint].get(str(person_id))
    if person_data:
        return person_data
    
    # Fall back to default data
    default_data = mock_data[endpoint].get("default")
    if default_data:
        return default_data
    
    return {"error": f"No mock data found for person_id: {person_id}"}

# API Endpoints

@app.post("/Bayanati/bayanati-api/api/MobileAPI/VIEW_PAYSLIP_PRC", 
          response_model=PayslipResponse,
          tags=["Personal Information"])
async def get_payslip_info(request: PayslipRequest):
    """
    Retrieve Employee Payslip Details
    Returns detailed payslip information for the specified employee.
    """
    try:
        # Get mock data
        mock_response = get_mock_response("payslip", request.i_PERSON_ID)
        
        if "error" in mock_response:
            raise HTTPException(status_code=404, detail=mock_response["error"])
        
        # Convert mock data to PayslipResponse format
        payslip_items = []
        if "o_PAYSLIP" in mock_response:
            for item in mock_response["o_PAYSLIP"]:
                payslip_items.append(PayslipItem(**item))
        
        return PayslipResponse(
            o_PAYSLIP=payslip_items,
            o_ERROR_CODE=mock_response.get("o_ERROR_CODE", 0),
            o_ERROR_DESC=mock_response.get("o_ERROR_DESC")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/Bayanati/bayanati-api/api/MobileAPI/GET_PERSONAL_INFO",
          response_model=EmployeeProfileResponse,
          tags=["Employee Profile"])
async def get_emp_profile(request: EmployeeProfileRequest):
    """
    Get Assignment Information
    Provides information about the employee's current work assignment.
    """
    try:
        # Get mock data
        mock_response = get_mock_response("employee_profile", request.i_PERSON_ID)
        
        if "error" in mock_response:
            raise HTTPException(status_code=404, detail=mock_response["error"])
        
        return EmployeeProfileResponse(
            o_CURSOR_DET=mock_response.get("o_CURSOR_DET"),
            o_ERROR_CODE=mock_response.get("o_ERROR_CODE", 0),
            o_ERROR_DESC=mock_response.get("o_ERROR_DESC")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/Bayanati/bayanati-api/api/MobileAPI/GET_ANN_LEAVE_BAL",
          response_model=AnnualLeaveBalanceResponse,
          tags=["Leave Management"])
async def get_annual_leave_bal(request: AnnualLeaveBalanceRequest):
    """
    Retrieve annual leave balance for an employee
    Returns accrued, taken, and remaining leave days.
    """
    try:
        # Get mock data - use assignment_id as identifier
        mock_response = get_mock_response("annual_leave", request.i_ASSIGNMENT_ID)
        
        if "error" in mock_response:
            raise HTTPException(status_code=404, detail=mock_response["error"])
        
        return AnnualLeaveBalanceResponse(
            o_ACCRUED_DAYS=mock_response.get("o_ACCRUED_DAYS", 0.0),
            o_TAKEN_DAYS=mock_response.get("o_TAKEN_DAYS", 0.0),
            o_REMAINING_DAYS=mock_response.get("o_REMAINING_DAYS", 0.0),
            o_ERROR_CODE=mock_response.get("o_ERROR_CODE", 0),
            o_ERROR_DESC=mock_response.get("o_ERROR_DESC")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/Bayanati/bayanati-api/api/MobileAPI/GET_PROFILE_COMPLETION",
          response_model=ProfileCompletionResponse,
          tags=["Dashboard"])
async def get_profile_completion(request: ProfileCompletionRequest):
    """
    Get Profile Completion
    Returns the completion status of the employee's profile.
    """
    try:
        # Get mock data
        mock_response = get_mock_response("profile_completion", request.i_PERSON_ID)
        
        if "error" in mock_response:
            raise HTTPException(status_code=404, detail=mock_response["error"])
        
        return ProfileCompletionResponse(
            o_PROFILE_COMPLETION=mock_response.get("o_PROFILE_COMPLETION"),
            o_ERROR_CODE=mock_response.get("o_ERROR_CODE", 0),
            o_ERROR_DESC=mock_response.get("o_ERROR_DESC")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Bayanati API FastAPI Implementation",
        "version": "1.0.0",
        "endpoints": [
            "/Bayanati/bayanati-api/api/MobileAPI/VIEW_PAYSLIP_PRC",
            "/Bayanati/bayanati-api/api/MobileAPI/GET_PERSONAL_INFO",
            "/Bayanati/bayanati-api/api/MobileAPI/GET_ANN_LEAVE_BAL",
            "/Bayanati/bayanati-api/api/MobileAPI/GET_PROFILE_COMPLETION"
        ],
        "docs": "/docs"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )