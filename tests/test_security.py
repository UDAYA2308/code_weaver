import pytest
from unittest.mock import patch, MagicMock
from src.code_weaver.tools.system_tools import run_command

def test_run_command_dangerous_commands():
    """Test that the agent is blocked from running highly destructive commands."""
    dangerous_commands = [
        "rm -rf /",
        "format C:",
        "shutdown /s /t 0",
        "mkfs.ext4 /dev/sda1"
    ]
    
    for cmd in dangerous_commands:
        # We mock subprocess.run to ensure we don't actually execute these
        with patch("subprocess.run") as mock_run:
            result = run_command.invoke({"command": cmd})
            # The tool should return a security error and NOT call subprocess.run
            assert "Security Error" in result or "forbidden" in result.lower()
            mock_run.assert_not_called()

def test_run_command_injection_blocking():
    """Test that shell chaining and piping are blocked to prevent command injection."""
    injection_attempts = [
        "ls ; rm -rf /",
        "echo hello && whoami",
        "cat file.txt | grep secret",
        "ls > output.txt",
        "python -c 'import os; os.system(\"ls\")'"
    ]
    
    for cmd in injection_attempts:
        with patch("subprocess.run") as mock_run:
            result = run_command.invoke({"command": cmd})
            assert "Security Error" in result or "forbidden" in result.lower()
            mock_run.assert_not_called()
