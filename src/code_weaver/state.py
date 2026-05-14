import operator
from typing import TypedDict, Annotated


# ── State ────────────────────────────────────────────────────────────────────


class AgentState(TypedDict):
    task: str
    messages: Annotated[list, operator.add]
    system_prompt: str
    temperature: float
    max_tokens: int