import subprocess
from pathlib import Path
from langchain_core.tools import tool


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


system_tools = [run_command]
