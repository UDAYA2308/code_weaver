import os
import subprocess
import shutil
from pathlib import Path
from typing import TypedDict, Annotated, List
import operator

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import re
from dotenv import load_dotenv

load_dotenv()

# ── State ────────────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    task: str
    messages: Annotated[list, operator.add]
    scratchpad: str
    working_files: list[str]
    iteration: int
    llm_calls: int  # ← add this

# ── Tools ────────────────────────────────────────────────────────────────────

def _load_gitignore(root: Path) -> List[str]:
    """Load .gitignore patterns from *root* (or its ancestors).
    Returns a list of glob‑style patterns. Empty list if no .gitignore found.
    """
    gitignore_path = root / ".gitignore"
    if not gitignore_path.is_file():
        return []
    patterns = []
    for line in gitignore_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        patterns.append(line)
    return patterns

def _is_ignored(path: Path, patterns: List[str]) -> bool:
    """Return True if *path* matches any of the gitignore *patterns*.
    The matching follows the simple glob rules used by ``Path.match``.
    """
    for pat in patterns:
        # ``Path.match`` matches against the whole path relative to the cwd.
        # Convert pattern to a relative form.
        if path.match(pat) or path.relative_to(path.anchor).match(pat):
            return True
    return False

# Cache the patterns at import time – the project root is the directory that
# contains the ``qpsi_code`` package.
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_GITIGNORE_PATTERNS = _load_gitignore(_PROJECT_ROOT)

# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

@tool
def read_file(path: str, start_line: int = None, end_line: int = None) -> str:
    """Read a file, optionally between *start_line* and *end_line*.
    Files matching .gitignore are rejected.
    """
    p = Path(path).resolve()
    if not p.is_file():
        return f"Error: {path} does not exist."
    if _is_ignored(p, _GITIGNORE_PATTERNS):
        return f"Error: Access to {path} is blocked by .gitignore."
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    if start_line is not None or end_line is not None:
        start = (start_line or 1) - 1
        end = end_line if end_line is not None else len(lines)
        lines = lines[start:end]
    return "\n".join(f"{i+1}: {l}" for i, l in enumerate(lines))

@tool
def edit_file(path: str, old_content: str, new_content: str) -> str:
    """Replace the first occurrence of *old_content* with *new_content*.
    The file must not be ignored.
    """
    p = Path(path).resolve()
    if not p.is_file():
        return f"Error: {path} does not exist."
    if _is_ignored(p, _GITIGNORE_PATTERNS):
        return f"Error: Access to {path} is blocked by .gitignore."
    text = p.read_text(encoding="utf-8", errors="replace")
    if old_content not in text:
        return f"Error: old_content not found in {path}."
    p.write_text(text.replace(old_content, new_content, 1), encoding="utf-8")
    return f"Edited {path}"

@tool
def write_file(path: str, content: str) -> str:
    """Write *content* to *path*, creating parent directories.
    Writing to ignored locations is prevented.
    """
    p = Path(path).resolve()
    if _is_ignored(p, _GITIGNORE_PATTERNS):
        return f"Error: Writing to {path} is blocked by .gitignore."
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"Written to {path}"

@tool
def delete_path(path: str) -> str:
    """Delete a file or directory unless it is ignored.
    """
    p = Path(path).resolve()
    if not p.exists():
        return f"Error: {path} does not exist."
    if _is_ignored(p, _GITIGNORE_PATTERNS):
        return f"Error: Deleting {path} is blocked by .gitignore."
    if p.is_dir():
        shutil.rmtree(p)
    else:
        p.unlink()
    return f"Deleted {path}"

@tool
def list_dir(path: str = ".", depth: int = 2) -> str:
    """List a directory tree up to *depth* levels, skipping ignored entries.
    """
    base = Path(path).resolve()
    if not base.is_dir():
        return f"Error: {path} is not a directory."
    result = []
    for p in sorted(base.rglob("*")):
        rel = p.relative_to(base)
        if len(rel.parts) > depth:
            continue
        if _is_ignored(p, _GITIGNORE_PATTERNS):
            continue
        indent = "  " * (len(rel.parts) - 1)
        result.append(f"{indent}{p.name}{'/' if p.is_dir() else ''}")
    return "\n".join(result) or "Empty directory."

