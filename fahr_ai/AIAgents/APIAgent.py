import sys
# Add the current directory to sys.path
sys.path.append("./")
import yaml
from copy import deepcopy
from typing import Dict, Optional, List
from langchain.chat_models.base import BaseChatModel
from langchain_core.runnables import RunnableConfig
from AIAgents.base_agent import BaseAgent, GraphState
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from requests.exceptions import RequestException
from utils.logger import get_logger
import os
import requests
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
import logging 
from langchain_core.prompts import ChatPromptTemplate
from contextlib import contextmanager
import json
from AIAgents.tools_registry import (
    get_emp_profile, get_annual_leave_bal, get_business_card_details,
    get_emp_insurance_history, get_contracts, get_assignment_info,
    get_salary_change_info, get_payslip_info, get_attendance_details,
    get_working_hours, get_main_address, get_documents,
    get_award_nominees_for_employee, get_crm_tickets
)

os.environ['NO_PROXY'] = '10.254.115.17, 10.254.140.69'

MAX_RESPONSE_LENGTH = 5000

@contextmanager
def patch_requests_for_logging(agent_instance, state):
    original_request = requests.request
    original_post = requests.post
    original_get = requests.get

    def logged_requests_request(method, url, **kwargs):
        agent_instance.logger.info(f"[REQUESTS LIB] {method.upper()} {url}")
        payload = kwargs.get('data') or kwargs.get('json')
        agent_instance.logger.info(f"Data: {payload}")
        response = original_request(method, url, **kwargs)
        agent_instance.logger.info(f"Response [{response.status_code}]: {response.text[:500]}...")
        state["api_call_history"].append({
            "method": method,
            "url": url,
            "request_body": payload,
            "status_code": response.status_code,
            "response_body": response.text
        })
        return response

    requests.request = logged_requests_request
    requests.post = lambda url, **kwargs: logged_requests_request("POST", url, **kwargs)
    requests.get = lambda url, **kwargs: logged_requests_request("GET", url, **kwargs)

    try:
        yield  # Execute the wrapped block (your agent logic)
    finally:
        # Restore original methods
        requests.request = original_request
        requests.post = original_post
        requests.get = original_get


