from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage

from .config import config
from .state import AgentState
from .tools import all_tools
from .utils import load_system_prompt

# ── LLM Setup ────────────────────────────────────────────────────────────────────

llm = ChatOpenAI(
    model=config.openai.model,
    base_url=config.openai.base_url,
    api_key=config.openai.api_key,
    temperature=config.openai.temperature,
    streaming=True,
).bind_tools(all_tools)

# ── Graph Nodes ──────────────────────────────────────────────────────────────────


def agent_node(state: AgentState) -> dict:
    system_prompt = load_system_prompt()

    if state.get("scratchpad"):
        system_prompt += f"\n\n## Scratchpad\n{state['scratchpad']}"

    response = llm.invoke([SystemMessage(content=system_prompt)] + state["messages"])
    return {
        "messages": [response],
        "iteration": state.get("iteration", 0) + 1,
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


def should_continue(state: AgentState) -> str:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END


# ── Graph Construction ───────────────────────────────────────────────────────────

tool_node = ToolNode(all_tools)

graph = StateGraph(AgentState)
graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)
graph.set_entry_point("agent")
graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
graph.add_edge("tools", "agent")

app = graph.compile()
