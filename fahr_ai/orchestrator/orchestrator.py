# Standard library imports
import os
import sys
import requests
from typing import List, Literal
# Third-party imports
import yaml
import json
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command
from typing_extensions import TypedDict
import logging 
# Add the current directory to sys.path
sys.path.append("./")

# Local application imports
from AIAgents.base_agent import GraphState
from AIAgents.VirtualAgent import VirtualAgent
from AIAgents.reviewerAgent import ReviewerAgent
from AIAgents.SuggestionAgent import SuggestionService
from configs.secrets import (
    AGENTS_CONFIG_PATH,
    ORCHESTRATOR_CONFIG_PATH
)
from modules.greetingHandler import GreetingHandler
from modules.tts_voice import TTSVoiceProcessor
from modules.conversationManager import ConversationManager
from modules.llm_service import LLMClient
from utils.logger import get_logger, log_execution
from utils.utils import clean_text, detect_language, reduce_personal_info

# Constants
MAX_VISITS_PER_AGENT = 1
PROXY_SETTINGS = {'NO_PROXY': 'localhost, 10.254.115.17, 10.254.140.69'}

# Apply environment settings
os.environ.update(PROXY_SETTINGS)


class QueryGuardrailSchema(TypedDict):
    """Schema for query guardrail validation results."""
    is_relevant: bool
    requires_auth: bool
    allow: bool
    message: str


class ConfigSchema(TypedDict):
    """Configuration schema for session state."""
    thread_id: str
    user_role: str
    channel_type: str
    session_start: bool
    userInfo: List


