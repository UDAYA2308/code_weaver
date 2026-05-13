# 🧶 Code Weaver

Code Weaver is an expert AI coding agent built with **LangGraph** and **LangChain**. It is designed to operate directly on a local filesystem to develop, refactor, and debug software autonomously.

## 🚀 Quick Start

### 1. Installation

You can install Code Weaver directly from the repository or a local folder.

**From GitHub:**
```bash
pip install git+https://github.com/your-username/code_weaver.git
```

**From a local folder:**
```bash
pip install /path/to/your/code_weaver_folder
```

### 2. Initialization

Before running the server, you need to initialize the configuration files and database. This creates a hidden directory in your user home folder (`~/.code_weaver`) to store your settings globally.

```bash
code_weaver init
```

**What this does:**
- Creates `~/.code_weaver/config.yaml` (LLM settings)
- Creates `~/.code_weaver/.env` (API keys)
- Creates `~/.code_weaver/system_prompt.md` (Agent persona)
- Initializes the local database for session persistence.

**Next Steps:**
Open the created files in `~/.code_weaver` and provide your `OPENAI_API_KEY` and preferred model.

### 3. Running the Agent

You can now start the Code Weaver server from **any** project directory. The agent will have access to the files in the folder where you run the command.

```bash
# Navigate to your project
cd /path/to/your/project

# Start the server
code_weaver serve
```

**Advanced Options:**
You can specify a custom host or port if the default is occupied:
```bash
code_weaver serve --port 8080 --host 0.0.0.0
```

---

## 🧪 Testing

The project includes a comprehensive test suite to ensure the reliability of the agent's tools and graph logic.

To run the tests (from the source folder):
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
pytest
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
├── pyproject.toml       # Project metadata and dependencies
├── README.md            # Project documentation
├── src/
│   └── code_weaver/
│       ├── cli.py      # Command line interface (init, serve)
│       ├── main.py     # Entry point
│       ├── chat.py     # CLI chat implementation
│       ├── graph.py    # LangGraph state machine definition
│       ├── state.py    # AgentState TypedDict definition
│       ├── config.py   # Pydantic configuration loader
│       ├── utils.py    # System prompt and helper utilities
│       ├── web_ui.py   # Chainlit-based visual interface
│       └── tools/      # Tool implementations
│           ├── __init__.py
│           ├── file_tools.py
│           ├── system_tools.py
│           ├── web_tools.py
│           └── code_tools.py
└── tests/              # Test suite for tools and agent logic
```
