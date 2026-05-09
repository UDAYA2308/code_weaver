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
            # Convert dict history back to tuple/message format if needed
            # But based on graph.py, it expects a list of messages
            # We'll use the role/content structure
            if isinstance(m, dict):
                # Simple conversion for the graph
                from langchain_core.messages import HumanMessage, AIMessage
                if m["role"] == "user":
                    history.append(HumanMessage(content=m["content"]))
                elif m["role"] == "assistant":
                    history.append(AIMessage(content=m["content"]))
            else:
                history.append(m)
            
        inputs = {
            "messages": history,
            "task": prompt
        }
        
        full_response = ""
        tool_interactions = []
        
        # Use stream_mode="messages" to get token-by-token streaming for AI messages
        # and "values" for state updates. 
        # To get both, we can use stream_mode=["messages", "values"] or just "messages"
        # and track the state.
        
        for msg, metadata in app.stream(inputs, stream_mode="messages"):
            # msg is the message chunk, metadata contains node info
            
            # 1. Handle Token Streaming from the agent
            if metadata.get("langgraph_node") == "agent":
                if msg.content:
                    full_response += msg.content
                    message_placeholder.markdown(full_response + "▌")
                
                # Handle tool calls appearing in the stream
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        if not any(ti['id'] == tool_call['id'] for ti in tool_interactions):
                            tool_interactions.append({
                                "id": tool_call['id'],
                                "tool": tool_call['name'],
                                "args": tool_call['args'],
                                "response": "Executing..."
                            })

            # 2. Handle Tool Responses
            # ToolNode outputs are usually full messages, not chunks
            if metadata.get("langgraph_node") == "tools":
                if msg.type == "tool":
                    tool_call_id = getattr(msg, 'tool_call_id', None)
                    for ti in tool_interactions:
                        if ti['id'] == tool_call_id:
                            ti['response'] = msg.content

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