@tool
def search(path: str, pattern: str, file_glob: str = "*") -> str:
    """Search for *pattern* (regex) in files under *path* matching *file_glob*.
    Ignored files are omitted.
    """
    root = Path(path).resolve()
    if not root.is_dir():
        return f"Error: {path} is not a directory."
    results = []
    for p in root.rglob(file_glob):
        if not p.is_file() or _is_ignored(p, _GITIGNORE_PATTERNS):
            continue
        try:
            text = p.read_text(errors="ignore")
        except Exception:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if re.search(pattern, line):
                results.append(f"{p}:{i}: {line.strip()}")
    return "\n".join(results) if results else "No matches found."

@tool
def run_command(command: str, cwd: str = ".") -> str:
    """Execute *command* in a subprocess and return its output.
    The working directory is resolved relative to the project root.
    """
    cwd_path = Path(cwd).resolve()
    result = subprocess.run(
        command,
        shell=True,
        cwd=cwd_path,
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = result.stdout + result.stderr
    return output.strip() or "Command completed with no output."

@tool
def fetch_url(url: str) -> str:
    """Fetch the first 5 KB of *url*.
    """
    import urllib.request
    with urllib.request.urlopen(url, timeout=10) as r:
        return r.read().decode()[:5000]

# ---------------------------------------------------------------------------
# Scratchpad helper tool
# ---------------------------------------------------------------------------
@tool
def update_scratchpad(content: str) -> str:
    """Replace the entire scratchpad with *content*.
    This allows the LLM to store short notes that will be injected into the
    system prompt on the next turn.
    """
    # Import inside the function to avoid circular imports.
    from scratchpad import set as set_scratchpad
    set_scratchpad(content)
    return "Scratchpad updated."

# ── Tools & LLM ───────────────────────────────────────────────────────────────

tools = [read_file, write_file, edit_file, delete_path, list_dir, search, run_command, fetch_url]

llm = ChatOpenAI(
    model=os.environ["OPENAI_MODEL"],
    base_url=os.environ["OPENAI_API_BASE_URL"],
    api_key=os.environ["OPENAI_API_KEY"],
    temperature=0,
    streaming=True,
).bind_tools(tools)

# ── System Prompt ─────────────────────────────────────────────────────────────

def load_system_prompt(path: str = "system.md") -> str:
    p = Path(path)
    return p.read_text() if p.exists() else "You are a helpful coding agent."

# ── Graph Nodes ───────────────────────────────────────────────────────────────

def agent_node(state: AgentState) -> dict:
    system_prompt = load_system_prompt()

    if state.get("scratchpad"):
        system_prompt += f"\n\n## Scratchpad\n{state['scratchpad']}"

    response = llm.invoke(
        [SystemMessage(content=system_prompt)] + state["messages"]
    )
    return {
        "messages": [response],
        "iteration": state.get("iteration", 0) + 1,
        "llm_calls": state.get("llm_calls", 0) + 1  # ← increment
    }

def should_continue(state: AgentState) -> str:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END

# ── Graph ─────────────────────────────────────────────────────────────────────

tool_node = ToolNode(tools)

graph = StateGraph(AgentState)
graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)
graph.set_entry_point("agent")
graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
graph.add_edge("tools", "agent")

app = graph.compile()

# ── Save Graph as PNG ─────────────────────────────────────────────────────────

try:
    png = app.get_graph().draw_mermaid_png()
    with open("graph.png", "wb") as f:
        f.write(png)
    print("Graph saved to graph.png")
except Exception as e:
    print(f"Could not save graph PNG: {e}")

# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    task = open("./task.txt", "r").read()

    print("\n── Agent Output ──")
    final = None
    for chunk in app.stream(
            {
                "task": task,
                "messages": [HumanMessage(content=task)],
                "scratchpad": "",
                "working_files": [],
                "iteration": 0,
                "llm_calls": 0,
            },
            stream_mode="values"
    ):
        final = chunk
        chunk["messages"][-1].pretty_print()

    if final:
        print(f"\n── Stats ──")
        print(f"LLM calls : {final['llm_calls']}")
        print(f"Iterations: {final['iteration']}")