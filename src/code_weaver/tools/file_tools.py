import os
import subprocess
import shutil
import re
from pathlib import Path
from typing import List
from langchain_core.tools import tool

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
        if path.match(pat) or path.relative_to(path.anchor).match(pat):
            return True
    return False

# Project root is the directory that contains the src folder
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_GITIGNORE_PATTERNS = _load_gitignore(_PROJECT_ROOT)

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

file_tools = [read_file, write_file, edit_file, delete_path, list_dir, search]
