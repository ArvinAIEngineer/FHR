import requests
import yaml
from typing import Dict, Any
from langchain_community.agent_toolkits.openapi.toolkit import RequestsToolkit
from langchain_community.utilities.requests import TextRequestsWrapper

from langchain_core.tools import tool, BaseTool
import requests
import inspect

import os
from datetime import datetime
from dotenv import load_dotenv
from urllib.parse import urljoin
import requests
from urllib.parse import urljoin
from workflows import RAGWorkflow
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import messages_from_dict
from AIAgents.chroma_retrival import ChromaRetriever
from langchain_core.messages import HumanMessage


load_dotenv()

base_url = "http://10.254.115.17:8090/Bayanati/bayanati-api"

@tool
def get_emp_profile(i_PERSON_ID: str, i_SESSION_ID: str = "0", i_LANG: str = "US") -> dict:
    """Retrieves detailed personal information of an employee such as name, date of birth, nationality, and other demographic details."""
    
    print(f"Invoking {inspect.currentframe().f_code.co_name} with arguments: {inspect.currentframe().f_locals}")
    
    endpoint = "/api/MobileAPI/GET_PERSONAL_INFO"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID": "0",
        "i_PERSON_ID": i_PERSON_ID,
        "i_LANG": "US"
    }

    response = requests.post(url, headers=headers, json=payload)
    print(f"\n\nAPI Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def get_annual_leave_bal(i_ASSIGNMENT_ID: int, i_SESSION_ID: str = "0", i_CALC_DATE: str = None) -> dict:
    """Fetch employee annual leaves balance. you may use employee profile for assignment id.
     
    Calculation date should be in format DD-MM-YYYY. If not provided, uses today's date. """
    
    # If no date provided, use today's date
    if i_CALC_DATE is None:
        today = datetime.now()
        i_CALC_DATE = today.strftime("%d-%m-%Y")
    else:
        # Validate and convert date format if needed
        try:
            # Try to parse different date formats and convert to DD-MM-YYYY
            if "-" in i_CALC_DATE:
                # Check if it's YYYY-MM-DD format
                if len(i_CALC_DATE.split("-")[0]) == 4:
                    date_obj = datetime.strptime(i_CALC_DATE, "%Y-%m-%d")
                    i_CALC_DATE = date_obj.strftime("%d-%m-%Y")
                # Otherwise assume it's already DD-MM-YYYY
            elif "/" in i_CALC_DATE:
                # Handle DD/MM/YYYY format
                date_obj = datetime.strptime(i_CALC_DATE, "%d/%m/%Y")
                i_CALC_DATE = date_obj.strftime("%d-%m-%Y")
        except ValueError:
            # If date parsing fails, use today's date as fallback
            today = datetime.now()
            i_CALC_DATE = today.strftime("%d-%m-%Y")
    
    endpoint = "/api/MobileAPI/GET_ANN_LEAVE_BAL"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_ASSIGNMENT_ID": i_ASSIGNMENT_ID,
        "i_CALC_DATE": i_CALC_DATE
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}
    
@tool
def get_business_card_details(i_PERSON_ID: int, i_SESSION_ID: str = "0", i_LANG: str = "US") -> dict:
    """
    Retrieves the business card details of an employee.

    Args:
        i_SESSION_ID (str): Session ID of the user.
        i_PERSON_ID (int): Employee's person ID. [Required]
        i_LANG (str): Language code ("US" or "AR").

    Returns:
        dict: Business card details including department, job title, contact info, etc.
    """
    endpoint = "/api/MobileAPI/GET_BUSINESS_CARD_DET"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_PERSON_ID": i_PERSON_ID,
        "i_LANG": i_LANG
    }

    response = requests.post(url, headers=headers, json=payload)
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def get_contracts(i_PERSON_ID: int, i_SESSION_ID: str = "0", i_LANG: str = "US") -> dict:
    """
    Fetches contract details for the employee.

    Args:
        i_SESSION_ID (str): Session identifier.
        i_PERSON_ID (int): Employee person ID. [Required]
        i_LANG (str): Language code ("US" or "AR").

    Returns:
        dict: List of contracts including type, start/end dates, and terms.
    """
    endpoint = "/api/MobileAPI/GET_CONTRACTS"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_PERSON_ID": i_PERSON_ID,
        "i_LANG": i_LANG
    }

    response = requests.post(url, headers=headers, json=payload)
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def get_salary_change_info(i_PERSON_ID: int, i_SESSION_ID: str = "0", i_LANG: str = "US") -> dict:
    """
    Retrieves salary change information for the employee.

    Args:
        i_SESSION_ID (str): User session ID.
        i_PERSON_ID (int): Person ID of the employee. [Required]
        i_LANG (str): Language preference ("US" or "AR").

    Returns:
        dict: Salary change details such as old salary, new salary, change date, and reason.
    """
    endpoint = "/api/MobileAPI/GET_SALARY_DET"  # <-- replace with actual endpoint if different
    url = urljoin(base_url + "/", endpoint.lstrip("/"))

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_PERSON_ID": i_PERSON_ID,
        "i_LANG": i_LANG
    }

    response = requests.post(url, headers=headers, json=payload)

    try:
        return response.json()
    except Exception as e:
        return {
            "error": str(e),
            "status_code": response.status_code,
            "text": response.text
        }

@tool
def get_payslip_info(i_PERSON_ID: int, i_SESSION_ID: str = "0", i_PERIOD_MONTH: str = "06", i_PERIOD_YEAR: str = "2025", i_LANG: str = "US") -> dict:
    """
    Retrieves the payslip information for the employee using the VIEW_PAYSLIP_PRC stored procedure.

    Args:
        i_PERSON_ID (int): Person ID of the employee. [Required]
        i_SESSION_ID (str): Session ID of the user. Defaults to "0".
        i_PERIOD_MONTH (str): Payroll period month (e.g., "06").
        i_PERIOD_YEAR (str): Payroll period year (e.g., "2025").
        i_LANG (str): Language preference ("US" or "AR"). Defaults to "US".

    Returns:
        dict: Contains employee details, earnings and deductions, bank info, payroll elements, 
              total earnings, total deductions, net salary value, and any error information.
    """
    endpoint = "/api/MobileAPI/VIEW_PAYSLIP_PRC"  # Updated to match your procedure
    url = urljoin(base_url + "/", endpoint.lstrip("/"))

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_PERSON_ID": i_PERSON_ID,
        "i_PERIOD_MONTH": i_PERIOD_MONTH,
        "i_PERIOD_YEAR": i_PERIOD_YEAR,
        "i_LANG": i_LANG
    }

    response = requests.post(url, headers=headers, json=payload)

    try:
        return response.json()
    except Exception as e:
        return {
            "error": str(e),
            "status_code": response.status_code,
            "text": response.text
        }
    
