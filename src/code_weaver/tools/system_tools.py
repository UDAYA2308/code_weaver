import subprocess
from pathlib import Path

from langchain_core.tools import tool


@tool
def run_command(command: str, cwd: str = ".") -> str:
    """
    Execute a shell command in a subprocess and return its output.
    
    Use this for:
    1. Running tests (e.g., 'pytest', 'npm test').
    2. Installing dependencies (e.g., 'pip install', 'npm install').
    3. Building the project or running scripts.
    4. Any system-level operation not covered by specialized tools.
    
    Args:
        command: The full shell command to execute.
        cwd: The working directory for the command, relative to project root. Defaults to root (".").
        
    Returns:
        The combined STDOUT and STDERR of the command.
    """
    cwd_path = Path(cwd).resolve()
    result = subprocess.run(
        command,
        shell=True,
        cwd=cwd_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )

    output = (result.stdout or "") + (result.stderr or "")
    return output.strip() or "Command completed with no output."


system_tools = [run_command]
