# Standard library imports
import os
import sys
from typing import List, Literal, Any
import time 
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
from AIAgents.APIAgent import APIAgent
from AIAgents.base_agent import GraphState
from AIAgents.LegalAgent import LegalAgent
from AIAgents.reviewerAgent import ReviewerAgent
from AIAgents.SuggestionAgent import SuggestionAgent
from api import VectorstoreConnector
from configs.secrets import (
    AGENTS_CONFIG_PATH,
    ORCHESTRATOR_CONFIG_PATH,
    ROLE_AGENT_MAPPING_PATH,
    ROLE_API_MAPPING_PATH,
)
from modules.greetingHandler import GreetingHandler
from modules.tts_voice import TTSVoiceProcessor
from modules.conversationManager import ConversationManager
from workflows import RAGWorkflow
from utils.logger import get_logger, log_execution
from utils.utils import clean_text, detect_language

# Constants
MAX_VISITS_PER_AGENT = 1
PROXY_SETTINGS = {'NO_PROXY': '10.254.115.17, 10.254.140.69'}

# Apply environment settings
os.environ.update(PROXY_SETTINGS)


class QueryGuardrailSchema(TypedDict):
    """Schema for query guardrail validation results."""
    is_relevant: bool
    requires_auth: bool
    allow: bool
    message: str
    detected_category: Literal['HR', 'legal', 'general']


