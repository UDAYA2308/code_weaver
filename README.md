# Code Weaver

An AI Coding Agent built with LangGraph and LangChain.

## Installation

This project is managed by [uv](https://github.com/astral-sh/uv).

1. Install uv if you haven't already:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Sync the environment:
   ```bash
   uv sync
   ```

## Usage

Ensure you have a `.env` file in the root directory with your `OPENAI_API_KEY`.

### Interactive Chat
Run the chat interface using `uv run`:
```bash
uv run python -m code_weaver.chat
```

### Task-based Execution
Create a `task.txt` file in the root directory and run:
```bash
uv run python -m code_weaver.main
```
