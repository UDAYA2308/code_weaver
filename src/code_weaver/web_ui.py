import streamlit as st
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
        # Display tool calls if they exist in the message history
        if "tool_calls" in message and message["tool_calls"]:
            with st.expander("🛠️ Tool Calls"):
                st.json(message["tool_calls"])
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
        inputs = {
            "messages": [("user", prompt)],
            "task": prompt
        }
        
        # Run the graph
        # We use the compiled app from graph.py
        final_state = app.invoke(inputs)
        
        # Extract messages from the final state
        messages = final_state.get("messages", [])
        
        # Find all tool calls made during this turn
        all_tool_calls = []
        for msg in messages:
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                all_tool_calls.extend(msg.tool_calls)
        
        # Display tool calls in a collapsible expander within the assistant message
        if all_tool_calls:
            with tool_calls_container:
                with st.expander("🛠️ Tool Calls", expanded=True):
                    st.json(all_tool_calls)
        
        # The last message in the state is the final response
        if messages:
            full_response = messages[-1].content
        else:
            full_response = "I'm sorry, I couldn't process that request."
            
        message_placeholder.markdown(full_response)
    
    # Add assistant response to chat history, including tool calls for persistence
    st.session_state.messages.append({
        "role": "assistant", 
        "content": full_response, 
        "tool_calls": all_tool_calls
    })
