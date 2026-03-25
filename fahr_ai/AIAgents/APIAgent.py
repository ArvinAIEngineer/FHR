import sys
# Add the current directory to sys.path
sys.path.append("./")
import yaml
from copy import deepcopy
from typing import Dict, Optional, List
from langchain.chat_models.base import BaseChatModel
from langchain_community.agent_toolkits.openapi.spec import reduce_openapi_spec
from langchain_community.utilities.requests import RequestsWrapper
from langchain_community.agent_toolkits.openapi import planner
from langchain_community.agent_toolkits.openapi.planner import RequestsPostToolWithParsing
from langchain_core.runnables import RunnableConfig
from AIAgents.base_agent import BaseAgent, GraphState
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from requests.exceptions import RequestException
from utils.logger import get_logger
import os
import requests
from langchain_core.messages import HumanMessage
from langchain.agents.structured_chat.output_parser import StructuredChatOutputParser
import logging 
from langchain_community.llms import OpenAI
from langchain_community.agent_toolkits.openapi.planner_prompt import ( 
    PARSING_POST_PROMPT, 
    REQUESTS_POST_TOOL_DESCRIPTION, 
    API_CONTROLLER_PROMPT,
    REQUESTS_POST_TOOL_DESCRIPTION
)
from langchain_core.prompts import BasePromptTemplate, PromptTemplate
from pydantic import Field
from typing import Any, Callable, Dict, List, Literal, Optional, Sequence, cast
from langchain_community.tools.requests.tool import BaseRequestsTool
from functools import partial
from langchain_core.tools import BaseTool, Tool

os.environ['NO_PROXY'] = '10.254.115.17, 10.254.140.69'


from contextlib import contextmanager
import types

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
    APIAgent is a specialized agent designed to interact with APIs.
    It uses OpenAPI specifications to understand the API's capabilities and structure.
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
            llm: Language model to use for the agent.
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
            self.tool_promt = config["POST_tool_prompt"]
            self.parse_promt = config["POST_parsing_prompt"]
            self.controller_prompt = config["API_controller_prompt"]
            self.API_orch_prompt = config["API_orch_prompt"]

        PARSING_POST_PROMPT = PromptTemplate(
            template=self.parse_promt,
            input_variables=["response"],
        )
        REQUESTS_POST_TOOL_DESCRIPTION = self.tool_promt
        API_CONTROLLER_PROMPT = self.controller_prompt
        API_ORCHESTRATOR_PROMPT = self.API_orch_prompt
        RequestsPostToolWithParsing = CustomRequestsPostTool
        # Override planner prompts
        planner.PARSING_POST_PROMPT = PARSING_POST_PROMPT
        planner.REQUESTS_POST_TOOL_DESCRIPTION = REQUESTS_POST_TOOL_DESCRIPTION
        planner.API_CONTROLLER_PROMPT = API_CONTROLLER_PROMPT
        planner.API_ORCHESTRATOR_PROMPT = API_ORCHESTRATOR_PROMPT
        planner.RequestsPostToolWithParsing = CustomRequestsPostTool
        # Load and reduce OpenAPI spec. Then filter by allowed APIs
        self.raw_api_spec, self.api_spec = self.load_and_reduce_spec(openAPI_file_path)

        # Initialize the RequestsWrapper with or without authentication
        if auth_config:
            # If authentication is needed, handle different auth types
            headers = self.handle_authentication(auth_config)
            self.requests_wrapper = RequestsWrapper(headers=headers)
        else:
            # No authentication needed
            self.requests_wrapper = RequestsWrapper()

        self.api_agent = planner.create_openapi_agent(
            self.api_spec,
            self.requests_wrapper,
            self.llm,
            allow_dangerous_requests=True,
            handle_parsing_errors=True,
            max_iterations = 2,
            max_execution_time=40.0, # 40 sec
            early_stopping_method = "generate"
        )

    def is_allowed(self, api_spec, allowed_endpoints):  # * SHAR
        reduced_endpoints = []
        new_api_spec = deepcopy(api_spec)

        for endpoint in new_api_spec.endpoints:
            if endpoint[0].split(" ")[1] in allowed_endpoints:
                reduced_endpoints.append(endpoint)

        # if len(allowed_endpoints) > len(reduced_endpoints):
        #     raise Exception("Not all allowed endpoints are present in the original API spec")

        object.__setattr__(new_api_spec, "endpoints", reduced_endpoints)
        return new_api_spec

    async def run(self, state: GraphState, config: RunnableConfig):
        """
        Run the agent with the given state.

        Args:
            state (dict): Current state with user input.

        Returns:
            The response from the API agent or an error message if a connection issue occurs.
        """
        thread_id = int(config["configurable"]["thread_id"])
        self.logger = get_logger(thread_id)
        self.logger.setLevel(logging.INFO)
        state["api_call_history"] = []
        # Create the API agent with the reduced API spec during runtime
        user_role = config["configurable"]["user_role"]
        # Normalize keys for comparison
        valid_roles = {key.lower(): key for key in self.role_api_mapping.keys()}

        if user_role in valid_roles:
            user_role = valid_roles[user_role]
            self.logger.info(f"User role '{user_role}'")
        else:
            self.logger.info(f"Unknown role '{user_role}', falling back to 'all'")
            user_role = "all"
        user_info = config["configurable"]["userInfo"]
        allowed_apis: list = self.role_api_mapping.get(user_role, [])
        reduced_api_spec = self.is_allowed(self.api_spec, allowed_apis)

        # self.logger.info(f"Allowed APIs for role `{user_role}`: {allowed_apis}")
        # self.logger.info(f"Available OpenAPI endpoints: {[e[0] for e in self.api_spec.endpoints]}")
        # langchain.globals.set_verbose(True)


        user_query = next(
                (msg.content for msg in reversed(state["messages"]) if isinstance(msg, HumanMessage)),"")

        person_id = user_info.get("person_id", "")
        session_id = config.get("configurable", {}).get("thread_id", "default_session_id")
        assignment_id = self.get_assignment_id(person_id, session_id)

        # Combine into final input
        input_payload = f"{user_query}\n\n[my i_PERSON_ID is]: {person_id}\n [my i_SESSION_ID is]: {session_id}\n [my i_ASSIGNMENT_ID is]: {assignment_id}"
        # print(input_payload)
        try:
            with patch_requests_for_logging(self, state):
                response = await self.api_agent.ainvoke(input_payload)
            self.logger.info(f"APIAgent response: {response}")
            return response
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

    def load_and_reduce_spec(self, file_path):
        """
        Loads and reduces the OpenAPI spec from a given YAML file.

        Args:
            file_path (str): Path to the OpenAPI specification file.

        Returns:
            tuple: The raw API spec and the reduced API spec.
        """
        self.logger.info(f"Loading OpenAPI spec from {file_path}")
        with open(file_path, encoding="utf8") as f:
            raw_api_spec = yaml.load(f, Loader=yaml.Loader)

        # Check if 'servers' key exists, add default if not
        if "servers" not in raw_api_spec:
            # Use base_url if provided, otherwise default to localhost
            server_url = self.base_url if self.base_url else "http://localhost"
            raw_api_spec["servers"] = [{"url": server_url}]
            self.logger.info(f"Full OpenAPI paths: {list(raw_api_spec['paths'].keys())}")

            self.logger.warning(f"Warning: 'servers' key not found in OpenAPI spec. Using server URL: {server_url}")
            self.logger.info(f"To set a different base URL, initialize APIAgent with the base_url parameter.")

        return raw_api_spec, reduce_openapi_spec(raw_api_spec)  # ?SHAR

    def get_endpoints(self):
        """
        Extracts all GET and POST endpoints from the OpenAPI spec.

        Returns:
            list: List of tuples containing (route, operation) pairs.
        """
        self.logger.info("Extracting endpoints from OpenAPI spec")
        if not self.raw_api_spec or not self.raw_api_spec.get("paths"):
            self.logger.error("No paths found in OpenAPI spec.")
            return []
        return [
            (route, operation) for route, operations in self.raw_api_spec["paths"].items() for operation in operations if operation in ["get", "post"]
        ]

    def get_assignment_id(self, person_id: int, session_id: str, lang: str = "US") -> int:
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
            print(f"Request error: {e}")
        except ValueError as ve:
            print(f"Parsing error: {ve}")
        return None



