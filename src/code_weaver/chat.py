import os
from pathlib import Path
from typing import TypedDict, Annotated
import operator

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Re‑use the tools defined in the main module
from main import (
    read_file,
    write_file,
    edit_file,
    delete_path,
    list_dir,
    search,
    run_command,
    fetch_url,
    load_system_prompt,
    AgentState,
    app,
)

# ---------------------------------------------------------------------------
# Chat loop
# ---------------------------------------------------------------------------

def multiline_input(prompt: str = "You (press Enter twice to send): ") -> str:
    """Collect multiple lines of input until the user enters a blank line."""
    print(prompt)
    lines = []
    while True:
        try:
            line = input()
        except (EOFError, KeyboardInterrupt):
            raise KeyboardInterrupt
        if line == "":
            break
        lines.append(line)
    return "\n".join(lines)

def chat() -> None:
    """Start an interactive chat session with the agent.

    The function keeps the full message history (both user and assistant
    messages) in the ``messages`` field of the state.  Each new user input is
    appended to this list and the graph is invoked again, allowing the LLM to
    reason about the entire conversation.
    """
    print("Enter your question (type 'exit' or press Ctrl‑C to quit):")
    # Initialise an empty state – the ``task`` field is not used for chat.
    state: AgentState = {
        "task": "",
        "messages": [],
        "scratchpad": "",
        "working_files": [],
        "iteration": 0,
        "llm_calls": 0,
    }

    while True:
        try:
            user_input = multiline_input()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if user_input.strip().lower() in {"exit", "quit"}:
            print("Goodbye!")
            break
        # Append the new human message to the history
        state["messages"].append(HumanMessage(content=user_input))
        # Run the graph – we stream values so that tool calls are processed.
        final_chunk = None
        for chunk in app.stream(state, stream_mode="values"):
            final_chunk = chunk
            # The latest assistant message is the last element in ``messages``
            # after each chunk.
            if chunk["messages"]:
                chunk["messages"][-1].pretty_print()
        # Update counters and store assistant response for next turn
        if final_chunk:
            # Append the assistant's response to the message history
            assistant_msg = final_chunk["messages"][-1]
            state["messages"].append(assistant_msg)
            # Update iteration and llm_calls counters from the final chunk.
            state["iteration"] = final_chunk.get("iteration", state["iteration"])
            state["llm_calls"] = final_chunk.get("llm_calls", state["llm_calls"])
        # Message history is retained in state for subsequent turns

if __name__ == "__main__":
    chat()