class Orchestrator:
    def __init__(
            self,
            orchestrator_configs_file: str = ORCHESTRATOR_CONFIG_PATH,
            agents_configs_file: str = AGENTS_CONFIG_PATH,
    ):
        self.base_logger = get_logger()
        self.base_logger.setLevel(logging.INFO)
        # Load all configurations
        self.configs = self._load_orchestrator_config(orchestrator_configs_file)


        # Initialize LLM (Get singleton instance)
        llm_client = LLMClient(config_path=self.configs["llm_config_path"])
        self.llm = llm_client.get_model()
        
        # Initialize all agents
        self._initialize_agents(agents_configs_file)

        # Initialize supporting components
        self.greeter = GreetingHandler()
        self.checkpointer = InMemorySaver()
        self.conversation_manager = ConversationManager(self)
        self.voice_processor = TTSVoiceProcessor()

        # Build state graph
        self.graph = self._build_graph()

    def _load_orchestrator_config(self, config_path: str) -> dict:
        """Load orchestrator configuration from YAML file."""
        try:
            with open(config_path, "r") as config_file:
                configs = yaml.safe_load(config_file)

            # Store common configuration values
            self.guardrail_prompt = configs["input_guardrail_prompt"]
            self.fahr_endpoints = configs["FAHR_endpoints"]

            return configs
        except (FileNotFoundError, KeyError, yaml.YAMLError) as e:
            self.base_logger.error(f"Error loading orchestrator config: {e}")
            raise

    def _load_role_mappings(self, role_agent_path: str, role_api_path: str) -> None:
        """Load role mappings for agents and APIs."""
        try:
            with open(role_agent_path, "r") as f:
                role_config = json.load(f)
                self.role_agent_mapping = role_config.get("role_agent_mapping", {})

            with open(role_api_path, "r") as f:
                self.role_api_mapping = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.base_logger.error(f"Error loading role mappings: {e}")
            raise
    # def _initialize_llm(self) -> ChatOpenAI:
    #     """Initialize the LLM with configuration parameters."""
    #     # return ChatOpenAI(
    #     #     model_name=self.configs["LLM_model_name"],
    #     #     openai_api_base=self.configs["openai_api_base_url"],
    #     #     openai_api_key=self.configs["openai_api_key"],
    #     #     temperature=0
    #     # )

    @log_execution
    def _initialize_agents(self, agents_config_path: str) -> None:
        """Initialize all agent instances."""

        # Legal Agent
        self.virtual_agent = VirtualAgent(
            llm_model=self.llm,
            config_path=agents_config_path,
            agent_name="LegalAgent"
        )

        # Reviewer Agent
        self.output_guardrail = ReviewerAgent(
            llm_model=self.llm,
            config_path=agents_config_path
        )

        # Suggestion Agent
        self.suggestion_agent = SuggestionService(
            llm_model=self.llm,
            config_path=agents_config_path,
            service_name="SuggestionService"
        )

    @log_execution
    async def input_guardrail_node(self, state: GraphState, config: RunnableConfig) -> GraphState:
        conversation_id = config.get("configurable", {}).get("thread_id", "unknown")
        logger = get_logger(conversation_id)  # ✅ CONVERSATION-SPECIFIC LOGGER
        logger.setLevel(logging.INFO)
        logger.info(f"Processing guardrail")
        messages = [{"role": "system", "content": self.guardrail_prompt}] + state["messages"]
        response = await self.llm.with_structured_output(QueryGuardrailSchema).ainvoke(messages)
        if not response.get("is_relevant", False):
            msg = response.get("message", "")
            if msg!="":
                state["messages"].append(
                    AIMessage(
                        content=msg,
                        response_agent="input_guardrail_agent"
                    )
                )
        logger.info(f"-------------InputguardrailAgent_node response: {state['messages']}")
        state["guardrail_response"] = response
        state["visited_agents"] = {}
        state["citations"] = []
        return state


    def input_guardrail_conditional(self, state: GraphState, config: RunnableConfig) -> Literal[
        "__end__","virtual_agent"]:
        """
        Updated conditional logic for input guardrail routing.
        Routes based on relevance, and domain mismatch.
        """
        channel_type = config.get("configurable", {}).get("channel_type", "UNKNOWN")
        conversation_id = config.get("configurable", {}).get("thread_id", "unknown")
        logger = get_logger(conversation_id)
        logger.setLevel(logging.INFO)
        response = state["guardrail_response"]

        # First check: If not relevant, end immediately
        if not response["is_relevant"]:
            return "__end__"

        # Second check: If public channel and requires auth, end
        if channel_type == "PUBLIC" and response.get("requires_auth", False):
            return "__end__"
        # Fallback for legal agent
        return "virtual_agent"


    def start_conditional_node(self, state: GraphState, config: RunnableConfig) -> Literal[
        "input_guardrail", "greeting"]:
        session_start = config.get("configurable", {}).get("session_start", False)
        conversation_id = config.get("configurable", {}).get("thread_id", "unknown")
        if session_start or conversation_id=="0":
            return "greeting"
        else:
            return "input_guardrail"

    @log_execution
    async def greeting_node(self, state: GraphState, config: RunnableConfig) -> GraphState:
        """
        Debug version of your greeting_node with extensive logging
        """
        try:
            # Extract user/channel info from config
            config_data = config.get("configurable", {})
            channel_type = config_data.get("channel_type", "default")
            user_info = config_data.get("userInfo", {})
            language = user_info.get("language", "en")
            user_name = user_info.get("employeeName", "User")

            # Run greeting using the greeter agent
            output_msg = await self.greeter.run(
                channel_type=channel_type,
                user_name=user_name,
                language=language
            )
            state["messages"].append(
                AIMessage(
                    content=output_msg,
                    response_agent="greeting_agent"
                )
            )

            # Prepare request payload - Debug each step
            messages_text = [msg.content for msg in state["messages"] if hasattr(msg, "content")]

            data = await self.suggestion_agent.generate_suggestions(messages_text)
            state["suggestions"] = data.get("suggestions", [])
            self.base_logger.info(f"--------------Suggestions: {state['suggestions']}")

        except Exception as e:
            self.base_logger.exception(f"Error in greeting_node: {str(e)}")

        return state

    @log_execution
    async def virtualAgent_node(self, state: GraphState, config: RunnableConfig) -> Command[Literal["output_guardrail"]]:
        # Process the state using LegalAgent - returns a string directly
        conversation_id = config.get("configurable", {}).get("thread_id", "unknown")
        logger = get_logger(int(conversation_id))
        logger.setLevel(logging.INFO)
        logger.info(f"-------------VirtualAgent_node state before entering run: {state['messages']}")
        logger.info(f"virtual agent node config {config}")
        state = await self.virtual_agent.run(state, config)
        logger.info(f"-------------VirtualAgent_node response: {state['messages'][-1]}")
        return Command(
            update={
                "messages": state["messages"], 
                "citations": state.get("citations", []),
                "api_call_history": state.get("api_call_history", []),
                "crm_response": state.get("crm_response", {})
                }, 
            goto="output_guardrail")

    @log_execution
    async def reviwerAgent_node(self, state: GraphState, config: RunnableConfig) -> GraphState:
        conversation_id = config.get("configurable", {}).get("thread_id", "unknown")
        logger = get_logger(conversation_id)
        logger.setLevel(logging.INFO)
        state = await self.output_guardrail.run(state, config)
        logger.info(f"Reviewer Agent response:: {state['messages'][-1]}")

        return state

    def _build_graph(self) -> StateGraph:
        """
        Updated graph builder with new legal CRM search workflow.
        """
        self.base_logger.info("Building state graph")
        # Initialize state graph
        builder = StateGraph(GraphState)

        # Define all nodes
        builder.add_node("greeting", self.greeting_node)
        builder.add_node("input_guardrail", self.input_guardrail_node)
        builder.add_node("virtual_agent", self.virtualAgent_node)
        builder.add_node("output_guardrail", self.reviwerAgent_node)

        # Define all transitions
        builder.add_conditional_edges(START, self.start_conditional_node,{
                                            "greeting": "greeting",      # Map return value to node name
                                            "input_guardrail": "input_guardrail"   # Map return value to node name
                                        })

        # Updated input guardrail conditional with new routing
        builder.add_conditional_edges("input_guardrail", self.input_guardrail_conditional, {
                                            "__end__": END,
                                            "virtual_agent": "virtual_agent"
        })

        # Keep existing edges
        builder.add_edge("greeting", END)
        builder.add_edge("output_guardrail", END)
        self.base_logger.info("Graph built successfully = " + str(builder))
        graph = builder.compile(self.checkpointer)
        self.base_logger.info("Graph compiled successfully = " + str(graph))

        # from langchain_core.runnables.graph import MermaidDrawMethod
        # graph.get_graph().draw_mermaid_png(output_file_path="Full_workflow.png", draw_method=MermaidDrawMethod.PYPPETEER)

        return graph

    def _create_runtime_config(self, thread_id, user_role, channel_type, session_start, avatar_id, user_info):
        """Create the runtime configuration dictionary."""
        return {
            "configurable": {
                "thread_id": thread_id,
                "user_role": user_role,
                "channel_type": channel_type,
                "session_start": session_start,
                "avatarId": avatar_id,
                "userInfo": user_info
            }
        }

    @log_execution
    async def _process_chat_history(self, conversation_id, api_config):
        """Load chat history from API or use in-memory history based on session state."""
        logger = get_logger(conversation_id)
        logger.setLevel(logging.INFO)
        is_conversation_active = self.conversation_manager.is_conversation_active(conversation_id)
        if is_conversation_active:
            logger.info(f"Continuing existing session for conversation {conversation_id}. Using in-memory history.")
            return []

        logger.info(f"Session start detected for conversation {conversation_id}. Loading chat history from API.")
        try:
            chat_history = await self.conversation_manager.load_conversation_history(conversation_id, api_config)
            logger.info(f"Loaded {len(chat_history)} messages from API for conversation {conversation_id}")
            if len(chat_history)>2:
                chat_history = chat_history[2:]
            if len(chat_history)>10:
                return chat_history[-10:]
            return chat_history
        except Exception as e:
            logger.error(f"Error loading chat history from API: {str(e)}")
            return []

    def _prepare_graph_input(self, input_message, chat_history):
        """Prepare the input for the graph based on session state and history."""
        new_message = HumanMessage(
            content=input_message,
            response_agent='graph_input')

        if chat_history:
            return {"messages": chat_history + [new_message]}
        return {"messages": [new_message]}


    def _create_text_output(self, ai_response, result):
        """Create the text output dictionary with references and suggestions."""
        return {
            "type": "text",
            "data": ai_response.content,
            "referenceData": result.get("citations", []),
            "faQsData": [clean_text(item) for item in result.get("suggestions", [])],
        }


    @log_execution
    async def _generate_voice_output(self, text_content, avatar_id, logger):
        """Generate voice output from text content."""
        try:
            output_voice = self.voice_processor.run(text_content, avatar_id)
            if output_voice["status"] == "success":
                logger.info("Voice output included")
                return {
                    "type": "voice",
                    "data": output_voice["output"]
                }
        except Exception as e:
            logger.error(f"Error generating voice output: {str(e)}")
        return None


    def _process_api_calls(self, api_call_history, logger):
        """Process API calls and create widget output if needed."""
        if not api_call_history:
            return None
        else:
            return {"type": "widget", "data": api_call_history}
    
    @log_execution
    async def run(self, user_input: dict, api_config: dict = None) -> List:
        """
        Run the orchestrator with the given user input and load conversation history from API.

        Args:
            user_input: Dictionary containing user input and conversation info
            api_config: Dictionary containing API configuration for conversation history
                    {
                        "base_url": "https://api.example.com",
                        "headers": {"Authorization": "Bearer token"},
                        "timeout": 30
                    }
        """
        conversation_id = user_input["conversationId"]
        logger = get_logger(conversation_id)
        logger.setLevel(logging.INFO)
        logger.info("Starting conversation")
        logger.info(f"Running orchestrator with payload: {user_input}")
        input_message = user_input["conversationMessage"]
        logger.info(f"Running orchestrator with user input message: {input_message}")
        is_voice_output = user_input["outputType"] == "VOICE"
        user_role = user_input["role"]
        channel_type = user_input["channel"]
        is_session_start = user_input["sessionStart"]
        avatar_id = user_input["avatarId"]
        user_info = reduce_personal_info(user_input["personalInfo"])
        logger.info(f"Running orchestrator with user info: {user_info}")

        # Add language detection
        user_info["language"] = detect_language(input_message)

        # Create unique thread ID and runtime configuration
        thread_id = str(conversation_id)
        runtime_config = self._create_runtime_config(
            thread_id, user_role, channel_type, is_session_start, avatar_id, user_info
        )

        # Process chat history
        chat_history = []
        if conversation_id!="0":
            chat_history = await self._process_chat_history(conversation_id, api_config)

        # Prepare input for the graph
        graph_input = self._prepare_graph_input(input_message, chat_history)

        # Run the graph and get results
        result = await self.graph.ainvoke(graph_input, runtime_config)

        # Format and prepare outputs
        ai_outputs = []

        # Add text output
        ai_response = AIMessage(content="")
        if isinstance(result["messages"][-1], AIMessage):
                ai_response = result["messages"][-1]  # Second-to-last AI message
        text_output = self._create_text_output(ai_response, result)
        ai_outputs.append(text_output)

        # Add voice output if needed
        if is_voice_output:
            voice_output = await self._generate_voice_output(ai_response.content, avatar_id, logger)
            if voice_output:
                ai_outputs.append(voice_output)

        # Add API widget output if available
        api_widget_output = self._process_api_calls(result.get("api_call_history", []), logger)
        if api_widget_output:
            ai_outputs.append(api_widget_output)

        logger.info(f"Orchestrator run completed for thread {thread_id}")
        logger.info(f"-----------------------------completed--------------------- \n\n")
        return ai_outputs


