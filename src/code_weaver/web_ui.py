import streamlit as st
import json
from code_weaver.graph import app
from code_weaver.state import AgentState

st.set_page_config(page_title="Code Weaver AI", page_icon="🧶", layout="wide")

st.title("🧶 Code Weaver AI")
st.markdown("An AI coding agent that can read, write, and execute code on your local system.")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # Display tool interactions if they exist in the message history
        if "tool_interactions" in message and message["tool_interactions"]:
            for interaction in message["tool_interactions"]:
                with st.expander(f"🛠️ Tool: {interaction['tool']}"):
                    st.markdown("**Arguments:**")
                    args_display = interaction['args']
                    if isinstance(args_display, dict):
                        args_display = json.dumps(args_display, indent=2)
                    st.code(args_display)
                    st.markdown("**Response:**")
                    st.markdown(interaction['response'])
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("How can I help you with your code today?"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        # Container for tool calls that can be updated in real-time
        tool_calls_container = st.container()
        message_placeholder = st.empty()
        
        # Prepare the state for the graph
        history = []
        for m in st.session_state.messages:
            history.append((m["role"], m["content"]))
            
        inputs = {
            "messages": history,
            "task": prompt
        }
        
        full_response = ""
        tool_interactions = []
        
        # Use app.stream with stream_mode="values" to get the full state after each node
        for event in app.stream(inputs, stream_mode="values"):
            if "messages" in event:
                last_msg = event["messages"][-1]
                
                # Helper to safely get message type and content
                msg_type = getattr(last_msg, 'type', None)
                msg_content = getattr(last_msg, 'content', "")

                # 1. Handle Text Streaming from the agent
                if msg_type == "ai" and msg_content:
                    full_response = msg_content
                    message_placeholder.markdown(full_response + "▌")
                
                # 2. Handle Tool Calls (Requests)
                if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                    for tool_call in last_msg.tool_calls:
                        if not any(ti['id'] == tool_call['id'] for ti in tool_interactions):
                            tool_interactions.append({
                                "id": tool_call['id'],
                                "tool": tool_call['name'],
                                "args": tool_call['args'],
                                "response": "Executing..."
                            })
                
                # 3. Handle Tool Responses
                if msg_type == "tool":
                    tool_call_id = getattr(last_msg, 'tool_call_id', None)
                    for ti in tool_interactions:
                        if ti['id'] == tool_call_id:
                            ti['response'] = msg_content

        # Final cleanup of the placeholder
        message_placeholder.markdown(full_response)
        
        # Display tool interactions in a nice format
        if tool_interactions:
            with tool_calls_container:
                for interaction in tool_interactions:
                    with st.expander(f"🛠️ Tool: {interaction['tool']}", expanded=False):
                        st.markdown("**Arguments:**")
                        args_display = interaction['args']
                        if isinstance(args_display, dict):
                            args_display = json.dumps(args_display, indent=2)
                        st.code(args_display)
                        st.markdown("**Response:**")
                        st.markdown(interaction['response'])
    
    # Add assistant response to chat history
    st.session_state.messages.append({
        "role": "assistant", 
        "content": full_response, 
        "tool_interactions": tool_interactions
    })
