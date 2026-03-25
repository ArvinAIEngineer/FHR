import os,json
os.environ['NO_PROXY'] = '10.254.115.17, 10.254.140.69'
import logging 
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage,trim_messages
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode, tools_condition
from AIAgents.base_agent import BaseAgent, GraphState
from utils.logger import get_logger
import yaml
from typing import Annotated, List, Any
from langchain_core.runnables import RunnableConfig
from utils.utils import extract_reference_data, extract_tool_outputs_from_events, filter_think
from langchain_core.messages.utils import count_tokens_approximately
from langchain_core.messages import RemoveMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langmem.short_term import SummarizationNode
from langchain_core.runnables import RunnableLambda

class VirtualAgent(BaseAgent):
    def __init__(self, config_path="./configs/agents_config.yaml", llm_model=None, agent_name="VirtualAgent"):
        self.logger = get_logger()
        self.logger.setLevel(logging.INFO)
        self.logger.info("Initializing VirtualAgent")

        self.llm_model = llm_model
        
        # Load config
        with open(config_path, 'r', encoding="utf-8") as file:
            self.config = yaml.safe_load(file)
            self.prompt_template = self.config['virtualAgent_prompt']
            self.failure_messages = self.config["failure_messages"]
            self.use_summarization = self.config.get("use_summarization", False)
            self.use_trimming = self.config.get("use_trimming", False)


        if self.use_summarization and self.use_trimming:
            raise ValueError("Only one of summarization or trimming should be enabled.")

        # Tools
        from AIAgents.tools_registry import get_legalAgent_tools
        self.tools = get_legalAgent_tools()
        print(f"Discovered tools: {[t.name for t in self.tools]}")

        self.llm_with_tools = self.llm_model.bind_tools(self.tools)

        # Build LangGraph internally
        self.graph_builder = StateGraph(GraphState)
        self.graph_builder.add_node("planner", self._planner_node)
        self.graph_builder.add_node("tools", ToolNode(tools=self.tools))

        self.graph_builder.add_edge(START, "planner")
        self.graph_builder.add_conditional_edges("planner", tools_condition)
        if self.use_summarization:
            self.summarization_node = SummarizationNode(
                        token_counter=count_tokens_approximately,
                        model=self.llm_model,
                        max_tokens=10000,
                        max_summary_tokens=5000,
                        output_messages_key="llm_input_messages",  
                        
                    )
            self.graph_builder.add_node("summarize", self.summarization_node)
            self.graph_builder.add_edge("tools", "summarize")
            self.graph_builder.add_edge("summarize", "planner")

        else:
            self.graph_builder.add_node("trim", RunnableLambda(self.trim_node))  # 👈 wrap the function
            self.graph_builder.add_edge("tools", "trim")
            self.graph_builder.add_edge("trim", "planner")

        self.graph = self.graph_builder.compile()

    @staticmethod
    def trim_node(input):
        trimmed = trim_messages(
            input["messages"],
            strategy="last",
            max_tokens=12000,  # You can read this from config too
            token_counter=count_tokens_approximately,
            start_on="human",
            end_on=("human", "tool"),
            include_system=True,
        )
        return {"llm_input_messages": trimmed}

    def _planner_node(self, state: GraphState, config: RunnableConfig) -> GraphState:
        thread_id = config["configurable"]["thread_id"]
        user_info = config.get("configurable", {}).get("userInfo", {})
        self.logger.info(f"User nfo in configurable {user_info}")
        language = user_info.get("language", "en")
        language = {'ar': 'Arabic', 'en': 'English'}.get(language, 'English')
        logger = get_logger(thread_id)
        logger.setLevel(logging.INFO)
        current_datetime = datetime.now().strftime("%d-%m-%Y")
        agent_prompt = self.prompt_template.format(language=language, current_datetime=current_datetime) + "\nEmployee_Profile" + json.dumps(user_info, indent=2)
        system_message = [SystemMessage(content=agent_prompt)]
        for msg in state.get("llm_input_messages", []):
            logger.info(f"##llm_input_messages: {msg.type.upper()}: {msg.content}")
        messages_history = state.get("llm_input_messages") or state.get("messages", [])
        full_history = system_message + messages_history

        self.logger.info(f"full history from planner: {full_history}")

        response = self.llm_with_tools.invoke(full_history, config=config)
        logger.info(f"[Planner Node] Response: {response}")
        return {"messages": [response]}

    async def run(self, state: GraphState, config: RunnableConfig) -> GraphState:
        thread_id = config["configurable"]["thread_id"]
        # Extract user/channel info from config
        config_data = config.get("configurable", {})
        user_info = config_data.get("userInfo", {})
        language = user_info.get("language", "en")
        logger = get_logger(thread_id)
        logger.setLevel(logging.INFO)

        messages_dict = {"messages": [RemoveMessage(REMOVE_ALL_MESSAGES)] + state["messages"]}
        logger.info(f"Running LegalAgent via internal LangGraph on messages: {messages_dict} ")
        
        vitrual_ai_message = None
        all_events = []

        async for event in self.graph.astream(messages_dict, config=config):
            all_events.append(event)  # collect for extraction later
            for value in event.values():
                if isinstance(value, list):
                    for msg in value:
                        if isinstance(msg, AIMessage):
                            tool_calls = msg.additional_kwargs.get("tool_calls", [])
                            for call in tool_calls:
                                logger.info(f"Function called: {call.get('function', {}).get('name')}")
                                logger.info(f"Function arguments: {call.get('function', {}).get('arguments')}")
                        if isinstance(msg, AIMessage) and msg.response_metadata.get("finish_reason") == "stop":
                            vitrual_ai_message = filter_think(msg)
                            if vitrual_ai_message:
                                if not getattr(vitrual_ai_message, "response_agent", ""):
                                    vitrual_ai_message.response_agent = "virtual_agent"
                        if isinstance(msg, ToolMessage):
                            if msg.name == 'get_knowledge_documents':
                                # # with chunkText
                                # state['citations']= (msg.content)
                                # without chunkText
                                # Step 1: Parse the string to Python list
                                parsed_data = json.loads(msg.content)
                                # Step 2: Extract only the metadata dict from each inner list
                                citations = [item for sublist in parsed_data for item in sublist if isinstance(item, dict)]
                                state['citations']= citations
                            logger.warning(f"Removed ToolMessage from final state")
                else:
                    logger.info(f"Unexpected event value: {value}")
            self.logger.info(f'loop complete grapgh state {state}')

        if vitrual_ai_message:
            state["messages"].append(vitrual_ai_message)

        logger.info(f"final state after clean {state}")      

        # Extract tool return values from all events
        tool_outputs = extract_tool_outputs_from_events(all_events)
        for item in tool_outputs:
            logger.info(f"[ToolOutput] Tool: {item['widgetType']}, Parsed: {json.dumps(item['data'], indent=2)}")
        state["api_call_history"] = tool_outputs

        logger.info(f"final state from legal agent  {state}")

        return state
