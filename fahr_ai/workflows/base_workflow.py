from abc import abstractmethod
from typing import Dict, Any


class BaseWorkflow():
    """
    Interface for assistant-level workflows.
    """

    @abstractmethod
    def build_workflow(self) -> Any:
        """
        Builds or compiles the workflow (e.g. a LangGraph object).
        """
        pass

    @abstractmethod
    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs the workflow given a state.
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """
        Resets internal agent state or memory if applicable.
        """
        pass

    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """
        Returns internal state.
        """
        pass