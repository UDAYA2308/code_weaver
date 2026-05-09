import streamlit as st
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage
from code_weaver.graph import app
import json

st.set_page_config(page_title="Code Weaver AI", page_icon="🧶", layout="wide")

st.title("🧶 Code Weaver AI")
st.markdown("An AI coding agent that can read, write, and execute code on your local system.")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

def render_group(messages):
    """Helper to render a group of messages (User or Assistant/Tool)"""
    if not messages:
        return

    # Map tool_call_id -> output for grouped rendering
    tool_outputs = {msg.tool_call_id: msg.content for msg in messages if isinstance(msg, ToolMessage)}

    if isinstance(messages[0], HumanMessage):
        with st.chat_message("user"):
            combined_text = "\n\n".join([m.content for m in messages if hasattr(m, 'content')])
            st.markdown(combined_text)
    else:
        with st.chat_message("assistant"):
            for msg in messages:
                if isinstance(msg, AIMessage):
                    if msg.content:
                        st.markdown(msg.content)
                    if msg.tool_calls:
                        for tool_call in msg.tool_calls:
                            with st.expander(f"🛠️ Tool: {tool_call['name']}"):
                                st.markdown(f"**Arguments:**\n```json\n{json.dumps(tool_call['args'], indent=2)}\n```")
                                output = tool_outputs.get(tool_call['id'])
                                if output:
                                    st.markdown(f"**Response:**\n```\n{output}\n```")
                                else:
                                    st.markdown("**Response:**\n*⏳ Executing...*")

def render_all_history(messages):
    """Groups and renders the entire message history."""
    if not messages:
        return

    grouped = []
    current_group = [messages[0]]
    for msg in messages[1:]:
        is_user = isinstance(msg, HumanMessage)
        prev_is_user = isinstance(current_group[0], HumanMessage)
        if is_user == prev_is_user:
            current_group.append(msg)
        else:
            grouped.append(current_group)
            current_group = [msg]
    grouped.append(current_group)

    for group in grouped:
        render_group(group)

# 1. Render existing history
render_all_history(st.session_state.messages)

# 2. Chat input
if prompt := st.chat_input("How can I help you today?"):
    user_msg = HumanMessage(content=prompt)
    st.session_state.messages.append(user_msg)

    # Render the user message immediately
    render_group([user_msg])

    # Create a container for the agent's multi-turn response
    with st.chat_message("assistant"):
        status_placeholder = st.empty()
        response_placeholder = st.empty()

        status_placeholder.markdown("Thinking and executing... ⏳")

        inputs = {"messages": st.session_state.messages}

        # Use stream_mode="values" to get state updates after every node
        for chunk in app.stream(inputs, stream_mode="values"):
            # Update session state
            st.session_state.messages = chunk.get("messages", [])

            # To avoid re-rendering the whole history, we only render the
            # messages that belong to the current turn (everything after the last user message)
            # Find the index of the last HumanMessage
            last_user_idx = -1
            for i in range(len(st.session_state.messages)-1, -1, -1):
                if isinstance(st.session_state.messages[i], HumanMessage):
                    last_user_idx = i
                    break

            current_turn_messages = st.session_state.messages[last_user_idx + 1:]

            # Update the response placeholder with the current turn's content
            with response_placeholder.container():
                # We use the same grouping logic for the current turn
                if current_turn_messages:
                    # Since we are already inside a 'with st.chat_message("assistant")' block,
                    # we just render the content of the AIMessages and Tool expanders
                    # without creating another chat_message bubble.
                    tool_outputs = {msg.tool_call_id: msg.content for msg in current_turn_messages if isinstance(msg, ToolMessage)}
                    for msg in current_turn_messages:
                        if isinstance(msg, AIMessage):
                            if msg.content:
                                st.markdown(msg.content)
                            if msg.tool_calls:
                                for tool_call in msg.tool_calls:
                                    with st.expander(f"🛠️ Tool: {tool_call['name']}"):
                                        st.markdown(f"**Arguments:**\n```json\n{json.dumps(tool_call['args'], indent=2)}\n```")
                                        output = tool_outputs.get(tool_call['id'])
                                        if output:
                                            st.markdown(f"**Response:**\n```\n{output}\n```")
                                        else:
                                            st.markdown("**Response:**\n*⏳ Executing...*")

        status_placeholder.empty()

    # Final rerun to ensure the state is perfectly synced for the next turn
    st.rerun()