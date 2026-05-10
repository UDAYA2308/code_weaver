from pathlib import Path


def load_system_prompt():
    """Loads the system prompt from a markdown file defined in config."""
    from .config import config

    root_dir = Path(__file__).parent.parent.parent
    prompt_path = root_dir / config.paths.system_prompt

    try:
        if prompt_path.exists():
            return prompt_path.read_text(encoding="utf-8")
        else:
            return "You are a helpful AI coding assistant."
    except Exception as e:
        print(f"Error loading system prompt: {e}")
        return "You are a helpful AI coding assistant."
