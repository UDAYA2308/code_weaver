import re
import shutil
from pathlib import Path
from typing import List, Optional

from langchain_core.tools import tool
from ..config import config

def _validate_path(path_str: str) -> tuple[Optional[Path], Optional[str]]:
    """
    Strictly validates a path against allowed and blocked lists in config.
    Supports regex and prefix matching.
    
    Returns:
        (resolved_path, error_message)
    """
    try:
        p = Path(path_str).resolve()
    except Exception as e:
        return None, f"Invalid path format: {e}"

    p_str = str(p)
    config_path = Path.home() / ".code_weaver" / "config.yaml"

    # 1. Blocked Paths (Highest Priority - Block always wins)
    for blocked in config.paths.blocked_paths:
        if any(char in blocked for char in r"^$[]()"):
            try:
                if re.search(blocked, p_str):
                    return None, f"Security Error: Access to {path_str} is explicitly blocked by configuration. To change this, edit {config_path}."
            except re.error:
                if p_str.startswith(blocked):
                    return None, f"Security Error: Access to {path_str} is explicitly blocked by configuration. To change this, edit {config_path}."
        else:
            try:
                blocked_p = Path(blocked).resolve()
                if p == blocked_p or p.is_relative_to(blocked_p):
                    return None, f"Security Error: Access to {path_str} is explicitly blocked by configuration. To change this, edit {config_path}."
            except Exception:
                if p_str.startswith(blocked):
                    return None, f"Security Error: Access to {path_str} is explicitly blocked by configuration. To change this, edit {config_path}."

    # 2. Allowed Paths (If list is empty, everything is allowed by default)
    if config.paths.allowed_paths:
        is_allowed = False
        for allowed in config.paths.allowed_paths:
            if any(char in allowed for char in r"^$[]()"):
                try:
                    if re.search(allowed, p_str):
                        is_allowed = True
                        break
                except re.error:
                    if p_str.startswith(allowed):
                        is_allowed = True
                        break
            else:
                try:
                    allowed_p = Path(allowed).resolve()
                    if p == allowed_p or p.is_relative_to(allowed_p):
                        is_allowed = True
                        break
                except Exception:
                    if p_str.startswith(allowed):
                        is_allowed = True
                        break
        
        if not is_allowed:
            return None, f"Security Error: Access to {path_str} is not in the allowed paths list. To grant access, add it to 'allowed_paths' in {config_path}."

    return p, None


@tool
def read_file(path: str, start_line: int = None, end_line: int = None) -> str:
    """Read the content of a file.
    
    Args:
        path: The absolute path to the file to be read.
        start_line: Optional starting line number (1-indexed) to read from.
        end_line: Optional ending line number (1-indexed) to read until.
    """
    p, error = _validate_path(path)
    if error:
        return error

    if not p.is_file():
        return f"Error: {path} does not exist."
    
    try:
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception as e:
        return f"Error reading file: {e}"

    if start_line is not None or end_line is not None:
        start = (start_line or 1) - 1
        end = end_line if end_line is not None else len(lines)
        lines = lines[start:end]
    return "\n".join(f"{i + 1}: {line}" for i, line in enumerate(lines))


@tool
def edit_file(path: str, start_line: int, end_line: int, new_content: str) -> str:
    """Replace a range of lines in a file with new text. 
    
    Args:
        path: The absolute path to the file to be edited.
        start_line: The first line number to replace (1-indexed).
        end_line: The last line number to replace (1-indexed).
        new_content: The new text to insert in place of the specified lines.
    """
    p, error = _validate_path(path)
    if error:
        return error

    if not p.is_file():
        return f"Error: {path} does not exist."
    
    try:
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception as e:
        return f"Error reading file: {e}"
    
    if start_line < 1 or end_line > len(lines) or start_line > end_line:
        return f"Error: Line range {start_line}-{end_line} is out of bounds for file with {len(lines)} lines."
    
    lines[start_line - 1 : end_line] = new_content.splitlines()
    result_text = "\n".join(lines)
    
    try:
        p.write_text(result_text, encoding="utf-8")
    except Exception as e:
        return f"Error writing file: {e}"
        
    return f"Edited lines {start_line} to {end_line} in {path}"


@tool
def write_file(path: str, content: str) -> str:
    """Write content to a file, creating parent directories if they do not exist.
    
    Args:
        path: The absolute path where the file should be written.
        content: The string content to write to the file.
    """
    p, error = _validate_path(path)
    if error:
        return error
    
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    except Exception as e:
        return f"Error writing file: {e}"
        
    return f"Written to {path}"


@tool
def delete_path(path: str) -> str:
    """Delete a file or a directory.
    
    Args:
        path: The absolute path to the file or directory to delete.
    """
    p, error = _validate_path(path)
    if error:
        return error

    if not p.exists():
        return f"Error: {path} does not exist."
    
    try:
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()
    except Exception as e:
        return f"Error deleting path: {e}"
        
    return f"Deleted {path}"


@tool
def list_dir(path: str = ".", depth: int = 2) -> str:
    """List the directory structure starting from a given path.
    
    Args:
        path: The absolute path to the directory to list. Defaults to current directory.
        depth: How many levels of subdirectories to traverse. Defaults to 2.
    """
    base, error = _validate_path(path)
    if error:
        return error
    if not base.is_dir():
        return f"Error: {path} is not a directory."
    
    result = []
    try:
        for p in sorted(base.rglob("*")):
            resolved_p = p.resolve()
            
            is_blocked = False
            for blocked in config.paths.blocked_paths:
                if any(char in blocked for char in r"^$[]()"):
                    if re.search(blocked, str(resolved_p)):
                        is_blocked = True
                        break
                elif str(resolved_p).startswith(str(Path(blocked).resolve())):
                    is_blocked = True
                    break
            if is_blocked:
                continue

            rel = p.relative_to(base)
            if len(rel.parts) > depth:
                continue
            indent = "  " * (len(rel.parts) - 1)
            result.append(f"{indent}{p.name}{'/' if p.is_dir() else ''}")
    except Exception as e:
        return f"Error listing directory: {e}"
        
    return "\n".join(result) or "Empty directory."


@tool
def search(path: str, pattern: str, file_glob: str = "*") -> str:
    """
    Search for a regular expression pattern across files in a directory.
    
    Args:
        path: The absolute path to the directory to search in.
        pattern: The regex pattern to search for.
        file_glob: A glob pattern to filter files (e.g., "*.py"). Defaults to all files.
    """
    root, error = _validate_path(path)
    if error:
        return error
    if not root.is_dir():
        return f"Error: {path} is not a directory."
    
    results = []
    try:
        for p in root.rglob(file_glob):
            resolved_p = p.resolve()
            
            is_blocked = False
            for blocked in config.paths.blocked_paths:
                if any(char in blocked for char in r"^$[]()"):
                    if re.search(blocked, str(resolved_p)):
                        is_blocked = True
                        break
                elif str(resolved_p).startswith(str(Path(blocked).resolve())):
                    is_blocked = True
                    break
            if is_blocked:
                continue

            if not p.is_file():
                continue
            try:
                text = p.read_text(errors="ignore")
            except Exception:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if re.search(pattern, line):
                    results.append(f"{p}:{i}: {line.strip()}")
    except Exception as e:
        return f"Error during search: {e}"
        
    return "\n".join(results) if results else "No matches found."


file_tools = [read_file, write_file, edit_file, delete_path, list_dir, search]