def _get_default_llm_chain(prompt: BasePromptTemplate) -> Any:
    from langchain.chains.llm import LLMChain

    return LLMChain(
        llm=OpenAI(),
        prompt=prompt,
    )

def _get_default_llm_chain_factory(
    prompt: BasePromptTemplate,
) -> Callable[[], Any]:
    """Returns a default LLMChain factory."""
    return partial(_get_default_llm_chain, prompt)

class CustomRequestsPostTool(BaseRequestsTool, BaseTool):
    """Requests POST tool with LLM-instructed extraction of truncated responses."""

    name: str = "requests_post"
    """Tool name."""
    description: str = REQUESTS_POST_TOOL_DESCRIPTION
    """Tool description."""
    response_length: int = MAX_RESPONSE_LENGTH

    def _run(self, text: str) -> str:
        from langchain.output_parsers.json import parse_json_markdown
        try:
            data = parse_json_markdown(text)
        except json.JSONDecodeError as e:
            raise e
        import time
        response: str = cast(str, self.requests_wrapper.post(data["url"], data["data"]))
        response = response[: self.response_length]
        return response
    
    async def _arun(self, text: str) -> str:
        raise NotImplementedError()

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


    # runtime_config = {
    #             "configurable": {
    #                 "user_role": "all", 
    #             }
    #         }
    with open(userInfo_file, "r") as file:
        userInfo = json.load(file)
        

    runtime_config = {
        "configurable": {
            "user_role": "all", 
            "userInfo": userInfo
        }
    }

    llm = ChatOpenAI(model="llama3.3:latest", openai_api_base="http://10.254.140.69:11434/v1", openai_api_key="AI-key")

    userInfo_file = "tests/userInfo.json"
    with open(userInfo_file, "r") as file:
        userInfo = json.load(file)

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
        "personalInfo":  userInfo
    }

    
 
    input_msg = user_input["conversationMessage"]
    is_output_voice = user_input["outputType"] == "VOICE"
    conversation_id = user_input["conversationId"]  # Support both field names
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
        base_url=base_url,  # Specify the base URL for your API
        auth_config=None,  # No authentication needed
    )

    # Extract endpoints for verification
    endpoints = api_agent.get_endpoints()
    # print(endpoints[:30])
    print(f"Number of endpoints: {len(endpoints)}")

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
    print("================================")

    # Example with authentication (for reference)
    """
    # OAuth2 example (like Amadeus)
    auth_config = {
        'auth_type': 'oauth2',
        'auth_url': 'https://api.example.com/oauth2/token',
        'client_id': 'your_client_id',
        'client_secret': 'your_client_secret'
    }

    # API Key example
    auth_config = {
        'auth_type': 'api_key',
        'key_name': 'x-api-key',
        'key_value': 'your_api_key_here',
        'header_name': 'x-api-key',
        'in_header': True
    }

    authenticated_agent = APIAgent(
        openAPI_file_path=yaml_file_path,
        llm=llm,
        base_url=base_url,
        auth_config=auth_config,
    )
    """