if __name__ == "__main__":
    import json
    import asyncio
    import uuid

    userInfo_file = "tests/userInfo.json"
    configs_file = "configs/orchestrator_configs.yaml"
    agent_configs_file = "configs/agents_config.yaml"
    # API configuration for conversation history
    api_config = {
        "base_url": "http://10.254.115.17:8090",  # Your gateway URL
        "headers": {
            # "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        "timeout": 30
    }

    with open(userInfo_file, "r") as file:
        userInfo = json.load(file)

    orchestrator = Orchestrator()

    ## concurrecy test 
    async def simulate_user(user_id, message):
        input_data = {
            "userId": user_id,
            "conversationId": 662256,
            "avatarId": 0,
            "sessionStart": False,
            "conversationTitle": "Test Run",
            "inputType": "TEXT",
            "outputType": "TEXT",
            "channel": "PRIVATE",
            "personId": 204319,
            "conversationMessage": message,
            "role": "EMPLOYEE",
            "attachments": [],
            "personalInfo": userInfo
        }
        result = await orchestrator.run(input_data, api_config)
        print(f"\nOutput for user {user_id}: {result}\n")

    async def run_concurrent_test(user_query):
        await asyncio.gather(
            simulate_user(1001, user_query)
            # simulate_user(1002, "What is the reimbursement policy?")
        )

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["bye", "exit"]:
            print("Bot: Goodbye!")
            break
 
        asyncio.run(run_concurrent_test(user_input))