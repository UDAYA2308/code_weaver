from langchain_core.messages import HumanMessage

# Import the compiled app and state from the graph module
from .graph import app
from .state import AgentState

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
    """Start an interactive chat session with the agent."""
    print("Enter your question (type 'exit' or press Ctrl‑C to quit):")

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

        state["messages"].append(HumanMessage(content=user_input))

        final_chunk = None
        for chunk in app.stream(state, stream_mode="values"):
            final_chunk = chunk
            if chunk["messages"]:
                chunk["messages"][-1].pretty_print()

        if final_chunk:
            assistant_msg = final_chunk["messages"][-1]
            state["messages"].append(assistant_msg)
            state["iteration"] = final_chunk.get("iteration", state["iteration"])
            state["llm_calls"] = final_chunk.get("llm_calls", state["llm_calls"])


if __name__ == "__main__":
    chat()
