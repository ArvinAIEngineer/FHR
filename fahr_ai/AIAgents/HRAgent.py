import sys
import yaml
# Add the current directory to sys.path
sys.path.append("./")

from typing import Optional, Dict, Any, List
from langchain.chat_models.base import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from AIAgents.base_agent import BaseAgent, GraphState
from utils.logger import get_logger
from utils.utils import _extract_citations
import logging 
import os
os.environ['NO_PROXY'] = '10.254.140.69'

class HRAgent(BaseAgent):
    def __init__(self,
                 config_path: str = "./configs/agents_config.yaml",
                 llm_model: Optional[BaseChatModel] = None,
                 ragworkflow_app: Any = None,
                 agent_name: str = "HRAgent"):
        """
        Initialize the HR Agent.

        :param rag_agent: An instance of the RAGAgent class responsible for handling document retrieval.
        """
        self.logger = get_logger()
        self.logger.setLevel(logging.INFO)
        self.logger.info("Initializing HRAgent")
        # Initialize LLM with default if not provided
        self.llm_model = llm_model

        # Load prompt from YAML file
        self.logger.info(f"Loading config from {config_path}")
        with open(config_path, 'r', encoding="utf-8") as file:
            self.config = yaml.safe_load(file)
            self.prompt_template = self.config['hrAgent_prompt']
            self.failure_messages = self.config["failure_messages"]
        
        # RAGWorkflow app
        self.app = ragworkflow_app


    async def run(self, state: GraphState, config: RunnableConfig) -> GraphState:
        """
        Execute the RAG workflow using the LangGraph application.

        Args:
            state: The current graph state containing memory, messages, etc.

        Returns:
            Updated graph state with RAG-enhanced output.
        """
        # Convert GraphState to EnhancedState format for the workflow
        self.logger.info(f"Running HRAgent with state: {state}")
        # Get the last human message for context retrieval
        user_query = ""
        for msg in reversed(state['messages']):
            if isinstance(msg, HumanMessage):
                user_query = msg
                break

        # Run the workflow with all the messages
        self.logger.info(f"Running workflow with user query: {user_query.content}")
        messages_state = {
            "messages": user_query,  # Make a copy of all messages
            "memory": state["memory"] if hasattr(state, "memory") else {}
        }
        result = await self.app.ainvoke(messages_state, config)

        # Process retrieval results
        ai_messages = [msg for msg in result["messages"] if isinstance(msg, AIMessage)]
        retrieved_info = ""
        if ai_messages:
            retrieved_info = ai_messages[-1].content

        # Get the inquery message
        language = config["configurable"]["userInfo"]["language"]

        # Get messages for current language, default to English if language not supported
        messages = self.failure_messages.get(language, self.failure_messages["en"])

        # Early exit if no documents were found
        stage = result.get("memory", {}).get("stage", "")
        if stage == "skipped_due_to_no_documents":
            self.logger.info("No relevant documents found; skipping LLM call.")
            return GraphState(
                messages=state["messages"] + [AIMessage(content=messages["no_documents"])],
                citations=[],
                suggestions=[],
            )

        if stage == "fallback" or not retrieved_info.strip():
            fallback_reason = result.get("memory", {}).get("fallback_reason", "unknown issue")
            fallback_msg = messages["fallback"].format(fallback_reason=fallback_reason)
            return GraphState(
                messages=state["messages"] + [AIMessage(content=fallback_msg)],
                citations=[],
                suggestions=[]
            )

        # Use the retrieved information to generate the final response
        formatted_prompt = self.prompt_template.format(
            user_question=user_query.content,
            retrieved_info=retrieved_info
        )

        # Generate response
        self.logger.info(f"Formatted prompt for LLM, to be used for generating response: {formatted_prompt}")
        response = await self.llm_model.ainvoke([HumanMessage(content=formatted_prompt)])
        self.logger.info(f"Generated response: {response}")

        # return response.content
        return GraphState(
             messages=state["messages"] + [AIMessage(content=response.content)],
             citations=  _extract_citations(result),
             suggestions=[]
        )

    def reset(self) -> None:
        """
        Resets the agent's internal state or memory.
        """
        self.logger.info("Resetting agent's internal state")
        self._internal_memory = {}

    def get_state(self) -> Dict[str, Any]:
        """
        Returns the agent's internal state (not the graph state).
        """
        self.logger.info("Getting agent's internal state")
        return self._internal_memory

    @property
    def name(self) -> str:
        """
        A human-readable name for the agent.
        """
        return self._name



#Example usage
if __name__ == "__main__":
    import asyncio
    from langchain_ollama import ChatOllama

    # Initialize models and vectorstore
    llm = ChatOllama(model="llama3.2:3b", temperature=0)

    # Initialize HRAgent
    agent = HRAgent(llm_model=llm)

    # Create a test query
    test_query = "Explain what a leave balance is based on law in 2019 and what is the difference regarding the previous years"

    # Create a GraphState with the query as a message
    state = GraphState(
        messages=[HumanMessage(content=test_query),
                  AIMessage(content="")],
        memory={},
        suggestions=[]
    )

    print(f"Sending query: {test_query}\n")
    print("Processing...\n")

    # Run the agent with the query
    response = agent.run(state)

    # Print the result (last AI message)

    print("=" * 80)
    print("AGENT RESPONSE:")
    print(response)
    print("=" * 80)
    print("\n")

