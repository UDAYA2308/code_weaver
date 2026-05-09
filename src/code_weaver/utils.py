import os
from pathlib import Path

def load_system_prompt(filename="system_prompt.md"):
    """Loads the system prompt from a markdown file in the root directory."""
    # The prompt is in the root directory, not inside src/code_weaver
    # We go up two levels from this file's location to reach the root
    root_dir = Path(__file__).parent.parent.parent
    prompt_path = root_dir / filename
    
    try:
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")
        else:
            return "You are a helpful AI coding assistant."
    except Exception as e:
        print(f"Error loading system prompt: {e}")
        return "You are a helpful AI coding assistant."