@tool
def get_attendance_details(i_PERSON_ID: int, i_DATE: str, i_SESSION_ID: str = "0", i_LANG: str = "US") -> dict:
    """
    Gets the attendance details of the employee for a given date.

    Args:
        i_SESSION_ID (str): Session ID of the requester.
        i_PERSON_ID (int): Person ID of the employee. [Required]
        i_DATE (str): Attendance date in DD-MM-YYYY format.
        i_LANG (str): Language code ("US" or "AR").

    Returns:
        dict: In/Out timings, attendance status, violations (if any).
    """
    endpoint = "/api/MobileAPI/GET_ATTENDANCE_DET"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_PERSON_ID": i_PERSON_ID,
        "i_DATE": i_DATE,
        "i_LANG": i_LANG
    }

    response = requests.post(url, headers=headers, json=payload)
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def get_main_address(i_PERSON_ID: int, i_SESSION_ID: str = "0", i_LANG: str = "US") -> dict:
    """
    Retrieves the employee's main address details.

    Args:
        i_SESSION_ID (str): Session ID.
        i_PERSON_ID (int): Person ID of the employee. [Required]
        i_LANG (str): Language selection.

    Returns:
        dict: Address fields including city, emirate, P.O. box, and phone.
    """
    endpoint = "/api/MobileAPI/GET_MAIN_ADDRESS"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_PERSON_ID": i_PERSON_ID,
        "i_LANG": i_LANG
    }

    response = requests.post(url, headers=headers, json=payload)
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def get_documents(i_PERSON_ID: int, i_SESSION_ID: str = "0", i_LANG: str = "US") -> dict:
    """
    Returns the list of documents related to the employee such as passport copies, Emirates ID, Visa, Family Book, Marriage certificate, driving license and other HR documents. Use GET_DOCUMENT_DETAILS get retrive details of each document type.

    Args:
        i_SESSION_ID (str): Active session token.
        i_PERSON_ID (int): Employee ID. [Required]
        i_LANG (str): Language code.

    Returns:
        dict: Document metadata such as type, upload date, and file name.
    """
    endpoint = "/api/MobileAPI/GET_DOCUMENTS"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_PERSON_ID": i_PERSON_ID,
        "i_LANG": i_LANG
    }

    response = requests.post(url, headers=headers, json=payload)
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def get_award_nominees_for_employee(i_PERSON_ID: int, i_SESSION_ID: str = "0", i_LANG: str = "US") -> dict:
    """
    Returns award nominations where the employee is a nominee. Can
        be filtered by award plan, status, and year.

    Args:
        i_SESSION_ID (str): Session token.
        i_PERSON_ID (int): Employee's person ID. [Required]
        i_LANG (str): Language ("US" or "AR").

    Returns:
        dict: Award title, nomination status, year, and level.
    """
    endpoint = "/api/MobileAPI/GET_AWARD_NOMINEES_FOR_EMP"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_PERSON_ID": i_PERSON_ID,
        "i_LANG": i_LANG
    }

    response = requests.post(url, headers=headers, json=payload)
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}


@tool
def get_crm_tickets(userName: str) -> dict:
    """
    Fetch CRM case information for a given userName from the Bayanati CRM API.
    """

    url = f"http://10.254.115.17:8090/Bayanati/bayanati-api/api/CrmAPI/CaseRetrival?userName={userName}"
    headers = {
        "accept": "*/*"
    }

    response = requests.get(url, headers=headers)

    try:
        return response.json()
    except Exception:
        return {
            "status_code": response.status_code,
            "response_text": response.text
        }

@tool
def load_tools_from_openapi_url(openapi_url: str):
    """
    Load tools from an OpenAPI specification URL.
    
    Args:
        openapi_url (str): The URL to fetch the OpenAPI specification from
        
    Returns:
        dict: A dictionary containing the loaded tools and specifications
    """
    response = requests.get(openapi_url)
    response.raise_for_status()
    # Parse the spec as dict (JSON or YAML)
    try:
        spec_dict = response.json()
    except Exception:
        spec_dict = yaml.safe_load(response.text)

    requests_wrapper = TextRequestsWrapper(headers={})

    toolkit = RequestsToolkit(
        openapi_spec=spec_dict,
        requests_wrapper=requests_wrapper,
        allow_dangerous_requests=True,
    )

    tools = toolkit.get_tools()
    return {tool.name: tool for tool in tools}

@tool
def print_available_apis(openapi_url: str):
    """Print available API endpoints from an OpenAPI specification URL."""
    response = requests.get(openapi_url)
    response.raise_for_status()
    try:
        spec_dict = response.json()
    except Exception:
        spec_dict = yaml.safe_load(response.text)
        
    servers = spec_dict.get("servers", [])
    if servers:
        print(f"Base URL: {servers[0].get('url')}")
    else:
        print("No servers defined in OpenAPI spec.")
    
    paths = spec_dict.get("paths", {})
    if paths:
        print("Available API endpoints:")
        for path, methods in paths.items():
            method_list = ", ".join(methods.keys())
            print(f"{path}  (methods: {method_list})")
    else:
        print("No paths defined in OpenAPI spec.")

# swagger_url = "https://uxuidevapis.fahr.gov.ae/bayanati-api/swagger/v1/swagger.json"
# print_available_apis(swagger_url)


