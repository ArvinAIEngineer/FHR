from abc import ABC, abstractmethod
from typing import Any, Dict, Protocol, runtime_checkable, TypedDict, List
from langgraph.graph import MessagesState

# Define a generic graph state
class GraphState(MessagesState):
    memory: Dict[str, Any]         # for agent's internal use
    input: Any                     # incoming user input
    output: Any                    # result of processing                 # next node to route to
    suggestions: List[str]  # suggestions for the user
    guardrail_response: dict
    ticket_summary:str
    crm_response:dict
    citations: List[Dict]
    api_call_history:List[dict]
    switch_avatar: dict
    visited_agents: dict
    raise_ticket: bool

@runtime_checkable
class BaseAgent(Protocol):
    """
    BaseAgent defines the interface all agents must adhere to.
    Compatible with LangGraph node-based execution and async flow.
    """

    @abstractmethod
    async def run(self, state):
        """
        Core method to execute agent logic given a graph state.
        """
        pass

    def reset(self) -> None:
        """
        Optional: Resets the agent's internal state or memory if needed.
        Default implementation does nothing.
        """
        pass

    def get_state(self) -> Dict[str, Any]:
        """
        Optional: Returns the agent’s internal state (not the graph state).
        Default implementation returns an empty dictionary.
        """
        return {}

    @property
    def name(self) -> str:
        """
        Optional: A human-readable or unique name for the agent.
        Default implementation returns an empty string.
        """
        return ""
