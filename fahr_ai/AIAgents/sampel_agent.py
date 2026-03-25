class AIAgent(BaseAgent):
    def __init__(self, name: str):
        self._name = name
        self._internal_memory = {}

    async def run(self, state: GraphState) -> GraphState:
        # Sample implementation
        user_input = state.get("input", "")
        response = f"Processed: {user_input}"  # placeholder logic
        state["output"] = response
        return state

    def reset(self) -> None:
        self._internal_memory.clear()

    def get_state(self) -> Dict[str, Any]:
        return self._internal_memory

    @property
    def name(self) -> str:
        return self._name
