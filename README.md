# 🧶 Code Weaver

Code Weaver is an expert AI coding agent built with **LangGraph** and **LangChain**. It is designed to operate directly on a local filesystem to develop, refactor, and debug software autonomously.

## 🚀 Quick Start

### 1. Installation
This project uses [uv](https://github.com/astral-sh/uv) for fast, reliable dependency management.

```bash
# Install uv if not already present
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync the project environment
uv sync
```

### 2. Configuration
Code Weaver requires an LLM backend (OpenAI compatible).

- **App Settings**: Configuration is managed in `config.yaml`. To generate a default template:
  ```bash
  uv run python setup_env.py
  ```
  Open `config.yaml` and provide your `api_key` and preferred `model`.
- **Agent Persona**: The agent's core instructions, safety guidelines, and communication style are defined in `system_prompt.md`.

### 3. Running the Agent
You can interact with Code Weaver via two different interfaces:

**Option A: Interactive CLI**
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
uv run python -m src.code_weaver.chat
```

**Option B: Web UI (Chainlit)**
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
uv run chainlit run src/code_weaver/web_ui.py
```

---

## 🧪 Testing
The project includes a comprehensive test suite to ensure the reliability of the agent's tools and graph logic.

To run the tests:
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
uv run pytest
```


## 🛠️ Technical Architecture

### 🧠 The Brain (LangGraph)
The agent is implemented as a state machine in `src/code_weaver/graph.py`.

**The Execution Loop:**
1. **Agent Node**: The LLM receives the `system_prompt`, the current `AgentState`, and the conversation history. It decides whether to provide a final answer or call a tool.
2. **Conditional Edge**: If the LLM generates `tool_calls`, the graph routes to the **Tool Node**. Otherwise, it terminates (`END`).
3. **Tool Node**: Executes the requested tools and appends the results to the message history.
4. **Cycle**: The flow returns to the **Agent Node** to analyze the tool output and decide the next step.

### 📋 State Management
The `AgentState` (defined in `src/code_weaver/state.py`) maintains the context across turns:
- `messages`: A growing list of all interactions (Human, AI, and Tool messages).

### 🧰 Toolset
Code Weaver's capabilities are split into specialized modules in `src/code_weaver/tools/`:

| Category | Tools | Description |
| :--- | :--- | :--- |
| **File** | `read_file`, `write_file`, `edit_file`, `delete_path`, `list_dir`, `search` | Full filesystem access. **Safety**: All tools respect `.gitignore` patterns and enforce absolute paths to prevent ambiguity. |
| **System** | `run_command` | Executes shell commands for testing, building, or installing dependencies. |
| **Web** | `duckduckgo_search`, `fetch_url` | Accesses external documentation and real-time information. |
| **Code** | `execute_python_code` | Runs Python snippets in a temporary isolated file for calculations or logic tests. |
---

## 📂 Project Structure

```text
code_weaver/
├── config.yaml          # LLM settings (model, base_url, temperature)
├── system_prompt.md     # The "Soul" of the agent: guidelines and persona
├── pyproject.toml       # Project metadata and dependencies
├── setup_env.py         # Config initialization utility
├── README.md            # Project documentation
├── src/
│   └── code_weaver/
│       ├── main.py      # Entry point (currently redirects to chat)
│       ├── chat.py      # CLI implementation with multi-line input
│       ├── graph.py     # LangGraph state machine definition
│       ├── state.py     # AgentState TypedDict definition
│       ├── config.py    # Pydantic configuration loader
│       ├── utils.py     # System prompt and helper utilities
│       ├── web_ui.py    # Chainlit-based visual interface
│       └── tools/       # Tool implementations
│           ├── __init__.py
│           ├── file_tools.py
│           ├── system_tools.py
│           ├── web_tools.py
│           └── code_tools.py
└── tests/               # Test suite for tools and agent logic
```