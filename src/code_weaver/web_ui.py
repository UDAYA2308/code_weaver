import sqlite3
import json
import chainlit as cl
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer
from langchain_core.messages import HumanMessage, AIMessage
from code_weaver.graph import app
from dotenv import load_dotenv

load_dotenv()

# ── 1. SQLite JSON Adapters ──────────────────────────────────────────────────
sqlite3.register_adapter(list, json.dumps)
sqlite3.register_adapter(dict, json.dumps)

# ── 2. Persistence & Auth ───────────────────────────────────────────────────
# We store the data layer instance globally so we can access it in 'main'
_data_layer = SQLAlchemyDataLayer(conninfo="sqlite+aiosqlite:///chainlit.db")


@cl.data_layer
def get_data_layer():
    return _data_layer


@cl.password_auth_callback
def auth_callback(username: str, password: str):
    if username == "admin" and password == "weaver123":
        return cl.User(identifier="admin", metadata={"role": "admin"})
    return None


# ── 3. Chat Logic ───────────────────────────────────────────────────────────

def get_initial_state():
    return {
        "task": "",
        "messages": [],
        "scratchpad": "",
        "working_files": [],
        "iteration": 0,
        "llm_calls": 0,
    }


@cl.on_chat_start
async def start():
    cl.user_session.set("graph_state", get_initial_state())


@cl.on_chat_resume
async def on_chat_resume(thread):
    messages = []
    for step in thread.get("steps", []):
        if step.get("type") == "user_message":
            messages.append(HumanMessage(content=step.get("output", "")))
        elif step.get("type") in ["assistant_message", "run"]:
            if step.get("output") and not step.get("parentId"):
                messages.append(AIMessage(content=step.get("output", "")))

    meta = thread.get("metadata", {})
    # SQLite returns JSON as string, handle conversion
    if isinstance(meta, str):
        try:
            meta = json.loads(meta)
        except (json.JSONDecodeError, TypeError):
            meta = {}

    cl.user_session.set("graph_state", {
        "task": meta.get("task", ""),
        "messages": messages,
        "scratchpad": meta.get("scratchpad", ""),
        "working_files": meta.get("working_files", []),
        "iteration": meta.get("iteration", 0),
        "llm_calls": meta.get("llm_calls", 0),
    })


@cl.on_message
async def main(message: cl.Message):
    state = cl.user_session.get("graph_state")
    state["messages"].append(HumanMessage(content=message.content))

    status_msg = cl.Message(content="")

    final_state = state
    async for chunk in app.astream(state, stream_mode="values"):
        final_state = chunk
        if chunk.get("messages"):
            last_msg = chunk["messages"][-1]
            if isinstance(last_msg, AIMessage) and last_msg.content:
                status_msg.content = last_msg.content

    await status_msg.send()

    new_state = {
        "task": final_state.get("task", ""),
        "messages": final_state["messages"],
        "scratchpad": final_state.get("scratchpad", ""),
        "working_files": final_state.get("working_files", []),
        "iteration": final_state.get("iteration", state["iteration"]),
        "llm_calls": final_state.get("llm_calls", state["llm_calls"]),
    }

    # ── UPDATED: Access the global data layer instance directly ──
    try:
        await _data_layer.update_thread(
            thread_id=cl.context.session.thread_id,
            metadata={
                "task": new_state["task"],
                "scratchpad": new_state["scratchpad"],
                "working_files": new_state["working_files"],
                "iteration": new_state["iteration"],
                "llm_calls": new_state["llm_calls"]
            }
        )
    except Exception as e:
        print(f"⚠️ Metadata update skipped: {e}")

    cl.user_session.set("graph_state", new_state)