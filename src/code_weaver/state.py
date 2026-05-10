from typing import TypedDict, Annotated
import operator

# ── State ────────────────────────────────────────────────────────────────────


class AgentState(TypedDict):
    task: str
    messages: Annotated[list, operator.add]
    scratchpad: str
    working_files: list[str]
    iteration: int
    llm_calls: int
