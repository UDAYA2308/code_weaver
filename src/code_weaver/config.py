from pathlib import Path

import yaml
from pydantic import BaseModel


class OpenAIConfig(BaseModel):
    api_key: str
    model: str = "gpt-4o"
    base_url: str = "https://api.openai.com/v1"
    temperature: float = 0.0


class PathConfig(BaseModel):
    system_prompt: str = "system_prompt.md"


class AppConfig(BaseModel):
    openai: OpenAIConfig
    paths: PathConfig

def load_config(config_path: str = "config.yaml") -> AppConfig:
    # Look for config in the global user directory
    global_config_dir = Path.home() / ".code_weaver"
    full_path = global_config_dir / config_path

    if not full_path.exists():
        raise FileNotFoundError(f"Config file not found at {full_path}. Please run 'code_weaver init'.")

    with open(full_path, "r") as f:
        config_dict = yaml.safe_load(f)

    return AppConfig(**config_dict)



# Singleton instance
config = load_config()