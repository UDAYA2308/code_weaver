import re
import shutil
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
    """Read the content of a file.
    
    Args:
        path: The absolute path to the file to be read.
        start_line: Optional starting line number (1-indexed) to read from.
        end_line: Optional ending line number (1-indexed) to read until.
        
    Returns:
        The content of the file with line numbers, or an error message if the file 
        cannot be accessed or is blocked by .gitignore.
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
    return "\n".join(f"{i + 1}: {line}" for i, line in enumerate(lines))


@tool
def edit_file(path: str, start_line: int, end_line: int, new_content: str) -> str:
    """Replace a range of lines in a file with new text. 
    
    This is the primary tool for refactoring and modifying existing code. 
    It is more robust than string replacement as it uses line numbers.
    
    Args:
        path: The absolute path to the file to be edited.
        start_line: The first line number to replace (1-indexed).
        end_line: The last line number to replace (1-indexed).
        new_content: The new text to insert in place of the specified lines.
        
    Returns:
        A success message or an error message if the file doesn't exist, 
        is blocked by .gitignore, or line numbers are out of range.
    """
    p = Path(path).resolve()
    if not p.is_file():
        return f"Error: {path} does not exist."
    if _is_ignored(p, _GITIGNORE_PATTERNS):
        return f"Error: Access to {path} is blocked by .gitignore."
    
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    
    if start_line < 1 or end_line > len(lines) or start_line > end_line:
        return f"Error: Line range {start_line}-{end_line} is out of bounds for file with {len(lines)} lines."
    
    # Replace the slice. start_line is 1-indexed.
    # lines[start_line-1 : end_line] replaces from start_line to end_line inclusive.
    lines[start_line - 1 : end_line] = new_content.splitlines()
    
    # Handle trailing newline if the original file had one or if new_content ends with one
    result_text = "\n".join(lines)
    
    p.write_text(result_text, encoding="utf-8")
    return f"Edited lines {start_line} to {end_line} in {path}"


@tool
def write_file(path: str, content: str) -> str:
    """Write content to a file, creating parent directories if they do not exist.
    
    Args:
        path: The absolute path where the file should be written.
        content: The string content to write to the file.
        
    Returns:
        A success message or an error message if writing is blocked by .gitignore.
    """
    p = Path(path).resolve()
    if _is_ignored(p, _GITIGNORE_PATTERNS):
        return f"Error: Writing to {path} is blocked by .gitignore."
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"Written to {path}"


@tool
def delete_path(path: str) -> str:
    """Delete a file or a directory.
    
    Use this to remove obsolete files or clean up temporary directories.
    
    Args:
        path: The absolute path to the file or directory to delete.
        
    Returns:
        A success message or an error message if the path does not exist 
        or is blocked by .gitignore.
    """
    p = Path(path).resolve()
    if not p.is_absolute():
        return f"Error: The path {path} must be an absolute path."
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
    """List the directory structure starting from a given path.
    
    Args:
        path: The absolute path to the directory to list. Defaults to current directory.
        depth: How many levels of subdirectories to traverse. Defaults to 2.
        
    Returns:
        A formatted tree-like string of the directory structure. 
        Entries matching .gitignore are omitted.
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
    """
    Search for a regular expression pattern across files in a directory.
    
    Args:
        path (str): The absolute path to the directory to search in.
        pattern (str): The regex pattern to search for.
        file_glob (str): A glob pattern to filter files (e.g., "*.py"). Defaults to all files.
        
    Returns:
        str: A list of matches in the format 'file:line: content'. 
             Returns 'No matches found' if no occurrences are found.
    """
    root = Path(path).resolve()
    if not root.is_absolute():
        return f"Error: The path {path} must be an absolute path."
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
