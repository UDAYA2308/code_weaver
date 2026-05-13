import json

import chainlit as cl
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from code_weaver.graph import app

from code_weaver.cli import DB_PATH

load_dotenv()

_data_layer = SQLAlchemyDataLayer(conninfo=f"sqlite+aiosqlite:///{DB_PATH}")


@cl.data_layer
def get_data_layer():
    return _data_layer

@cl.password_auth_callback
def auth_callback(username: str, password: str):
    return cl.User(identifier=username, metadata={"role": "admin"})

def get_initial_state():
    return {
        "task": "",
        "messages": [],
        "message_count": 0,
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

    cl.user_session.set(
        "graph_state",
        {
            "task": meta.get("task", ""),
            "messages": messages,
            "message_count": len(messages),
        },
    )

@cl.on_message
async def main(message: cl.Message):
    state = cl.user_session.get("graph_state") or get_initial_state()
    state["messages"].append(HumanMessage(content=message.content))
    state["message_count"] = state.get("message_count", 0) + 1

    ui_msg = cl.Message(content="")
    
    active_steps = {}
    parent_actions_step = None
    final_state = state
    processed_msg_count = state["message_count"]

    try:
        async for chunk in app.astream(
            state,
            stream_mode=["messages", "values"],
            version="v2",
            config={"configurable": {"thread_id": cl.context.session.thread_id}},
        ):
            if chunk["type"] == "messages":
                msg_chunk, metadata = chunk["data"]
                node_name = metadata.get("langgraph_node")

                if node_name == "agent" and hasattr(msg_chunk, "content") and msg_chunk.content:
                    await ui_msg.stream_token(msg_chunk.content)

                if node_name == "agent" and hasattr(msg_chunk, "tool_calls") and msg_chunk.tool_calls:
                    if parent_actions_step is None:
                        parent_actions_step = cl.Step(name="⚙️ Actions Taken")
                        await parent_actions_step.send()

                    for tc in msg_chunk.tool_calls:
                        tid = tc.get("id")
                        if tid and tid not in active_steps:
                            step = cl.Step(
                                name=f"🛠️ Tool: {tc['name']}", 
                                parent_id=parent_actions_step.id,
                                type="tool"
                            )
                            step.input = tc.get("args")
                            await step.send()
                            active_steps[tid] = step

            elif chunk["type"] == "values":
                final_state = chunk["data"]
                all_msgs = final_state.get("messages", [])
                
                for m in all_msgs[processed_msg_count:]:
                    if isinstance(m, AIMessage) and m.tool_calls:
                        for tc in m.tool_calls:
                            tid = tc.get("id")
                            if tid in active_steps:
                                # Only update if input has changed or wasn't set
                                if active_steps[tid].input != tc.get("args"):
                                    active_steps[tid].input = tc.get("args")
                                    await active_steps[tid].update()
                    
                    if isinstance(m, ToolMessage):
                        tid = m.tool_call_id
                        if tid in active_steps:
                            step = active_steps[tid]
                            if not step.output:
                                step.output = m.content
                                step.language = "json" if isinstance(m.content, (dict, list)) else "markdown"
                                await step.update()
                
                processed_msg_count = len(all_msgs)
                final_state["message_count"] = processed_msg_count

    except Exception as e:
        await cl.Message(content=f"❌ An error occurred: {str(e)}").send()
    finally:
        await ui_msg.send()
        cl.user_session.set("graph_state", final_state)