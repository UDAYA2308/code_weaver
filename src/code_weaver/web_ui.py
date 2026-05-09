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
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("How can I help you with your code today?"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Prepare the state for the graph
        inputs = {
            "messages": [("user", prompt)],
            "task": prompt
        }
        
        # Run the graph
        # Note: We use the compiled app from graph.py
        final_state = app.invoke(inputs)
        
        # The last message in the state is the final response
        if final_state and "messages" in final_state:
            full_response = final_state["messages"][-1].content
        else:
            full_response = "I'm sorry, I couldn't process that request."
            
        message_placeholder.markdown(full_response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
