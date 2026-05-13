from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

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

from langchain_core.runnables import RunnableConfig

async def agent_node(state: AgentState, config: RunnableConfig) -> dict:
    system_prompt = load_system_prompt()
    
    response = await llm.ainvoke([SystemMessage(content=system_prompt)] + state["messages"], config=config)
    
    return {
        "messages": [response],
    }


def should_continue(state: AgentState) -> str:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END


# ── Graph Construction ───────────────────────────────────────────────────────────

def create_app():
    tool_node = ToolNode(all_tools)
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    workflow.add_edge("tools", "agent")
    return workflow.compile()

app = create_app()
