import subprocess
from typing import Dict, Any


def lint_code(path: str) -> Dict[str, Any]:
    """
    Lints the specified file or directory using ruff.

    Args:
        path (str): The path to the file or directory to lint.
    """
    try:
        # We use 'ruff check' to find linting errors.
        # --format=text provides human-readable output.
        result = subprocess.run(
            ["ruff", "check", path], capture_output=True, text=True, check=False
        )

        return {
            "success": result.returncode == 0,
            "output": result.stdout if result.stdout else result.stderr,
            "return_code": result.returncode,
        }
    except FileNotFoundError:
        return {
            "success": False,
            "output": "Error: 'ruff' is not installed. Please install it using 'pip install ruff'.",
            "return_code": -1,
        }
    except Exception as e:
        return {
            "success": False,
            "output": f"An unexpected error occurred: {str(e)}",
            "return_code": -1,
        }


def fix_lint_errors(path: str) -> Dict[str, Any]:
    """
    Attempts to automatically fix linting errors using ruff.

    Args:
        path (str): The path to the file or directory to fix.
    """
    try:
        # 'ruff check --fix' automatically fixes safe errors.
        result = subprocess.run(
            ["ruff", "check", "--fix", path],
            capture_output=True,
            text=True,
            check=False,
        )

        return {
            "success": True,  # Even if some errors remain, the fix command itself succeeded
            "output": result.stdout
            if result.stdout
            else "Linting fixes applied where possible.",
            "return_code": result.returncode,
        }
    except FileNotFoundError:
        return {
            "success": False,
            "output": "Error: 'ruff' is not installed. Please install it using 'pip install ruff'.",
            "return_code": -1,
        }
    except Exception as e:
        return {
            "success": False,
            "output": f"An unexpected error occurred: {str(e)}",
            "return_code": -1,
        }