###################################################################################################
@tool
def get_attachment_by_key(i_ATTACHMENT_ID: int, i_SESSION_ID: str = "0", i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/GET_ATTACHMENT_BY_KEY"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_ATTACHMENT_ID": i_ATTACHMENT_ID

    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def delete_attachment_by_key(i_ATTACHMENT_ID: int, i_SESSION_ID: str = "0", i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/DELETE_ATTACHMENT_BY_KEY"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_ATTACHMENT_ID": i_ATTACHMENT_ID

    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def add_attachment(i_TRANSACTION_ID: str ="0",i_FILENAME:str = "0",i_FILE_BLOB:str ="0",i_FILE_TYPE:str="0"
                   ,i_USER:str ="0",i_TRX_TYPE:str="0", i_SESSION_ID: str = "0", i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/ADD_ATTACHMENT"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_TRANSACTION_ID": i_TRANSACTION_ID,
        "i_FILENAME":i_FILENAME,
        "i_FILE_BLOB":i_FILE_BLOB,
        "i_FILE_TYPE":i_FILE_TYPE,
        "i_USER":i_USER,
        "i_TRX_TYPE":i_TRX_TYPE,
        "i_LANG": i_LANG

    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def submit_trx(i_TRANSACTION_ID: str = "0") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/SUBMIT_TRX"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_TRANSACTION_ID": i_TRANSACTION_ID
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def validate_user_login(i_USER_NAME: str="0", i_PASSWORD: str = "0", i_LANG: str = "US", i_DEVICE_NAME:str="0",i_DEVICE_ID: str="0",
                        i_DEVICE_OS: str ="0",i_LATTITUDE:str ="0",i_LONGTITUDE:str ="0") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/VALIDATE_USER_LOGIN"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_USER_NAME": i_USER_NAME,
        "i_PASSWORD": i_PASSWORD,
        "i_LANG": i_LANG,
        "i_DEVICE_NAME":i_DEVICE_NAME,
        "i_DEVICE_ID":i_DEVICE_ID,
        "i_DEVICE_OS":i_DEVICE_OS,
        "i_LATTITUDE":i_LATTITUDE,
        "i_LONGTITUDE":i_LONGTITUDE,

    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def reset_password(i_USER_NAME: str, i_NEW_PASSWORD: str = "0", i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/RESET_PASSWORD"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_USER_NAME": i_USER_NAME,
        "i_NEW_PASSWORD": i_NEW_PASSWORD,
        "i_LANG": i_LANG

    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def user_change_password(i_USER_NAME: str,i_OLD_PASSWORD:str = "0", i_NEW_PASSWORD: str = "0",i_NEW_PASSWORD_2:str="0", i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/USER_CHANGE_PASSWORD"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_USER_NAME": i_USER_NAME,
        "i_OLD_PASSWORD":i_OLD_PASSWORD,
        "i_NEW_PASSWORD": i_NEW_PASSWORD,
        "i_NEW_PASSWORD_2":i_NEW_PASSWORD_2,
        "i_LANG": i_LANG

    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def validate_user_login_v3(i_USER_NAME: str, i_SESSION_ID: str = "0",i_PASSWORD: str = "0", i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/VALIDATE_USER_LOGIN_V3"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_USER_NAME": i_USER_NAME,
        "i_SESSION_ID": i_SESSION_ID,
        "i_PASSWORD": i_PASSWORD,
        "i_LANG": i_LANG

    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def get_award_types(i_SESSION_ID: str, i_PERSON_ID: str = "0", i_LANG: str = "US") -> dict:

    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/GET_AWARD_TYPES"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_PERSON_ID": i_PERSON_ID,
        "i_LANG": i_LANG

    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def view_award_winners(i_SESSION_ID: str,i_AWARD_TYPE:str, i_YEAR: str = "2025", i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/VIEW_AWARD_WINNERS"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_YEAR": i_YEAR,
        "i_AWARD_TYPE":i_AWARD_TYPE
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def get_reward_types(i_SESSION_ID: str, i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/GET_REWARD_TYPES"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_LANG": i_LANG

    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def get_award_actions(i_SESSION_ID: str, i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/GET_AWARD_ACTIONS"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_LANG": i_LANG

    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def submit_award_nomtinees(i_SESSION_ID: str,i_PERSON_ID:int,i_AWARD_PLAN_ID:int,i_MULT_PRP_IDS:int, i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/SUBMIT_AWARD_NOMINEES"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_PERSON_ID":i_PERSON_ID,
        "i_AWARD_PLAN_ID":i_AWARD_PLAN_ID,
        "i_MULT_PRP_IDS":i_MULT_PRP_IDS
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def get_award_nomtinees(i_SESSION_ID: str,i_PERSON_ID:int,i_AWARD_PLAN_ID:int, i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/GET_AWARD_NOMINEES"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_PERSON_ID":i_PERSON_ID,
        "i_AWARD_PLAN_ID":i_AWARD_PLAN_ID

    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def get_award_status(i_SESSION_ID: str, i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/GET_AWARD_STATUS"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_LANG": i_LANG

    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def get_award_plans(i_SESSION_ID: str,i_PERSON_ID:int, i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/GET_AWARD_PLANS"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_PERSON_ID":i_PERSON_ID

    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def get_award_plans_v2(i_SESSION_ID: str,i_ENTITY_CODE:str, i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/GET_AWARD_PLANS_V2"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_ENTITY_CODE":i_ENTITY_CODE
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def get_emp_award_question(i_SESSION_ID:str,i_AWARD_PROP_ID: str, i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/CrmAPI/GET_EMP_AWARD_QUESTIONS"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_AWARD_PROP_ID":i_AWARD_PROP_ID,
        "i_SESSION_ID": i_SESSION_ID,
        "i_LANG": i_LANG,
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def submit_emp_award_justification(i_SESSION_ID: str,i_PERSON_ID:int,i_QUESTION_ID:int,i_JUSTIFICATION:str, i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/SUBMIT_EMP_AWARD_JUSTIFICATION"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_PERSON_ID":i_PERSON_ID,
        "i_QUESTION_ID":i_QUESTION_ID,
        "i_JUSTIFICATION":i_JUSTIFICATION
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def save__award_justification(i_SESSION_ID: str,i_PERSON_ID:int,i_QUESTION_ID:int,i_JUSTIFICATION:str, i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/SAVE_MGR_AWARD_JUSTIFICATION"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_PERSON_ID":i_PERSON_ID,
        "i_QUESTION_ID":i_QUESTION_ID,
        "i_JUSTIFICATION":i_JUSTIFICATION
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def save_emp_award_justification(i_SESSION_ID: str,i_PERSON_ID:int,i_QUESTION_ID:int,i_JUSTIFICATION:str, i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/SAVE_EMP_AWARD_JUSTIFICATION"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_PERSON_ID":i_PERSON_ID,
        "i_QUESTION_ID":i_QUESTION_ID,
        "i_JUSTIFICATION":i_JUSTIFICATION
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def submit_emp_award_justification(i_SESSION_ID: str,i_PERSON_ID:int,i_AWARD_PROP_ID:int,i_COMMENTS:str, i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/SUBMIT_EMP_AWARD_JUSTIFICATION"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_PERSON_ID":i_PERSON_ID,
        "i_AWARD_PROP_ID":i_AWARD_PROP_ID,
        "i_COMMENTS":i_COMMENTS
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def save_mgr_award_justification(i_SESSION_ID: str,i_USER_NAME:str,i_QUESTION_ID:int,i_JUSTIFICATION:str, i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/SAVE_MGR_AWARD_JUSTIFICATION"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_USER_NAME":i_USER_NAME,
        "i_QUESTION_ID":i_QUESTION_ID,
        "i_JUSTIFICATION":i_JUSTIFICATION
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def submit_mgr_award_justification(i_SESSION_ID: str,i_USER_NAME:str,i_AWARD_PROP_ID:int,i_RESPONSE:str,i_COMMENTS:str, i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/SUBMIT_MGR_AWARD_JUSTIFICATION"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_USER_NAME":i_USER_NAME,
        "i_AWARD_PROP_ID":i_AWARD_PROP_ID,
        "i_RESPONSE":i_RESPONSE,
        "i_COMMENTS":i_COMMENTS,
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def get_employee_list(i_SESSION_ID: str,i_ENTITY_CODE:str,i_EMP_LEVEL:str,i_PERSON_ID:int, i_LANG: str = "US") -> dict:
    """Retrieve a list of employees who directly report to me"""

    endpoint = "/api/MobileAPI/GET_EMPLOYEE_LIST"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_ENTITY_CODE":i_ENTITY_CODE,
        "i_EMP_LEVEL":i_EMP_LEVEL,
        "i_PERSON_ID":i_PERSON_ID,
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}


@tool
def get_award_mgr_view(i_PERSON_ID:int, i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/GET_AWARDS_MGR_VIEW"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_PERSON_ID":i_PERSON_ID,
        "i_LANG": i_LANG,
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def rollback_transaction(i_SESSION_ID:str,i_TRANSACTION_ID:int, i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/ROLLBACK_TRANSACTION"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID":i_SESSION_ID,
        "i_TRANSACTION_ID":i_TRANSACTION_ID,
        "i_LANG": i_LANG,
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def get_nominations_monthly(i_SESSION_ID:str,i_ENTITY_CODE:str,i_MONTH:str, i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/GET_NOMINATIONS_MONTHLY"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID":i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_ENTITY_CODE":i_ENTITY_CODE,
        "i_MONTH":i_MONTH,
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def get_award_quest_attachment(i_SESSION_ID:str,i_AWARD_PROP_ID:int, i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/GET_AWARD_QUEST_ATTACHMENT"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID":i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_AWARD_PROP_ID":i_AWARD_PROP_ID,
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def get_award_questions(i_SESSION_ID:str,i_AWARD_CODE:str, i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/GET_AWARD_QUESTIONS"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID":i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_AWARD_PROP_ID":i_AWARD_CODE,
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def get_award_nominees_by_mgr(i_SESSION_ID:str,i_AWARD_CODE:str, i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/GET_AWARD_NOMINEES_BY_MGR"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID":i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_AWARD_PROP_ID":i_AWARD_CODE,
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def get_award_nominees_for_emp(i_SESSION_ID:str,i_PERSON_ID:int,i_AWARD_PLAN_ID:int,i_STATUS:str,i_YEAR:str ,i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/GET_AWARD_NOMINEES_FOR_EMP"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID":i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_PERSON_ID":i_PERSON_ID,
        "i_AWARD_PLAN_ID":i_AWARD_PLAN_ID,
        "i_STATUS":i_STATUS,
        "i_YEAR":i_YEAR

    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def get_award_nominees_by_emp(i_SESSION_ID:str,i_PERSON_ID:int,i_AWARD_PLAN_ID:int,i_STATUS:str ,i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/GET_AWARD_NOMINEES_BY_EMP"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID":i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_PERSON_ID":i_PERSON_ID,
        "i_AWARD_PLAN_ID":i_AWARD_PLAN_ID,
        "i_STATUS":i_STATUS
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}


@tool
def crm_case_retrieval(
    userName: str,
    fromDate: str,
    toDate: str,
    caseNumber: str,
    serviceName: str,
) -> Dict[str, Any]:
    """Retrieves CRM cases by filtering with optional parameters such as username, date range, case number, and service name. Useful for tracking and managing case records based on specific criteria"""
    endpoint = "/api/CrmAPI/CaseRetrival"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    params = {
        k: v
        for k, v in {
            "userName": userName,
            "fromDate": fromDate,
            "toDate": toDate,
            "caseNumber": caseNumber,
            "serviceName": serviceName,
        }.items()
        if v is not None
    }
    r = requests.get(url, params=params)
    try:
        return r.json()
    except Exception as e:
        return {"error": str(e), "status_code": r.status_code, "text": r.text}

@tool
def get_crm_groups(Username: str, Language: str) -> Dict[str, Any]:
    """Retrieves all groups from the CRM database based on the current user login. In the CRM portal, these groups are displayed as cards or menu links. Clicking a group card or link shows its associated service cards."""
    endpoint = "/api/CrmAPI/GetGroups"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    r = requests.get(url, params={"Username": Username, "Language": Language})
    try:
        return r.json()
    except Exception as e:
        return {"error": str(e), "status_code": r.status_code, "text": r.text}

@tool
def get_crm_services(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Retrieves service cards based on the currently logged-in user and the selected group ID obtained from the GetGroups endpoint."""
    endpoint = "/api/CrmAPI/GetServices"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    r = requests.post(url, json=payload)
    try:
        return r.json()
    except Exception as e:
        return {"error": str(e), "status_code": r.status_code, "text": r.text}

@tool
def create_crm_case(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Creates a new case in the CRM using the currently logged-in user name and the selected service ID from the GetServices endpoint. Attachments are optional"""
    endpoint = "/api/CrmAPI/CrmCaseRequest"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    r = requests.post(url, json=payload)
    try:
        return r.json()
    except Exception as e:
        return {"error": str(e), "status_code": r.status_code, "text": r.text}

@tool
def retrieve_crm_comments(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Retrieves all comments associated with the specified case number.."""
    endpoint = "/api/CrmAPI/CrmRetrieveComment"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    r = requests.post(url, json=payload)
    try:
        return r.json()
    except Exception as e:
        return {"error": str(e), "status_code": r.status_code, "text": r.text}

@tool
def create_crm_comment(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Create a comment in CRM for a specified case."""
    endpoint = "/api/CrmAPI/CrmCreateComment"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    r = requests.post(url, json=payload)
    try:
        return r.json()
    except Exception as e:
        return {"error": str(e), "status_code": r.status_code, "text": r.text}

@tool
def validate_crm_email(UserEmail: str) -> Dict[str, Any]:
    """Validate a CRM user email."""
    endpoint = "/api/CrmAPI/CrmEmailValidation"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    r = requests.get(url, params={"UserEmail": UserEmail})
    try:
        return r.json()
    except Exception as e:
        return {"error": str(e), "status_code": r.status_code, "text": r.text}

@tool
def get_crm_issue_types(ServiceId: str) -> Dict[str, Any]:
    """If the case registration form includes a issue lookup, pass the service ID to retrieve all related issue types."""
    endpoint = "/api/CrmAPI/TypeOfIssues"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    r = requests.get(url, params={"ServiceId": ServiceId})
    try:
        return r.json()
    except Exception as e:
        return {"error": str(e), "status_code": r.status_code, "text": r.text}

@tool
def get_crm_training_types(ServiceId: str) -> Dict[str, Any]:
    """If the case registration form includes a issue lookup, pass the service ID to retrieve all related training types."""
    endpoint = "/api/CrmAPI/TrainingTypes"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    r = requests.get(url, params={"ServiceId": ServiceId})
    try:
        return r.json()
    except Exception as e:
        return {"error": str(e), "status_code": r.status_code, "text": r.text}

@tool
def get_crm_locations(ServiceId: str) -> Dict[str, Any]:
    """If the case registration form includes a issue lookup, pass the service ID to retrieve all related location types."""
    endpoint = "/api/CrmAPI/Locations"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    r = requests.get(url, params={"ServiceId": ServiceId})
    try:
        return r.json()
    except Exception as e:
        return {"error": str(e), "status_code": r.status_code, "text": r.text}

@tool
def get_crm_inquiry_subjects(ServiceId: str) -> Dict[str, Any]:
    """If the case registration form includes a issue lookup, pass the service ID to retrieve all related inquiry subjects"""
    endpoint = "/api/CrmAPI/InquirySubject"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    r = requests.get(url, params={"ServiceId": ServiceId})
    try:
        return r.json()
    except Exception as e:
        return {"error": str(e), "status_code": r.status_code, "text": r.text}

@tool
def get_crm_inquiry_types(ServiceId: str) -> Dict[str, Any]:
    """If the case registration form includes a issue lookup, pass the service ID to retrieve all related inquiry types."""
    endpoint = "/api/CrmAPI/InquiryTypes"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    r = requests.get(url, params={"ServiceId": ServiceId})
    try:
        return r.json()
    except Exception as e:
        return {"error": str(e), "status_code": r.status_code, "text": r.text}

@tool
def get_user_roles(UserName: str) -> Dict[str, Any]:
    """Retrieve CRM roles for a user."""
    endpoint = "/api/CrmAPI/GetUserRoles"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    r = requests.get(url, params={"UserName": UserName})
    try:
        return r.json()
    except Exception as e:
        return {"error": str(e), "status_code": r.status_code, "text": r.text}

@tool
def get_form_data(ServiceId: str) -> Dict[str, Any]:
    """Retrieves dynamic form field details from the CRM database based on the service ID. This includes various field types used in the portal, such as input fields, textareas, dropdowns, radio buttons, and labels."""
    endpoint = "/api/CrmAPI/GetFormData"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    r = requests.get(url, params={"ServiceId": ServiceId})
    try:
        return r.json()
    except Exception as e:
        return {"error": str(e), "status_code": r.status_code, "text": r.text}

@tool
def upload_crm_case_attachment(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Upload attachments for a CRM case request."""
    endpoint = "/api/CrmAPI/CrmCaseRequestAttachment"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    r = requests.post(url, json=payload)
    try:
        return r.json()
    except Exception as e:
        return {"error": str(e), "status_code": r.status_code, "text": r.text}

@tool
def get_crm_attachment_by_file_id(FileId: str) -> Dict[str, Any]:
    """Retrieve a CRM case attachment by file ID."""
    endpoint = "/api/CrmAPI/CrmCaseRequestGetAttachmentByFileId"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    r = requests.get(url, params={"FileId": FileId})
    try:
        return r.json()
    except Exception as e:
        return {"error": str(e), "status_code": r.status_code, "text": r.text}

@tool
def delete_crm_attachments(file_ids: list[str]) -> Dict[str, Any]:
    """Delete CRM case attachments by file IDs."""
    endpoint = "/api/CrmAPI/CrmCaseRequestDeleteAttachmentByFileId"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    r = requests.delete(url, json=file_ids)
    try:
        return r.json()
    except Exception as e:
        return {"error": str(e), "status_code": r.status_code, "text": r.text}

@tool
def get_attachments_for_ticket(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Retrieve attachments for a CRM ticket."""
    endpoint = "/api/CrmAPI/GetAttachmentsForTicket"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    r = requests.post(url, json=payload)
    try:
        return r.json()
    except Exception as e:
        return {"error": str(e), "status_code": r.status_code, "text": r.text}

@tool
def delete_attachment_by_key(i_ATTACHMENT_ID: int, i_SESSION_ID: str = "0", i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/DELETE_ATTACHMENT_BY_KEY"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_ATTACHMENT_ID": i_ATTACHMENT_ID

    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def add_attachment(i_TRANSACTION_ID: str ="0",i_FILENAME:str = "0",i_FILE_BLOB:str ="0",i_FILE_TYPE:str="0"
                   ,i_USER:str ="0",i_TRX_TYPE:str="0", i_SESSION_ID: str = "0", i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/ADD_ATTACHMENT"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_TRANSACTION_ID": i_TRANSACTION_ID,
        "i_FILENAME":i_FILENAME,
        "i_FILE_BLOB":i_FILE_BLOB,
        "i_FILE_TYPE":i_FILE_TYPE,
        "i_USER":i_USER,
        "i_TRX_TYPE":i_TRX_TYPE,
        "i_LANG": i_LANG

    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def submit_trx(i_TRANSACTION_ID: str = "0") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/SUBMIT_TRX"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_TRANSACTION_ID": i_TRANSACTION_ID
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def validate_user_login(i_USER_NAME: str="0", i_PASSWORD: str = "0", i_LANG: str = "US", i_DEVICE_NAME:str="0",i_DEVICE_ID: str="0",
                        i_DEVICE_OS: str ="0",i_LATTITUDE:str ="0",i_LONGTITUDE:str ="0") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/VALIDATE_USER_LOGIN"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_USER_NAME": i_USER_NAME,
        "i_PASSWORD": i_PASSWORD,
        "i_LANG": i_LANG,
        "i_DEVICE_NAME":i_DEVICE_NAME,
        "i_DEVICE_ID":i_DEVICE_ID,
        "i_DEVICE_OS":i_DEVICE_OS,
        "i_LATTITUDE":i_LATTITUDE,
        "i_LONGTITUDE":i_LONGTITUDE,

    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def reset_password(i_USER_NAME: str, i_NEW_PASSWORD: str = "0", i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/RESET_PASSWORD"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_USER_NAME": i_USER_NAME,
        "i_NEW_PASSWORD": i_NEW_PASSWORD,
        "i_LANG": i_LANG

    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def user_change_password(i_USER_NAME: str,i_OLD_PASSWORD:str = "0", i_NEW_PASSWORD: str = "0",i_NEW_PASSWORD_2:str="0", i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/USER_CHANGE_PASSWORD"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_USER_NAME": i_USER_NAME,
        "i_OLD_PASSWORD":i_OLD_PASSWORD,
        "i_NEW_PASSWORD": i_NEW_PASSWORD,
        "i_NEW_PASSWORD_2":i_NEW_PASSWORD_2,
        "i_LANG": i_LANG

    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def validate_user_login_v3(i_USER_NAME: str, i_SESSION_ID: str = "0",i_PASSWORD: str = "0", i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/VALIDATE_USER_LOGIN_V3"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_USER_NAME": i_USER_NAME,
        "i_SESSION_ID": i_SESSION_ID,
        "i_PASSWORD": i_PASSWORD,
        "i_LANG": i_LANG

    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def get_award_types(i_SESSION_ID: str, i_PERSON_ID: str = "0", i_LANG: str = "US") -> dict:

    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/GET_AWARD_TYPES"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_PERSON_ID": i_PERSON_ID,
        "i_LANG": i_LANG

    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def view_award_winners(i_SESSION_ID: str,i_AWARD_TYPE:str, i_YEAR: str = "2025", i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/VIEW_AWARD_WINNERS"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_YEAR": i_YEAR,
        "i_AWARD_TYPE":i_AWARD_TYPE
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def get_reward_types(i_SESSION_ID: str, i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/GET_REWARD_TYPES"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_LANG": i_LANG

    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def get_award_actions(i_SESSION_ID: str, i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/GET_AWARD_ACTIONS"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_LANG": i_LANG

    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def submit_award_nomtinees(i_SESSION_ID: str,i_PERSON_ID:int,i_AWARD_PLAN_ID:int,i_MULT_PRP_IDS:int, i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/SUBMIT_AWARD_NOMINEES"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_PERSON_ID":i_PERSON_ID,
        "i_AWARD_PLAN_ID":i_AWARD_PLAN_ID,
        "i_MULT_PRP_IDS":i_MULT_PRP_IDS
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def get_award_nomtinees(i_SESSION_ID: str,i_PERSON_ID:int,i_AWARD_PLAN_ID:int, i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/GET_AWARD_NOMINEES"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_PERSON_ID":i_PERSON_ID,
        "i_AWARD_PLAN_ID":i_AWARD_PLAN_ID

    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def get_award_status(i_SESSION_ID: str, i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/GET_AWARD_STATUS"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_LANG": i_LANG

    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def get_award_plans(i_SESSION_ID: str,i_PERSON_ID:int, i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/GET_AWARD_PLANS"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_PERSON_ID":i_PERSON_ID

    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def get_award_plans_v2(i_SESSION_ID: str,i_ENTITY_CODE:str, i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/GET_AWARD_PLANS_V2"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_ENTITY_CODE":i_ENTITY_CODE
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def get_emp_award_question(i_SESSION_ID:str,i_AWARD_PROP_ID: str, i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/CrmAPI/GET_EMP_AWARD_QUESTIONS"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_AWARD_PROP_ID":i_AWARD_PROP_ID,
        "i_SESSION_ID": i_SESSION_ID,
        "i_LANG": i_LANG,
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def submit_emp_award_justification(i_SESSION_ID: str,i_PERSON_ID:int,i_QUESTION_ID:int,i_JUSTIFICATION:str, i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/SUBMIT_EMP_AWARD_JUSTIFICATION"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_PERSON_ID":i_PERSON_ID,
        "i_QUESTION_ID":i_QUESTION_ID,
        "i_JUSTIFICATION":i_JUSTIFICATION
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def save__award_justification(i_SESSION_ID: str,i_PERSON_ID:int,i_QUESTION_ID:int,i_JUSTIFICATION:str, i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/SAVE_MGR_AWARD_JUSTIFICATION"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_PERSON_ID":i_PERSON_ID,
        "i_QUESTION_ID":i_QUESTION_ID,
        "i_JUSTIFICATION":i_JUSTIFICATION
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def save_emp_award_justification(i_SESSION_ID: str,i_PERSON_ID:int,i_QUESTION_ID:int,i_JUSTIFICATION:str, i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/SAVE_EMP_AWARD_JUSTIFICATION"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_PERSON_ID":i_PERSON_ID,
        "i_QUESTION_ID":i_QUESTION_ID,
        "i_JUSTIFICATION":i_JUSTIFICATION
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def submit_emp_award_justification(i_SESSION_ID: str,i_PERSON_ID:int,i_AWARD_PROP_ID:int,i_COMMENTS:str, i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/SUBMIT_EMP_AWARD_JUSTIFICATION"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_PERSON_ID":i_PERSON_ID,
        "i_AWARD_PROP_ID":i_AWARD_PROP_ID,
        "i_COMMENTS":i_COMMENTS
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def save_mgr_award_justification(i_SESSION_ID: str,i_USER_NAME:str,i_QUESTION_ID:int,i_JUSTIFICATION:str, i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/SAVE_MGR_AWARD_JUSTIFICATION"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_USER_NAME":i_USER_NAME,
        "i_QUESTION_ID":i_QUESTION_ID,
        "i_JUSTIFICATION":i_JUSTIFICATION
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

# @tool
# def get_emp_award_nominations(i_PERSON_ID:int, i_LANG: str = "US") -> dict:
#     """Fetch personal employee info."""
#     endpoint = "/api/MobileAPI/GET_EMP_AWARD_NOMINATIONS"
#     url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
#     headers = {
#         "accept": "application/json",
#         "Content-Type": "application/json"
#     }
    
#     payload = {
#         "i_PERSON_ID":i_PERSON_ID,
#         "i_LANG": i_LANG,
#     }

#     response = requests.post(url, headers=headers, json=payload)
#     # print(f"API Response {response.json()}")
#     try:
#         return response.json()
#     except Exception as e:
#         return {"error": str(e), "status_code": response.status_code, "text": response.text}


@tool
def rollback_transaction(i_SESSION_ID:str,i_TRANSACTION_ID:int, i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/ROLLBACK_TRANSACTION"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID":i_SESSION_ID,
        "i_TRANSACTION_ID":i_TRANSACTION_ID,
        "i_LANG": i_LANG,
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def get_nominations_monthly(i_SESSION_ID:str,i_ENTITY_CODE:str,i_MONTH:str, i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/GET_NOMINATIONS_MONTHLY"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID":i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_ENTITY_CODE":i_ENTITY_CODE,
        "i_MONTH":i_MONTH,
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def get_award_quest_attachment(i_SESSION_ID:str,i_AWARD_PROP_ID:int, i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/GET_AWARD_QUEST_ATTACHMENT"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID":i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_AWARD_PROP_ID":i_AWARD_PROP_ID,
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def get_award_questions(i_SESSION_ID:str,i_AWARD_CODE:str, i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/GET_AWARD_QUESTIONS"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID":i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_AWARD_PROP_ID":i_AWARD_CODE,
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def get_award_nominees_by_mgr(i_SESSION_ID:str,i_AWARD_CODE:str, i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/GET_AWARD_NOMINEES_BY_MGR"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID":i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_AWARD_PROP_ID":i_AWARD_CODE,
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def get_award_nominees_for_emp(i_SESSION_ID:str,i_PERSON_ID:int,i_AWARD_PLAN_ID:int,i_STATUS:str,i_YEAR:str ,i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/GET_AWARD_NOMINEES_FOR_EMP"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID":i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_PERSON_ID":i_PERSON_ID,
        "i_AWARD_PLAN_ID":i_AWARD_PLAN_ID,
        "i_STATUS":i_STATUS,
        "i_YEAR":i_YEAR

    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def get_award_nominees_by_emp(i_SESSION_ID:str,i_PERSON_ID:int,i_AWARD_PLAN_ID:int,i_STATUS:str ,i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/GET_AWARD_NOMINEES_BY_EMP"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID":i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_PERSON_ID":i_PERSON_ID,
        "i_AWARD_PLAN_ID":i_AWARD_PLAN_ID,
        "i_STATUS":i_STATUS
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}


@tool
def get_knowledge_documents(query: str) -> dict:
    """
    Fetch internal knowledge database or UAE federal government employee HR policies, including housing allowance, leave types, contract regulations, payroll, benefits, and other administrative rules as outlined by FAHR and relevant resolutions. Use this tool for any queries related to internal employment laws, federal HR procedures, or policy documents.
    """
    
    print(f"Getting internal knowledge for query: {query}")

    message_objs = [HumanMessage(content=query)]
    state = {
        "messages": message_objs,
        "conversation_id": "default"
    }

    config = RunnableConfig(configurable={"thread_id": "default"})
    results = rag_workflow_instance.run(state, config=config)
    # results = retriever.query(query)
    
    return results
    
@tool
def get_performance_history(i_PERSON_ID: int, i_SESSION_ID: str = "0", i_LANG: str = "US") -> dict:
    """
    Fetches performance history for the employee.
 
    Args:
        i_PERSON_ID (int): Employee person ID. [Required]
        i_SESSION_ID (str): Session identifier.
        i_LANG (str): Language code ("US" or "AR").
 
    Returns:
        dict: List of performance history entries including year, rating, etc.
    """
    endpoint = "/api/MobileAPI/GET_PERFORMANCE_DET"  # Replace if actual endpoint differs
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
 
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
 
    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_PERSON_ID": i_PERSON_ID,
        "i_LANG": i_LANG
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}
@tool
def get_working_hours(i_PERSON_ID: int, i_SESSION_ID: str = "0", i_LANG: str = "US") -> dict:
    """
    Retrieves the attendace of the employee.

    Args:
        i_SESSION_ID (str): User's session identifier.
        i_PERSON_ID (int): Employee's person ID. [Required]
        i_LANG (str): Language code.

    Returns:
        dict: clock in and out information
    """
    endpoint = "/api/MobileAPI/GET_WORKING_HOURS"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_PERSON_ID": i_PERSON_ID,
        "i_LANG": i_LANG
    }

    response = requests.post(url, headers=headers, json=payload)
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}
@tool
def get_attendance_details(i_PERSON_ID: int, i_DATE: str, i_SESSION_ID: str = "0", i_LANG: str = "US") -> dict:
    """
    Gets the attendance details of the employee for a given date.

    Args:
        i_SESSION_ID (str): Session ID of the requester.
        i_PERSON_ID (int): Person ID of the employee. [Required]
        i_DATE (str): Attendance date in DD-MM-YYYY format.
        i_LANG (str): Language code ("US" or "AR").

    Returns:
        dict: In/Out timings, attendance status, violations (if any).
    """
    endpoint = "/api/MobileAPI/GET_ATTENDANCE_DET"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_PERSON_ID": i_PERSON_ID,
        "i_DATE": i_DATE,
        "i_LANG": i_LANG
    }

    response = requests.post(url, headers=headers, json=payload)
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}
@tool
def get_person_request_v2(i_SESSION_ID:str,i_PERSON_ID:int,i_YEAR:str, i_LANG: str = "US") -> dict:
    """Fetch personal employee info."""
    endpoint = "/api/MobileAPI/GET_PERSON_REQUESTS-V2"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID":i_SESSION_ID,
        "i_PERSON_ID":i_PERSON_ID,
        "i_YEAR":i_YEAR,
        "i_LANG": i_LANG,
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}
@tool
def get_emp_insurance_history(i_PERSON_ID: int, i_SESSION_ID: str = "0", i_LANG: str = "US") -> dict:
    """
    Retrieves the insurance history of the employee.

    Args:
        i_SESSION_ID (str): Session ID.
        i_PERSON_ID (int): Person ID of the employee. [Required]
        i_LANG (str): Language code ("US" or "AR").

    Returns:
        dict: Insurance policy details, enrollment periods, and coverage.
    """
    endpoint = "/api/MobileAPI/GET_EMP_INSURANCE_HISTORY"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_PERSON_ID": i_PERSON_ID,
        "i_LANG": i_LANG
    }

    response = requests.post(url, headers=headers, json=payload)
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}
@tool
def get_business_card_details(i_PERSON_ID: int, i_SESSION_ID: str = "0", i_LANG: str = "US") -> dict:
    """
    Retrieves the business card details of an employee.

    Args:
        i_SESSION_ID (str): Session ID of the user.
        i_PERSON_ID (int): Employee's person ID. [Required]
        i_LANG (str): Language code ("US" or "AR").

    Returns:
        dict: Business card details including department, job title, contact info, etc.
    """
    endpoint = "/api/MobileAPI/GET_BUSINESS_CARD_DET"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_PERSON_ID": i_PERSON_ID,
        "i_LANG": i_LANG
    }

    response = requests.post(url, headers=headers, json=payload)
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}
@tool
def get_assignment_info(i_PERSON_ID: int, i_SESSION_ID: str = "0", i_LANG: str = "US") -> dict:
    """
    Retrieves the current assignment information for the employee.

    Args:
        i_SESSION_ID (str): User session ID.
        i_PERSON_ID (int): Person ID of the employee. [Required]
        i_LANG (str): Language preference ("US" or "AR").

    Returns:
        dict: Assignment details such as location, job title, and department.
    """
    endpoint = "/api/MobileAPI/GET_ASSIGNMENT_INFO"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_PERSON_ID": i_PERSON_ID,
        "i_LANG": i_LANG
    }

    response = requests.post(url, headers=headers, json=payload)
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def get_leave_mgr_details(i_SESSION_ID:str,i_MANAGER_ID:int,i_START_DATE:str,i_END_DATE:str,i_LEVEL:str, i_LANG: str = "US") -> dict:
    """Allows a manager to view leave details of team members within
        a specific date range and level. Requires manager ID, language, and date range.
        The i_LEVEL determines whether the manager wants to see the details of their
        direct reportees or within his Hierarchy."""
    endpoint = "/api/MobileAPI/GET_LEAVE_MGR_DETAILS"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID":i_SESSION_ID,
        "i_MANAGER_ID":i_MANAGER_ID,
        "i_START_DATE":i_START_DATE,
        "i_END_DATE":i_END_DATE,
        "i_LANG": i_LANG,
        "i_LEVEL":i_LEVEL

    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}
@tool
def get_mgr_latest_leave_emp_det(i_SESSION_ID:str,i_PERSON_ID:int,i_LEVEL:str, i_LANG: str = "US") -> dict:
    """This endpoint provides details about the latest leave requests
        for employees under a manager's hierarchy. Allows a manager to view leave
        details of team members within a specific date range and level. Requires manager
        ID, language, and date range. The i_LEVEL"""
    endpoint = "/api/MobileAPI/GET_MGR_LATEST_LEAVE_EMP_DET"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID":i_SESSION_ID,
        "i_PERSON_ID":i_PERSON_ID,
        "i_LEVEL":i_LEVEL,
        "i_LANG": i_LANG,
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}
@tool
def get_person_request(i_SESSION_ID:str,i_PERSON_ID:int,i_YEAR:str, i_LANG: str = "US") -> dict:
    """Retrieves personal requests submitted by the employee."""
    endpoint = "/api/MobileAPI/GET_PERSON_REQUESTS"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID":i_SESSION_ID,
        "i_PERSON_ID":i_PERSON_ID,
        "i_YEAR":i_YEAR,
        "i_LANG": i_LANG,
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}
@tool
def view_payslip_pdf(i_SESSION_ID:str,i_PERSON_ID:int,i_PERIOD_MONTH:str, i_PERIOD_YEAR:str,i_LANG: str = "US") -> dict:
    """Retrieves the PDF version of an employee's payslip payslip for
        the specified month and year. This is typically used to download or view payslip
        documents. Requires person ID"""
    endpoint = "/api/MobileAPI/VIEW_PAYSLIP_PDF"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID":i_SESSION_ID,
        "i_PERSON_ID":i_PERSON_ID,
        "i_YEAR":i_YEAR,
        "i_LANG": i_LANG,
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}
    
@tool
def get_live_notification_count(i_SESSION_ID:str,i_USER_NAME:str,i_STATUS:str,i_LANG: str = "US") -> dict:
    """Retrieves the count of live notifications for a specific user based on provided criteria."""
    endpoint = "/api/MobileAPI/GET_LIVE_NOTIFICATIONS_COUNT"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID":i_SESSION_ID,
        "i_USER_NAME":i_USER_NAME,
        "i_STATUS":i_STATUS,
        "i_LANG": i_LANG,
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}
@tool
def get_live_notification_by_page(i_SESSION_ID:str,i_USER_NAME:str,i_STATUS:str,i_PAGE_SIZE:str,i_START_WITH_ID:str,i_LANG: str = "US") -> dict:
    """Retrieves a paginated list of live notifications for a specific user based on provided criteria."""
    endpoint = "/api/MobileAPI/GET_LIVE_NOTIFICATIONS_BY_PAGE"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID":i_SESSION_ID,
        "i_USER_NAME":i_USER_NAME,
        "i_STATUS":i_STATUS,
        "i_PAGE_SIZE":i_PAGE_SIZE,
        "i_START_WITH_ID":i_START_WITH_ID,
        "i_LANG": i_LANG,
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}
@tool
def get_notification_body_v2(i_SESSION_ID:str,i_NOTIFICATION_ID:str,i_LANG: str = "US") -> dict:
    """Retrieves detailed content of a specific notification using its
        unique ID, session, and preferred language."""
    endpoint = "/api/MobileAPI/GET_NOTIFICATION_BODY_V2"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID":i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_NOTIFICATION_ID":i_NOTIFICATION_ID
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def pm_get_appraisal_plans(i_SESSION_ID:str,i_PERSON_ID:int,i_LANG: str = "US") -> dict:
    """Returns list of all appraisals for a specific employee using i_PERSON_ID.
        This endpoint returns all the appraisals for the employee including year,
        status, plan name, submitted dates, phases"""
    endpoint = "/api/MobileAPI/PM_GET_APPRAISAL_PLANS"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "i_SESSION_ID":i_SESSION_ID,
        "i_PERSON_ID":i_PERSON_ID,
        "i_LANG": i_LANG
    }

    response = requests.post(url, headers=headers, json=payload)
    # print(f"API Response {response.json()}")
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def get_code_of_conduct(i_PERSON_ID: int, i_SESSION_ID: str = "0", i_LANG: str = "US") -> dict:
    """
    Retrieves the code of conduct for an employee.

    Args:
        i_SESSION_ID (str): Session ID.
        i_PERSON_ID (int): Person ID of the employee. [Required]
        i_LANG (str): Language selection.

    Returns:
        dict: Code of conduct information.
    """
    endpoint = "/api/MobileAPI/GET_CODE_OF_CONDUCT"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_PERSON_ID": i_PERSON_ID,
        "i_LANG": i_LANG
    }

    response = requests.post(url, headers=headers, json=payload)
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}
@tool
def get_eit_requests(i_PERSON_ID: str, i_TRANSACTION_ID: int = None, i_REQUEST_TYPE: str = None, 
                     i_START_DATE: str = None, i_END_DATE: str = None, i_LANG: str = "US") -> dict:
    """
    Retrieves EIT requests for an employee.

    Args:
        i_PERSON_ID (str): Person ID of the employee. [Required]
        i_TRANSACTION_ID (int): Transaction ID (optional).
        i_REQUEST_TYPE (str): Request type (optional).
        i_START_DATE (str): Start date (optional).
        i_END_DATE (str): End date (optional).
        i_LANG (str): Language selection.

    Returns:
        dict: EIT request details.
    """
    endpoint = "/api/MobileAPI/GET_EIT_REQUESTS"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "i_PERSON_ID": i_PERSON_ID,
        "i_TRANSACTION_ID": i_TRANSACTION_ID,
        "i_REQUEST_TYPE": i_REQUEST_TYPE,
        "i_START_DATE": i_START_DATE,
        "i_END_DATE": i_END_DATE,
        "i_LANG": i_LANG
    }

    response = requests.post(url, headers=headers, json=payload)
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}
@tool
def get_emp_all_details_per_type(i_MANAGER_ID: int, i_SESSION_ID: str = "0", i_LANG: str = "US", 
                                 l_FROM_DATE: str = None, l_END_DATE: str = None, 
                                 i_INFORMATION_TYPE: str = None) -> dict:
    """
    Retrieves all employee details per type for a manager.

    Args:
        i_SESSION_ID (str): Session ID.
        i_LANG (str): Language selection.
        i_MANAGER_ID (int): Manager ID. [Required]
        l_FROM_DATE (str): From date (optional).
        l_END_DATE (str): End date (optional).
        i_INFORMATION_TYPE (str): Information type (optional).

    Returns:
        dict: Employee details per type.
    """
    endpoint = "/api/MobileAPI/GET_EMP_ALL_DETAILS_PER_TYPE"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_MANAGER_ID": i_MANAGER_ID,
        "l_FROM_DATE": l_FROM_DATE,
        "l_END_DATE": l_END_DATE,
        "i_INFORMATION_TYPE": i_INFORMATION_TYPE
    }

    response = requests.post(url, headers=headers, json=payload)
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}
@tool
def get_emp_comp_off_overtime_det(i_PERSON_ID: int, i_SESSION_ID: str = "0", i_LEVEL: str = None, 
                                  i_LANG: str = "US", i_START_DATE: str = None, 
                                  i_END_DATE: str = None) -> dict:
    """
    Retrieves employee compensation overtime details.

    Args:
        i_SESSION_ID (str): Session ID.
        i_LEVEL (str): Level (optional).
        i_PERSON_ID (int): Person ID of the employee. [Required]
        i_LANG (str): Language selection.
        i_START_DATE (str): Start date (optional).
        i_END_DATE (str): End date (optional).

    Returns:
        dict: Employee compensation overtime details.
    """
    endpoint = "/api/MobileAPI/GET_EMP_COMP_OFF_OVERTIME_DET"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_LEVEL": i_LEVEL,
        "i_PERSON_ID": i_PERSON_ID,
        "i_LANG": i_LANG,
        "i_START_DATE": i_START_DATE,
        "i_END_DATE": i_END_DATE
    }

    response = requests.post(url, headers=headers, json=payload)
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}
@tool
def get_ma_qassart_sent(i_PERSON_ID: int, i_SESSION_ID: str = "0", i_MONTH: str = None, 
                        i_YEAR: str = None, i_LANG: str = "US") -> dict:
    """
    Retrieves MaQassart sent information.

    Args:
        i_SESSION_ID (str): Session ID.
        i_PERSON_ID (int): Person ID of the employee. [Required]
        i_MONTH (str): Month (optional).
        i_YEAR (str): Year (optional).
        i_LANG (str): Language selection.

    Returns:
        dict: MaQassart sent information.
    """
    endpoint = "/api/MobileAPI/GET_MA_QASSART_SENT"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_PERSON_ID": i_PERSON_ID,
        "i_MONTH": i_MONTH,
        "i_YEAR": i_YEAR,
        "i_LANG": i_LANG
    }

    response = requests.post(url, headers=headers, json=payload)
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}
@tool
def get_other_address(i_PERSON_ID: int, i_SESSION_ID: str = "0", i_LANG: str = "US") -> dict:
    """
    Retrieves other address information for an employee.

    Args:
        i_SESSION_ID (str): Session ID.
        i_PERSON_ID (int): Person ID of the employee. [Required]
        i_LANG (str): Language selection.

    Returns:
        dict: Other address information.
    """
    endpoint = "/api/MobileAPI/GET_OTHER_ADDRESS"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_PERSON_ID": i_PERSON_ID,
        "i_LANG": i_LANG
    }

    response = requests.post(url, headers=headers, json=payload)
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}
@tool
def get_phones(i_PERSON_ID: int, i_SESSION_ID: str = "0", i_LANG: str = "US") -> dict:
    """
    Retrieves phone information for an employee.

    Args:
        i_SESSION_ID (str): Session ID.
        i_PERSON_ID (int): Person ID of the employee. [Required]
        i_LANG (str): Language selection.

    Returns:
        dict: Phone information.
    """
    endpoint = "/api/MobileAPI/GET_PHONES"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_PERSON_ID": i_PERSON_ID,
        "i_LANG": i_LANG
    }

    response = requests.post(url, headers=headers, json=payload)
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}
@tool
def get_profile_completion(i_PERSON_ID: int, i_SESSION_ID: str = "0", i_LANG: str = "US", 
                           i_YEAR: str = None) -> dict:
    """
    Retrieves profile completion information and percentage for an employee.

    Args:
        i_SESSION_ID (str): Session ID.
        i_LANG (str): Language selection.
        i_PERSON_ID (int): Person ID of the employee. [Required]
        i_YEAR (str): Year (optional).

    Returns:
        dict: Profile completion information.
    """
    endpoint = "/api/MobileAPI/GET_PROFILE_COMPLETION"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_PERSON_ID": i_PERSON_ID,
        "i_YEAR": i_YEAR
    }

    response = requests.post(url, headers=headers, json=payload)
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}
@tool
def get_qualifications(i_PERSON_ID: int, i_SESSION_ID: str = "0", i_LANG: str = "US") -> dict:
    """
    Retrieves qualifications information for an employee.

    Args:
        i_SESSION_ID (str): Session ID.
        i_PERSON_ID (int): Person ID of the employee. [Required]
        i_LANG (str): Language selection.

    Returns:
        dict: Qualifications information.
    """
    endpoint = "/api/MobileAPI/GET_QUALIFICATIONS"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_PERSON_ID": i_PERSON_ID,
        "i_LANG": i_LANG
    }

    response = requests.post(url, headers=headers, json=payload)
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}
@tool
def olm_employee_course_his_v2(i_PERSON_ID: int, i_SESSION_ID: str = "0", i_LANG: str = "US", 
                               i_YEAR: str = None, i_DAYS: int = None) -> dict:
    """
    Retrieves employee course history version 2.

    Args:
        i_SESSION_ID (str): Session ID.
        i_LANG (str): Language selection.
        i_PERSON_ID (int): Person ID of the employee. [Required]
        i_YEAR (str): Year (optional).
        i_DAYS (int): Days (optional).

    Returns:
        dict: Employee course history information.
    """
    endpoint = "/api/MobileAPI/OLM_EMPLOYEE_COURSE_HIS_V2"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_PERSON_ID": i_PERSON_ID,
        "i_YEAR": i_YEAR,
        "i_DAYS": i_DAYS
    }

    response = requests.post(url, headers=headers, json=payload)
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}
@tool
def pm_get_appraisal_templates(plaN_ID: int, i_SESSION_ID: str = "0", i_LANG: str = "US") -> dict:
    """
    Retrieves appraisal templates for performance management.

    Args:
        i_SESSION_ID (str): Session ID.
        i_LANG (str): Language selection.
        plaN_ID (int): Plan ID. [Required]

    Returns:
        dict: Appraisal templates information.
    """
    endpoint = "/api/MobileAPI/PM_GET_APPRAISAL_TEMPLATES"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_LANG": i_LANG,
        "plaN_ID": plaN_ID
    }

    response = requests.post(url, headers=headers, json=payload)
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}
@tool
def pm_get_completed_appraisals_v2(i_PERSON_ID: int, i_SESSION_ID: str = "0", i_LANG: str = "US") -> dict:
    """
    Retrieves completed appraisals version 2 for performance management.

    Args:
        i_SESSION_ID (str): Session ID.
        i_LANG (str): Language selection.
        i_PERSON_ID (int): Person ID of the employee. [Required]

    Returns:
        dict: Completed appraisals information.
    """
    endpoint = "/api/MobileAPI/PM_GET_COMPLETED_APPRAISALS_V2"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_PERSON_ID": i_PERSON_ID
    }

    response = requests.post(url, headers=headers, json=payload)
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def pm_get_completed_objectives(i_PERSON_ID: int, i_MAIN_APPR_ID: int, i_APPRAISAL_ID: int, 
                                i_SESSION_ID: str = "0", i_LANG: str = "US") -> dict:
    """
    Retrieves completed objectives for performance management.

    Args:
        i_SESSION_ID (str): Session ID.
        i_LANG (str): Language selection.
        i_PERSON_ID (int): Person ID of the employee. [Required]
        i_MAIN_APPR_ID (int): Main appraisal ID. [Required]
        i_APPRAISAL_ID (int): Appraisal ID. [Required]

    Returns:
        dict: Completed objectives information.
    """
    endpoint = "/api/MobileAPI/PM_GET_COMPLETED_OBJECTIVES"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_PERSON_ID": i_PERSON_ID,
        "i_MAIN_APPR_ID": i_MAIN_APPR_ID,
        "i_APPRAISAL_ID": i_APPRAISAL_ID
    }

    response = requests.post(url, headers=headers, json=payload)
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}

@tool
def view_resume(i_PERSON_ID: int, i_SESSION_ID: str = "0", i_LANG: str = "US") -> dict:
    """
    Retrieves resume information for an employee.

    Args:
        i_SESSION_ID (str): Session ID.
        i_LANG (str): Language selection.
        i_PERSON_ID (int): Person ID of the employee. [Required]

    Returns:
        dict: Resume information.
    """
    endpoint = "/api/MobileAPI/VIEW_RESUME"
    url = urljoin(base_url + "/", endpoint.lstrip("/"))

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "i_SESSION_ID": i_SESSION_ID,
        "i_LANG": i_LANG,
        "i_PERSON_ID": i_PERSON_ID
    }

    response = requests.post(url, headers=headers, json=payload)
    try:
        return response.json()
    except Exception as e:
        return {"error": str(e), "status_code": response.status_code, "text": response.text}


def discover_tools() -> list:
    """Auto-discover all @tool-decorated functions in this file."""
    tools = []
    current_module = globals()

    for name, obj in current_module.items():
        if isinstance(obj, BaseTool):
            tools.append(obj)

    return tools

def get_legalAgent_tools() -> list:
    """Auto-discover all @tool-decorated functions in this file."""
    tools = [
            get_emp_profile,
            get_annual_leave_bal,
            get_business_card_details,
            get_emp_insurance_history,
            get_contracts,
            get_assignment_info,
            get_salary_change_info,
            get_payslip_info,
            get_attendance_details,
            get_working_hours,
            get_main_address,
            get_documents,
            get_award_nominees_for_employee,
            get_crm_tickets,
            get_employee_list,
            crm_case_retrieval,
            get_knowledge_documents,
            get_performance_history,
            get_code_of_conduct,
            get_eit_requests,
            get_emp_all_details_per_type,
            get_emp_comp_off_overtime_det,
            get_ma_qassart_sent,
            get_other_address,
            get_phones,
            get_profile_completion,
            get_qualifications,
            olm_employee_course_his_v2,
            pm_get_appraisal_templates,
            pm_get_completed_appraisals_v2,
            pm_get_completed_objectives,
            view_resume,
            get_leave_mgr_details,
            get_mgr_latest_leave_emp_det,
            get_person_request,
            view_payslip_pdf,
            get_live_notification_count,
            get_live_notification_by_page,
            get_notification_body_v2,
            pm_get_appraisal_plans
        ]

    return tools

from langchain_openai import ChatOpenAI
from api import VectorstoreConnector
from modules.llm_service import LLMClient
from configs.secrets import ORCHESTRATOR_CONFIG_PATH
with open(ORCHESTRATOR_CONFIG_PATH, "r") as config_file:
        configs = yaml.safe_load(config_file)

llm_client = LLMClient(config_path=configs["llm_config_path"])
llm_model = llm_client.get_model()

vectorstore_connector = VectorstoreConnector()
vectorstore = vectorstore_connector.get_vectorstore()
# retriever = ChromaRetriever()
rag_workflow_instance = RAGWorkflow(vectorstore=vectorstore, llm_model=llm_model)