class APIAgent(BaseAgent):
    """
    APIAgent is a specialized agent designed to interact with APIs using tools and LLM bind_tools.
    This version supports both authenticated and non-authenticated APIs.
    """

    def __init__(
        self,
        openAPI_file_path,
        role_api_mapping: dict,
        llm_model: Optional[BaseChatModel] = None,
        config_path: str = "./configs/agents_config.yaml",
        base_url="http://10.254.115.17:8090/",
        auth_config=None,
    ):
        """
        Initialize the APIAgent.

        Args:
            openAPI_file_path (str): Path to the OpenAPI specification file.
            llm_model: Language model to use for the agent.
            base_url (str, optional): Base URL for the API if not specified in OpenAPI spec.
            auth_config (dict, optional): Authentication configuration.
                If None, no authentication will be used.
        """
        self.llm = llm_model
        self.openAPI_file_path = openAPI_file_path
        self.base_url = base_url
        self.role_api_mapping = role_api_mapping
        self.logger = get_logger()
        self.logger.setLevel(logging.INFO)
        self.logger.info("Initializing APIAgent")
        self.api_call_history = []  # stores all calls made during a single run()

        # Load prompt from YAML file
        with open(config_path, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
            self.system_prompt = config.get("API_system_prompt", "You are a helpful API assistant.")

        # Initialize tools
        self.tools = [
            get_emp_profile,
            get_annual_leave_bal,
            get_business_card_details,
            get_emp_insurance_history,
            get_contracts,
            get_assignment_info,
            get_attendance_details,
            get_working_hours,
            get_main_address,
            get_documents,
            get_award_nominees_for_employee,
            get_salary_change_info,
            get_payslip_info,
            get_crm_tickets
        ]

        # Bind tools to LLM
        self.llm_with_tools = self.llm.bind_tools(self.tools)

        # Create prompt template
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", "{input}")
        ])

        # Initialize the RequestsWrapper with or without authentication
        if auth_config:
            headers = self.handle_authentication(auth_config)
            # Store headers for tool usage
            self.auth_headers = headers
        else:
            self.auth_headers = {}

    async def run(self, state: GraphState, config: RunnableConfig):
        """
        Run the agent with the given state using tools and LLM bind_tools.

        Args:
            state (dict): Current state with user input.
            config: Runtime configuration

        Returns:
            The response from the API agent or an error message if a connection issue occurs.
        """
        thread_id = int(config["configurable"]["thread_id"])
        self.logger = get_logger(thread_id)
        self.logger.setLevel(logging.INFO)
        state["api_call_history"] = []

        # Get user configuration
        user_info = config["configurable"]["userInfo"]
        
        # Get user query
        user_query = next(
            (msg.content for msg in reversed(state["messages"]) if isinstance(msg, HumanMessage)), "")

        # Prepare context information
        person_id = user_info.get("personId", "")
        session_id = config.get("configurable", {}).get("thread_id", "default_session_id")
        assignment_id = self.get_assignment_id(person_id, session_id)

        # Enhanced input with context
        enhanced_input = f"""
User Query: {user_query}

Context Information:
- Person ID: {person_id}
- Session ID: {session_id}
- Assignment ID: {assignment_id}

Please use the available tools to help answer the user's query. You have access to various employee-related APIs.
"""

        try:
            with patch_requests_for_logging(self, state):
                # Generate response with tools
                response = await self.llm_with_tools.ainvoke(enhanced_input)
                
                # Check if the response contains tool calls
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    self.logger.info(f"Tool calls detected: {len(response.tool_calls)}")
                    
                    # Execute tool calls
                    tool_results = []
                    for tool_call in response.tool_calls:
                        tool_name = tool_call['name']
                        tool_args = tool_call['args']
                        
                        # Add context to tool arguments
                        tool_args.update({
                            'person_id': person_id,
                            'session_id': session_id,
                            'assignment_id': assignment_id
                        })
                        
                        self.logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
                        
                        # Find and execute the tool
                        tool_to_execute = None
                        for tool in self.tools:
                            if tool.name == tool_name:
                                tool_to_execute = tool
                                break
                        
                        if tool_to_execute:
                            try:
                                tool_result = await tool_to_execute.ainvoke(tool_args)
                                tool_results.append({
                                    'tool_call_id': tool_call['id'],
                                    'result': tool_result
                                })
                            except Exception as e:
                                self.logger.error(f"Error executing tool {tool_name}: {str(e)}")
                                tool_results.append({
                                    'tool_call_id': tool_call['id'],
                                    'result': f"Error: {str(e)}"
                                })
                    
                    # Create a follow-up message with tool results
                    messages = [
                        HumanMessage(content=enhanced_input),
                        response,
                    ]
                    
                    # Add tool results as ToolMessages
                    for tool_result in tool_results:
                        messages.append(ToolMessage(
                            content=str(tool_result['result']),
                            tool_call_id=tool_result['tool_call_id']
                        ))
                    
                    # Get final response
                    final_response = await self.llm_with_tools.ainvoke(messages)
                    
                    self.logger.info(f"APIAgent final response: {final_response}")
                    return final_response.content if hasattr(final_response, 'content') else str(final_response)
                else:
                    # No tool calls, return direct response
                    self.logger.info(f"APIAgent direct response: {response}")
                    return response.content if hasattr(response, 'content') else str(response)
                    
        except RequestException as e:
            self.logger.error(f"Connection error: {str(e)}")
            return f"Connection error occurred: {str(e)}"
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            return f"An unexpected error occurred: {str(e)}"

    def handle_authentication(self, auth_config):
        """
        Handle different authentication methods based on the provided configuration.

        Args:
            auth_config (dict): Authentication configuration with:
                - auth_type: The type of authentication (e.g., 'oauth2', 'api_key', 'basic')
                - Other parameters specific to the auth type

        Returns:
            dict: Headers to use for authenticated requests
        """
        self.logger.info("Handling authentication")
        if not auth_config:
            self.logger.info("No authentication configuration provided.")
            return {}
        auth_type = auth_config.get("auth_type", "").lower()

        if auth_type == "oauth2":
            import requests

            self.logger.info("Using OAuth2 authentication")
            auth_url = auth_config.get("auth_url")
            client_id = auth_config.get("client_id")
            client_secret = auth_config.get("client_secret")

            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            data = {
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            }
            response = requests.post(auth_url, headers=headers, data=data)
            self.logger.info(f"OAuth2 response: {response.status_code} - {response.text}")
            if response.status_code != 200:
                self.logger.error(f"Failed to obtain OAuth2 token: {response.text}")
                raise RequestException(f"Failed to obtain OAuth2 token: {response.text}")
            response.raise_for_status()
            return {"Authorization": f"Bearer {response.json().get('access_token')}"}

        elif auth_type == "api_key":
            self.logger.info("Using API Key authentication")
            key_name = auth_config.get("key_name", "api_key")
            key_value = auth_config.get("key_value")
            header_name = auth_config.get("header_name", "Authorization")

            if auth_config.get("in_header", True):
                self.logger.info("Adding API key to headers")
                return {header_name: key_value}
            else:
                # For query parameter API keys, return empty headers
                # The key will need to be added to each request URL
                return {}

        elif auth_type == "basic":
            self.logger.info("Using Basic authentication")
            import base64

            username = auth_config.get("username")
            password = auth_config.get("password")
            credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
            return {"Authorization": f"Basic {credentials}"}

        else:
            # Default case or unknown auth type
            return {}

    def get_assignment_id(self, person_id: int, session_id: str, lang: str = "US") -> int:
        """Get assignment ID for the given person and session."""
        url = "http://10.254.115.17:8090/Bayanati/bayanati-api/api/MobileAPI/GET_ASSIGNMENT_INFO"
        headers = {
            "Content-Type": "application/json"
        }
        payload = {
            "i_SESSION_ID": session_id,
            "i_PERSON_ID": person_id,
            "i_LANG": lang
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()  # Raise for HTTP errors
            data = response.json()

            records = data.get("O_CURSOR_DET", [])
            if not records:
                raise ValueError("No assignment records found")
            assignment_id = records[0].get("ASSIGNMENT_ID")
            return assignment_id

        except requests.RequestException as e:
            self.logger.error(f"Request error: {e}")
        except ValueError as ve:
            self.logger.error(f"Parsing error: {ve}")
        return None


if __name__ == "__main__":
    import json
    import asyncio
    
    # Example usage with no authentication
    yaml_file_path = "./tests/filtered_swagger2.yaml"
    role_api_mapping_path = "./configs/role_management/role_api_map.json"
    userInfo_file = "tests/userInfo.json"

    with open(role_api_mapping_path, "r") as f:
        role_api_mapping: dict = json.load(f)
    
    # Specify the base URL for your API if not in the OpenAPI spec
    base_url = "http://10.254.115.17:8090/"

    with open(userInfo_file, "r") as file:
        userInfo = json.load(file)

    llm = ChatOpenAI(model="llama3.3:latest", openai_api_base="http://10.254.140.69:11434/v1", openai_api_key="AI-key")

    user_input = {
        "userId": 0,
        "conversationId": 1234,
        "avatarId": 1,
        "sessionStart": False,
        "conversationTitle": "string",
        "inputType": "TEXT",
        "outputType": "TEXT",
        "channel": "PRIVATE",
        "personId": 0,
        "conversationMessage": "Status of my ticket CAS-02462-T3C9G9",
        "role": "all",
        "attachments": [],
        "personalInfo": userInfo
    }

    input_msg = user_input["conversationMessage"]
    is_output_voice = user_input["outputType"] == "VOICE"
    conversation_id = user_input["conversationId"]
    user_role = user_input["role"]
    channel_type = user_input["channel"]
    session_start = user_input["sessionStart"]
    userInfo = user_input["personalInfo"]
    thread_id = str(conversation_id)
    
    runtime_config = {
        "configurable": {
            "thread_id": thread_id,
            "user_role": user_role,
            "channel_type": channel_type,
            "session_start": session_start,
            "userInfo": userInfo
        }
    }

    # Create API agent without authentication but with base_url
    api_agent = APIAgent(
        openAPI_file_path=yaml_file_path,
        role_api_mapping=role_api_mapping,
        llm_model=llm,
        base_url=base_url,
        auth_config=None,
    )

    # Example query
    question = "what is my annual leave balance?"
    
    state = {"messages": [HumanMessage(content=question)]}

    response = asyncio.run(api_agent.run(state, runtime_config))
    print("================================")
    print(f"Response: {response}")
    print("================================")
    print()
    for element in api_agent.api_call_history:
        widgetType = element.get("url", "")
        widgetData = element.get("response_body", "")
        print(widgetType, widgetData)
    print("================================")