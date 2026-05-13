import os
import subprocess
import tempfile

from langchain_core.tools import tool
from pydantic import BaseModel, Field


class ExecuteCodeInput(BaseModel):
    code: str = Field(description="The Python code to execute")


@tool("execute_python_code", args_schema=ExecuteCodeInput)
def execute_python_code(code: str) -> str:
    """
    Execute a snippet of Python code in an isolated temporary environment.
    
    Use this for:
    1. Complex calculations or data transformations.
    2. Testing a small logic snippet before implementing it in the codebase.
    3. Processing data without creating permanent files.
    
    IMPORTANT: Use this ONLY for Python code. For shell commands, installation of packages, 
    or running existing project tests, use 'run_command'.
    
    Args:
        code (str): The complete, self-contained Python code to execute.
    """
    try:
        # Create a temporary file to run the code
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp:
            tmp.write(code.encode("utf-8"))
            tmp_path = tmp.name

        try:
            # Execute the temporary file
            result = subprocess.run(
                ["python", tmp_path], capture_output=True, text=True, timeout=30
            )

            output = ""
            if result.stdout:
                output += f"STDOUT:\n{result.stdout}"
            if result.stderr:
                output += f"\nSTDERR:\n{result.stderr}"

            if not output:
                return "Code executed successfully with no output."
            return output

        finally:
            # Ensure the temporary file is deleted
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    except subprocess.TimeoutExpired:
        return "Error: Code execution timed out after 30 seconds."
    except Exception as e:
        return f"Error executing code: {str(e)}"


code_tools = [execute_python_code]
