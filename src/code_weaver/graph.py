import os
from pathlib import Path
from typing import Annotated
import operator

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage

from .state import AgentState
from .tools import all_tools
from .utils import load_system_prompt

# ── LLM Setup ────────────────────────────────────────────────────────────────────

llm = ChatOpenAI(
    model=os.environ.get("OPENAI_MODEL", "gpt-4o"),
    base_url=os.environ.get("OPENAI_API_BASE_URL", "https://api.openai.com/v1"),
    api_key=os.environ.get("OPENAI_API_KEY"),
    temperature=0,
    streaming=True,
).bind_tools(all_tools)

# ── Graph Nodes ──────────────────────────────────────────────────────────────────

def agent_node(state: AgentState) -> dict:
    system_prompt = load_system_prompt()

    if state.get("scratchpad"):
        system_prompt += f"\n\n## Scratchpad\n{state['scratchpad']}"

    response = llm.invoke(
        [SystemMessage(content=system_prompt)] + state["messages"]
    )
    return {
        "messages": [response],
        "iteration": state.get("iteration", 0) + 1,
        "llm_calls": state.get("llm_calls", 0) + 1
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
