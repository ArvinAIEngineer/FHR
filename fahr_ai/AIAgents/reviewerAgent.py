import sys
import yaml
# Add the current directory to sys.path
sys.path.append("./")

from typing import Dict, Optional, List
from langchain.chat_models.base import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel
from AIAgents.base_agent import BaseAgent, GraphState
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, AIMessage
from utils.logger import get_logger
import logging 

import os
from pydantic import BaseModel, Field
from typing import Optional, Union

os.environ['NO_PROXY'] = '10.254.115.17, 10.254.140.69'


class ReviewerResponse(BaseModel):
    """Structured response from the reviewer agent"""
    raise_ticket: bool = Field(description="Whether to raise a support ticket")
    final_answer: str = Field(description="The final response to send to the user")
    review_notes: Optional[str] = Field(default=None, description="Internal notes about the review (not sent to user)")

class ReviewerAgent(BaseAgent):
    def __init__(self,
                 llm_model: Optional[BaseChatModel] = None,
                 config_path: str = "./configs/agents_config.yaml",
                 ):
        self.logger = get_logger()
        self.logger.setLevel(logging.INFO)
        self.logger.info("Initializing ReviewerAgent")
        self.llm = llm_model
        
        # Create structured LLM
        self.structured_llm = self.llm.with_structured_output(ReviewerResponse)

        # Load prompt from YAML file
        self.logger.info(f"Loading config from {config_path}")
        with open(config_path, 'r', encoding="utf-8") as file:
            config = yaml.safe_load(file)
            self.reviewer_prompt = ChatPromptTemplate.from_messages([
                ("system", config['reviewerAgent_prompt']['system']),
                ("human", config['reviewerAgent_prompt']['human'])
            ])

    async def run(self, state: GraphState, config: RunnableConfig) -> GraphState:
        thread_id = int(config["configurable"]["thread_id"])
        self.logger = get_logger(thread_id)
        self.logger.setLevel(logging.INFO)
        # Get the user question from state
        self.logger.info(f"Running ReviewerAgent with state: {state}")
        # Check if the last 2 messages are both AI messages
        messages = state['messages']

        user_query = ""
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                user_query = msg.content
                break

        # # Get AI response content if available
        # ai_response = ""
        # if len(messages) >= 2 and isinstance(messages[-1], AIMessage):
        #     # if isinstance(messages[-2], AIMessage):
        #     #     ai_response = messages[-2].content  # Second-to-last AI message
        #     # elif isinstance(messages[-2], HumanMessage):
        #     ai_response = messages[-1].content   # Last AI message

        # Extract AI messages from conversation history
        def get_recent_ai_messages(messages, count=2):
            """Extract the most recent AI messages from the conversation."""
            ai_messages = [msg.content for msg in reversed(messages) if isinstance(msg, AIMessage)]
            return ai_messages[:count]

        # Get recent AI responses
        recent_ai_messages = get_recent_ai_messages(messages)
        last_ai_message = recent_ai_messages[0] if recent_ai_messages else ""
        second_last_ai_message = recent_ai_messages[1] if len(recent_ai_messages) > 1 else ""

        # Format the prompt with user question and AI responses
        formatted_prompt = self.reviewer_prompt.format(
            user_question=user_query,
            ai_response_1=second_last_ai_message,
            ai_response_2=last_ai_message
        )
        try:
            # Use structured output for reliable parsing
            reviewer_response: ReviewerResponse = await self.structured_llm.ainvoke([
                HumanMessage(content=formatted_prompt)
            ])
            
            self.logger.info(f"Structured response from ReviewerAgent: raise_ticket={reviewer_response.raise_ticket}")
            if reviewer_response.review_notes:
                self.logger.info(f"Review notes: {reviewer_response.review_notes}")
            
            # Update state with the reviewed response
            state['messages'].append(AIMessage(content=reviewer_response.final_answer))
            
            # Set raise_ticket flag in state
            state['raise_ticket'] = reviewer_response.raise_ticket
            
            if reviewer_response.raise_ticket:
                self.logger.info("Raise ticket flag set to True - support ticket required")
                state["citations"]=[]
            
        except Exception as e:
            self.logger.error(f"Error getting structured response from reviewer: {e}")
            # Fallback: return original AI response with safe defaults
            state['raise_ticket'] = False
            self.logger.info("Fallback: Using original AI response")
        
        return state


#Example usage
if __name__ == "__main__":
    import asyncio
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(model="llama3.3:latest",temperature=0.0, openai_api_base="http://10.254.140.69:11434/v1", openai_api_key="AI-key")

    reviewer_agent = ReviewerAgent(
            llm_model=llm,
            config_path="./configs/agents_config.yaml"
    )

    # Example state
    state = {
        'messages': [
            HumanMessage(content="What is the capital of France?"),
            AIMessage(content="we incounter internal server error ip 10.254.115.19 ")
        ]
    }

    response = asyncio.run(reviewer_agent.run(state))  # Await the async method
    print(response)