class RouterState(TypedDict):
    """Worker router state definition.

    If no workers needed, route to `reviwer_agent`.
    """
    next: Literal["hr_agent", "legal_agent", "api_agent", "reviwer_agent"]
    messages: str


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
            role_agent_mapping_path: str = ROLE_AGENT_MAPPING_PATH,
            role_api_mapping_path: str = ROLE_API_MAPPING_PATH,
            avatar_profiles_path: str = "./configs/avatar_profiles.json"
    ):
        self.base_logger = get_logger()
        self.base_logger.setLevel(logging.INFO)
        # Load all configurations
        self.configs = self._load_orchestrator_config(orchestrator_configs_file)
        self._load_role_mappings(role_agent_mapping_path, role_api_mapping_path)
        self._load_avatar_profiles(avatar_profiles_path)

        # Initialize LLM
        self.llm = self._initialize_llm()

        # Initialize ragworkflow
        ragworkflow_app = self._initialize_ragworkflow()
        
        # Initialize all agents
        self._initialize_agents(agents_configs_file, ragworkflow_app)

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
            self.system_prompt = configs["chatAgent_prompt"]
            self.chatAgent_prompt_template = self.system_prompt
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
                self.always_allowed_agents = role_config.get("always_allowed_agents", [])

            with open(role_api_path, "r") as f:
                self.role_api_mapping = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.base_logger.error(f"Error loading role mappings: {e}")
            raise

    def _load_avatar_profiles(self, profiles_path: str) -> None:
        """Load avatar profiles from JSON file."""
        try:
            with open(profiles_path, "r") as f:
                self.avatar_profiles = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.base_logger.error(f"Error loading avatar profiles: {e}")
            raise

    def _initialize_llm(self) -> ChatOpenAI:
        """Initialize the LLM with configuration parameters."""
        return ChatOpenAI(
            model_name=self.configs["LLM_model_name"],
            openai_api_base=self.configs["openai_api_base_url"],
            openai_api_key=self.configs["openai_api_key"],
            temperature=0
        )

    def _initialize_ragworkflow(self) -> Any:
        """Initialize and return the ragworkflow."""
        vectorstore_connector = VectorstoreConnector()
        vectorstore = vectorstore_connector.get_vectorstore()
        # Initialize RAG workflow
        self.base_logger.info("Initializing RAG workflow")
        ragWorkflow = RAGWorkflow(
            vectorstore=vectorstore,
            llm_model=self.llm,
            config_path=self.configs['rag_workflow_config']
        )
        return ragWorkflow.app

    @log_execution
    def _initialize_agents(self, agents_config_path: str, ragworkflow_app: Any) -> None:
        """Initialize all agent instances."""

        # API Agent
        self.base_logger.info(f"FAHR endpoints: {self.fahr_endpoints}")
        self.api_agent = APIAgent(
            openAPI_file_path=self.fahr_endpoints,
            llm_model=self.llm,
            role_api_mapping=self.role_api_mapping,
            auth_config=None
        )

        # Legal Agent
        self.legal_agent = LegalAgent(
            llm_model=self.llm,
            config_path=agents_config_path,
            ragworkflow_app=ragworkflow_app,
            agent_name="LegalAgent"
        )

        # Reviewer Agent
        self.reviewer_agent = ReviewerAgent(
            llm_model=self.llm,
            config_path=agents_config_path
        )

        # Suggestion Agent
        self.suggestion_agent = SuggestionAgent(
            llm_model=self.llm,
            config_path=agents_config_path,
            agent_name="SuggestionAgent"
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
            state["messages"].append(AIMessage(content=response.get("message", "")))
        state["guardrail_response"] = response
        state["visited_agents"] = {}
        state["citations"] = []
        return state
    
    @log_execution
    async def avatar_switch_node(self, state: GraphState, config: RunnableConfig) -> GraphState:
        """Handle avatar switching when domain mismatch is detected"""
        conversation_id = config.get("configurable", {}).get("thread_id", "unknown")
        logger = get_logger(conversation_id)
        logger.setLevel(logging.INFO)
        response = state["guardrail_response"]
        q_domain = response["detected_category"]
        
        logger.info(f"Processing avatar switch for domain: {q_domain}")
        
        output_avatar = None
        switch_avatar = False
        
        # Find matching avatar for the detected domain
        try:
            for key, profile in self.avatar_profiles.get("profiles", {}).items():
                logger.debug(f"Checking profile {key}: {profile}")
                if profile.get("domain") == q_domain:
                    output_avatar = int(key)
                    switch_avatar = True
                    logger.info(f"Found matching avatar {output_avatar} for domain {q_domain}")
                    break
        except Exception as e:
            logger.error(f"Error finding avatar for domain {q_domain}: {e}")
        
        # Set the switch_avatar state
        if switch_avatar:
            state["switch_avatar"] = {"switch": True, "avatarId": output_avatar}
            logger.info(f"Avatar switch set: {state['switch_avatar']}")
        else:
            logger.warning(f"No avatar found for domain {q_domain}")
            state["switch_avatar"] = {"switch": False, "avatarId": None}
        
        return state

    def input_guardrail_conditional(self, state: GraphState, config: RunnableConfig) -> Literal[
        "__end__", "avatar_switch", "router_agent"]:
        """
        Updated conditional logic for input guardrail routing.
        Routes based on relevance, domain mismatch, and category.
        """
        if len(state["messages"])>10:
            state["messages"] = state["messages"][-10:]
        channel_type = config.get("configurable", {}).get("channel_type", "UNKNOWN")
        conversation_id = config.get("configurable", {}).get("thread_id", "unknown")
        logger = get_logger(conversation_id)
        logger.setLevel(logging.INFO)
        response = state["guardrail_response"]
        q_domain = response["detected_category"]

        # First check: If not relevant, end immediately
        if not response["is_relevant"]:
            return "__end__"

        # Second check: If public channel and requires auth, end
        if channel_type == "PUBLIC" and response.get("requires_auth", False):
            return "__end__"

        # Get avatar profile safely for domain mismatch check
        input_avatar = config.get("configurable", {}).get("avatarId", "UNKNOWN")
        try:
            if input_avatar == "UNKNOWN":
                avatar_profile = {"domain": "UNKNOWN"}
            else:
                avatar_profile = self.avatar_profiles["profiles"].get(str(input_avatar), {"domain": "UNKNOWN"})
        except Exception as e:
            logger.error(f"Error accessing avatar profile: {e}")
            avatar_profile = {"domain": "UNKNOWN"}
        
        current_domain = avatar_profile.get("domain", "UNKNOWN")
        
        # Third check: Domain mismatch - route to avatar switch
        if q_domain != current_domain and q_domain != "general":
            logger.info(f"Domain mismatch detected: current={current_domain}, detected={q_domain}")
            return "avatar_switch"
        else:
            # Fallback for any other categories
            return "router_agent"


    def start_conditional_node(self, state: GraphState, config: RunnableConfig) -> Literal[
        "input_guardrail", "greeting"]:
        session_start = config.get("configurable", {}).get("session_start", False)
        conversation_id = config.get("configurable", {}).get("thread_id", "unknown")
        if session_start or conversation_id==0:
            return "greeting"
        else:
            return "input_guardrail"

    async def greeting_node(self, state: GraphState, config: RunnableConfig)-> GraphState:
        channel_type = config["configurable"]["channel_type"]
        userInfo = config["configurable"]["userInfo"]
        language = userInfo.get("language", "en")
        user_name = userInfo["full_name"]
        output_msg = await self.greeter.run(channel_type=channel_type, user_name=user_name, language=language)
        state["messages"].append(AIMessage(content=output_msg))
        return state

    def inject_allowed_agents_to_chatAgent(self, base_prompt: str, allowed_agents: List[str], user_role: str):
        """Inject the allowed agents into the base prompt."""
        allowed_agents_str = ", ".join(allowed_agents).strip()
        return base_prompt.replace("<ALLOWED AGENTS>", allowed_agents_str).replace("<USER ROLE>", user_role)

    @log_execution
    async def LegalAgent_node(self, state: GraphState, config: RunnableConfig) -> Command[Literal["router_agent"]]:
        # Process the state using LegalAgent - returns a string directly
        conversation_id = config.get("configurable", {}).get("thread_id", "unknown")
        logger = get_logger(int(conversation_id))
        logger.setLevel(logging.INFO)

        state = await self.legal_agent.run(state, config)
        logger.info(f"-------------LegalAgent_node response: {state['messages'][-1]}")
        return Command(
            update={
                "messages": state["messages"], 
                "citations": state.get("citations", []),
                "crm_response": state.get("crm_response", {})
                }, 
            goto="router_agent")

    @log_execution
    async def APIAgent_node(self, state: GraphState, config: RunnableConfig) -> Command[Literal["router_agent"]]:
        # Process the state using APIAgent - returns a string directly
        conversation_id = config.get("configurable", {}).get("thread_id", "unknown")
        logger = get_logger(conversation_id)
        logger.setLevel(logging.INFO)
        output = await self.api_agent.run(state, config)
        logger.info(f"API Agent response: {output}")
        # Append the response as an AIMessage
        if isinstance(output, dict) and "output" in output:
            content = output["output"]
        else:
            content = str(output)
        state["messages"].append(AIMessage(content=content))
        return Command(update={
            "messages": state["messages"],
            "api_call_history": state["api_call_history"]
        }, goto="router_agent")

    @log_execution
    async def reviwerAgent_node(self, state: GraphState, config: RunnableConfig) -> GraphState:
        conversation_id = config.get("configurable", {}).get("thread_id", "unknown")
        logger = get_logger(conversation_id)
        logger.setLevel(logging.INFO)
        state = await self.reviewer_agent.run(state, config)
        logger.info(f"Reviewer Agent response:: {state}")

        return state

    @log_execution
    async def suggestionAgent_node(self, state: GraphState, config: RunnableConfig) -> GraphState:
        # Process the state to append suggestion based on the context
        state = await self.suggestion_agent.run(state, config)
        return state

    @log_execution
    async def chatAgent_node(
            self, state: GraphState, config: RunnableConfig
    ) -> Command[Literal["legal_agent", "api_agent", "reviwer_agent"]]:
        conversation_id = config.get("configurable", {}).get("thread_id", "unknown")
        logger = get_logger(conversation_id)
        logger.setLevel(logging.INFO)
        state["switch_avatar"] = {}

        user_role = config["configurable"]["user_role"].lower()
        userInfo = config["configurable"]["userInfo"]
        language = userInfo.get("language", "en")

        # Format the chat agent prompt with user info
        chatAgent_prompt = self.chatAgent_prompt_template.format(personal_info=json.dumps(userInfo), language=language)

        # this is prompt injection based on roles, these two lines can be commented out without consequences
        allowed_agents: list = self.role_agent_mapping.get(user_role, []) + self.always_allowed_agents
        chatAgent_prompt = self.inject_allowed_agents_to_chatAgent(chatAgent_prompt, allowed_agents, user_role)

        logger.info(f"reduced chat agent prompt based on: {user_role}")

        messages = [{"role": "system", "content": chatAgent_prompt}] + state["messages"]

        # Pass the formatted messages to the LLM
        response = await self.llm.with_structured_output(RouterState).ainvoke(messages)
        logger.info(f"Chat Agent response: {response}")

        if response['next'] in allowed_agents:
            # Initialize count for this agent if it doesn't exist
            if response['next'] not in state["visited_agents"]:
                state["visited_agents"][response['next']] = 0
            # Log the current state of visited_agents for debugging
            logger.info(f"Visited agents before update: {state.get('visited_agents')}")

            # Check if we can visit this agent (either not visited yet or below max visits)
            current_visits = state["visited_agents"].get(response['next'], 0)

            if current_visits < MAX_VISITS_PER_AGENT:
                # Increment the visit count for this agent
                state["visited_agents"][response['next']] = current_visits + 1
                logger.info(
                    f"Incremented visits for {response['next']} to {state['visited_agents'][response['next']]}")
                goto = response['next']
                # Append the LLM response as an AIMessage
                state["messages"].append(AIMessage(content=response["messages"]))
            else:
                logger.info(f"Maximum visits reached for agent: {response['next']} (visits: {current_visits})")
                goto = "reviwer_agent"
        else:
            logger.info(f"agent not allowed: {response['next']} for user role: {user_role}")
            # Append the LLM response as an AIMessage
            state["messages"].append(AIMessage(content=response["messages"]))
            goto = "reviwer_agent"


        logger.info(f"-------------Orchestrator response: {response['messages']}")
        if goto == "hr_agent":
            goto="legal_agent"
        logger.info(f"chatAgent decided to goto: {goto}")

        return Command(goto=goto, 
                       update={
                           "messages": state["messages"],
                           "switch_avatar": state["switch_avatar"]
                        })

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
        builder.add_node("avatar_switch", self.avatar_switch_node)
        builder.add_node("legal_agent", self.LegalAgent_node)
        builder.add_node("router_agent", self.chatAgent_node)
        builder.add_node("api_agent", self.APIAgent_node)
        builder.add_node("reviwer_agent", self.reviwerAgent_node)
        builder.add_node("suggestion_agent", self.suggestionAgent_node)

        # Define all transitions
        builder.add_conditional_edges(START, self.start_conditional_node,{
                                            "greeting": "greeting",      # Map return value to node name
                                            "input_guardrail": "input_guardrail"   # Map return value to node name
                                        })

        # Updated input guardrail conditional with new routing
        builder.add_conditional_edges("input_guardrail", self.input_guardrail_conditional, {
                                            "__end__": END,
                                            "avatar_switch": "avatar_switch",
                                            "router_agent": "router_agent"
        })

        # Keep existing edges
        builder.add_edge("greeting", "suggestion_agent")
        builder.add_edge("reviwer_agent", "suggestion_agent")
        builder.add_edge("avatar_switch", END)
        builder.add_edge("suggestion_agent", END)
        self.base_logger.info("Graph built successfully = " + str(builder))
        graph = builder.compile(self.checkpointer)
        self.base_logger.info("Graph compiled successfully = " + str(graph))
        return graph

    def _normalize_user_role(self, role):
        """Normalize the user role to a standard format."""
        valid_roles = {key.lower(): key for key in self.role_api_mapping.keys()}
        if role.lower() in valid_roles:
            return valid_roles[role.lower()]
        self.base_logger.info(f"Unknown role '{role}', falling back to 'all'")
        return "all"

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
        new_message = HumanMessage(content=input_message)

        if chat_history:
            return {"messages": chat_history + [new_message]}
        return {"messages": [new_message]}

    @log_execution
    async def _combine_ai_messages(self, result):
        """Combine the last two AI messages if they exist."""
        ai_messages = [msg for msg in result['messages']
                       if hasattr(msg, 'content') and getattr(msg, 'type', None) == 'ai']

        if len(ai_messages) < 2:
            return

        # Get the last 2 AI messages
        last_two_messages = ai_messages[-2:]
        message_contents = [msg.content for msg in last_two_messages if msg.content]

        combine_prompt = f"""
        You are a structured synthesis assistant responsible for merging two AI-generated responses into a single, clear, and complete message.

        Your tasks:
        - Extract and integrate all unique, important information from both responses.
        - Eliminate redundant or repeated content.
        - Maintain a professional, informative, and friendly tone.
        - Ensure the final message flows logically and covers all key details without hallucinations.
        - If both responses contain similar ideas, retain only the clearer or more complete version.

        ### Response 1:
        {message_contents[0]}

        ### Response 2:
        {message_contents[1]}

        Please return only the final combined response text without additional commentary or headings.
        """

        combined_response = await self.llm.agenerate([[HumanMessage(content=combine_prompt)]])
        combined_text = combined_response.generations[0][0].text.strip()

        # Replace the last AI message with the combined content
        for i in range(len(result['messages']) - 1, -1, -1):
            if getattr(result['messages'][i], 'type', None) == 'ai':
                result['messages'][i].content = combined_text
                break


    def _create_text_output(self, ai_response, result):
        """Create the text output dictionary with references and suggestions."""
        return {
            "type": "text",
            "data": clean_text(ai_response.content),
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

        api_widgets = []
        for call in api_call_history:
            status_code = call.get("status_code")
            if not status_code or status_code < 200 or status_code >= 300:
                continue

            try:
                response_body = call.get("response_body", "")
                content_str = (
                    response_body if isinstance(response_body, str)
                    else json.dumps(response_body)
                )

                api_widgets.append({
                    "widgetType": str(call.get("url", "")),
                    "data": content_str
                })
            except Exception as e:
                logger.warning(f"Skipping response from {call.get('url', 'unknown')}: {str(e)}")

        if api_widgets:
            return {"type": "widget", "data": [api_widgets[-1]]}
        return None

    def _process_switch_avatar(self, switch_avatar_data):
        # Extract avatar switching if available
        if switch_avatar_data and switch_avatar_data.get("switch", False):
            return {"type": "avatar", "data": switch_avatar_data}
        else:
            return None

    def _process_crm(self, result):
        """Process CRM agent output."""
        crm_data = result.get("crm_data", {})
        if crm_data and crm_data.get("switch", False):
            result["messages"].append(AIMessage(content=crm_data["answer"]))
        return result
    
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
        logger.info(f"Running orchestrator with user input: {user_input}")
        input_message = user_input["conversationMessage"]
        is_voice_output = user_input["outputType"] == "VOICE"
        user_role = self._normalize_user_role(user_input["role"])
        channel_type = user_input["channel"]
        is_session_start = user_input["sessionStart"]
        avatar_id = user_input["avatarId"]
        user_info = user_input["personalInfo"]

        # Add language detection
        user_info["language"] = detect_language(input_message)

        # Create unique thread ID and runtime configuration
        thread_id = str(conversation_id)
        runtime_config = self._create_runtime_config(
            thread_id, user_role, channel_type, is_session_start, avatar_id, user_info
        )

        # Process chat history
        chat_history = []
        if conversation_id!=0:
            chat_history = await self._process_chat_history(conversation_id, api_config)

        # Prepare input for the graph
        graph_input = self._prepare_graph_input(input_message, chat_history)

        # Run the graph and get results
        result = await self.graph.ainvoke(graph_input, runtime_config)

        # Add crm output to messages if exsit
        result = self._process_crm(result)

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

        # Add Avatar output if available
        avatar_ouput = self._process_switch_avatar(result.get("switch_avatar", {}))
        if avatar_ouput:
            ai_outputs.append(avatar_ouput)
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
    role_agent_map_path = "configs/role_management/role_agent_map.json"
    role_api_map_path = "configs/role_management/role_api_map.json"

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

    ## normal test 
    
    # random_id = str(uuid.uuid4())
    # user_input = {
    #         "userId": 0,
    #         "conversationId": 642,
    #         "avatarId": 0,
    #         "sessionStart": False,
    #         "conversationTitle": "string",
    #         "inputType": "TEXT",
    #         "outputType": "TEXT",
    #         "channel": "PRIVATE",
    #         "personId": 204319,
    #         "conversationMessage": "what is my leave balance?",
    #         "role": "EMPLOYEE",
    #         "attachments": [],
    #         "personalInfo":  userInfo
    #     }

    # AI_outputs = asyncio.run(orchestrator.run(user_input, api_config))
    # # Process questions

    # print(AI_outputs[0])


    ## concurrecy test 
    async def simulate_user(user_id, message):
        input_data = {
            "userId": user_id,
            "conversationId": uuid.uuid4().int & (1<<32)-1,
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
        print(f"\nOutput for user {user_id}: {result[0]}\n")

    async def run_concurrent_test():
        await asyncio.gather(
            simulate_user(1001, "What are the conditions of getting annual leave?")
            # simulate_user(1002, "What is the reimbursement policy?")
        )

    asyncio.run(run_concurrent_test())


    # from docx import Document
    # import pandas as pd
    # import uuid
    # # Load DOCX file
    # doc_path = "tests/testQs1.docx"
    # doc = Document(doc_path)

    # # Extract questions (they appear on the right side of table rows)
    # questions = []
    # for table in doc.tables:
    #     for row in table.rows:
    #         cells = row.cells
    #         if len(cells) >= 2:
    #             question = cells[1].text.strip()
    #             if question:
    #                 questions.append(question)
    # responses = []
    # # Process questions
    # for question in questions[:1]:
    #     # random_id = str(uuid.uuid4())
    #     user_input = {
    #         "userId": 0,
    #         "conversationId": 5697,
    #         "avatarId": 0,
    #         "sessionStart": False,
    #         "conversationTitle": "string",
    #         "inputType": "TEXT",
    #         "outputType": "TEXT",
    #         "channel": "PRIVATE",
    #         "personId": 965246,
    #         "conversationMessage": question,
    #         "role": "EMPLOYEE",
    #         "attachments": [],
    #         "personalInfo":  userInfo
    #     }
    #     AI_outputs = asyncio.run(orchestrator.run(user_input, api_config))
    #     responses.append(AI_outputs)
    # # Save to Excel
    # df = pd.DataFrame({"Question": questions, "Response": responses})
    # df.to_excel("tests/questions_with_responses.xlsx", index=False)

    # print("Saved to questions_with_responses.xlsx")



