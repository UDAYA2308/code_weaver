import re
import subprocess
import os
from pathlib import Path

from langchain_core.tools import tool
from ..config import config

def _is_command_safe(command: str) -> bool:
    """
    Strictly validates if a command is safe based on the config whitelist.
    """
    # 1. Block shell chaining/piping to prevent command injection
    forbidden_chars = r"[;&|><`$\(\)\{\}\[\]]"
    if re.search(forbidden_chars, command):
        return False

    # 2. Extract the base command
    parts = command.split()
    if not parts:
        return False
    
    base_cmd = parts[0].lower()
    if "/" in base_cmd or "\\" in base_cmd:
        base_cmd = Path(base_cmd).name.lower()

    # Use the whitelist from config.yaml
    return base_cmd in config.paths.allowed_commands

@tool
def run_command(command: str, cwd: str = ".") -> str:
    """
    Execute a shell command in a subprocess and return its output.
    
    Args:
        command: The full shell command to execute.
        cwd: The working directory for the command, relative to project root. Defaults to root (".").
        
    Returns:
        The combined STDOUT and STDERR of the command.
    """
    if not _is_command_safe(command):
        return (
            f"Security Error: The command provided is forbidden. "
            f"Allowed commands are: {', '.join(config.paths.allowed_commands)}. "
            f"To allow this command, add it to the 'allowed_commands' list in your config.yaml file "
            f"(usually located at {Path.home() / '.code_weaver' / 'config.yaml'})."
        )

    cwd_path = Path(cwd).resolve()
    
    safe_env = {
        "PATH": os.environ.get("PATH", ""),
        "LANG": "en_US.UTF-8",
        "LC_ALL": "en_US.UTF-8",
    }

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
            env=safe_env
        )
        output = (result.stdout or "") + (result.stderr or "")
        return output.strip() or "Command completed with no output."
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds."
    except Exception as e:
        return f"System Error: {e}"

system_tools = [run_command]
