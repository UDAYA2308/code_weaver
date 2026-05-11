import json
import sqlite3

import chainlit as cl
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from code_weaver.graph import app

load_dotenv()

# ── 1. Persistence Setup ────────────────────────────────────────────────────
sqlite3.register_adapter(list, json.dumps)
sqlite3.register_adapter(dict, json.dumps)

_data_layer = SQLAlchemyDataLayer(conninfo="sqlite+aiosqlite:///chainlit.db")


@cl.data_layer
def get_data_layer():
    return _data_layer


@cl.password_auth_callback
def auth_callback(username: str, password: str):
    if username == "admin" and password == "weaver123":
        return cl.User(identifier="admin", metadata={"role": "admin"})
    return None


# ── 2. Helpers ──────────────────────────────────────────────────────────────


def get_initial_state():
    return {
        "task": "",
        "messages": [],
        "scratchpad": "",
        "working_files": [],
        "iteration": 0,
        "llm_calls": 0,
    }


# ── 3. Chat Logic ───────────────────────────────────────────────────────────


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

    cl.user_session.set(
        "graph_state",
        {
            "task": meta.get("task", ""),
            "messages": messages,
            "scratchpad": meta.get("scratchpad", ""),
            "working_files": meta.get("working_files", []),
            "iteration": meta.get("iteration", 0),
            "llm_calls": meta.get("llm_calls", 0),
        },
    )


import json
import chainlit as cl


@cl.on_message
async def main(message: cl.Message):
    state = cl.user_session.get("graph_state") or get_initial_state()
    state["messages"].append(HumanMessage(content=message.content))

    active_steps = {}
    current_text_msg = None
    final_state = state

    async for chunk in app.astream(
            state,
            stream_mode=["messages", "values"],
            version="v2",
            config={"configurable": {"thread_id": cl.context.session.thread_id}},
    ):
        stream_type = chunk.get("type")
        data = chunk.get("data")

        if stream_type == "messages":
            msg_chunk, metadata = data
            if metadata.get("langgraph_node") == "agent":
                # 1. Handle Tool Intent
                if hasattr(msg_chunk, "tool_calls") and msg_chunk.tool_calls:
                    if current_text_msg:
                        await current_text_msg.send()
                        current_text_msg = None

                    for tc in msg_chunk.tool_calls:
                        tc_id = tc.get("id")
                        if tc_id and tc_id not in active_steps:
                            # Create Step (Sibling)
                            step = cl.Step(
                                name=f"🛠️ {tc['name']}",
                                type="tool",
                                parent_id=None,
                                show_input="json",
                                default_open=False,
                            )
                            await step.send()
                            active_steps[tc_id] = step

                # 2. Handle Content
                elif hasattr(msg_chunk, "content") and msg_chunk.content:
                    if any(tag in msg_chunk.content for tag in ["<|", "|>", "thought"]):
                        continue

                    if current_text_msg is None:
                        current_text_msg = cl.Message(content="")

                    await current_text_msg.stream_token(msg_chunk.content)

        elif stream_type == "values":
            # 3. Sync Arguments and Responses from the Source of Truth
            all_msgs = data.get("messages", [])

            # Map tool call data
            for m in reversed(all_msgs):
                if isinstance(m, AIMessage) and m.tool_calls:
                    for tc in m.tool_calls:
                        tid = tc.get("id")
                        if tid in active_steps:
                            # Finalize the arguments
                            active_steps[tid].input = tc.get("args", {})
                            await active_steps[tid].update()
                    break

            # Map tool result data
            tool_responses = {
                m.tool_call_id: m.content
                for m in all_msgs
                if isinstance(m, ToolMessage)
            }
            for tid, step in active_steps.items():
                if tid in tool_responses and not step.output:
                    step.output = tool_responses[tid]
                    step.language = "markdown"
                    await step.update()

            final_state = data

    if current_text_msg:
        await current_text_msg.send()

    cl.user_session.set("graph_state", final_state)
