import os
import yaml
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional

class OpenAIConfig(BaseModel):
    api_key: str
    model: str = "gpt-4o"
    base_url: str = "https://api.openai.com/v1"
    temperature: float = 0.0

class PathConfig(BaseModel):
    system_prompt: str = "system_prompt.md"

class AgentConfig(BaseModel):
    max_iterations: int = 10

class AppConfig(BaseModel):
    openai: OpenAIConfig
    paths: PathConfig
    agent: AgentConfig

def load_config(config_path: str = "config.yaml") -> AppConfig:
    root_dir = Path(__file__).parent.parent.parent
    full_path = root_dir / config_path
    
    if not full_path.exists():
        raise FileNotFoundError(f"Config file not found at {full_path}")
    
    with open(full_path, "r") as f:
        config_dict = yaml.safe_load(f)
    
    # Resolve environment variables in the yaml (e.g., ${OPENAI_API_KEY})
    def resolve_env(val):
        if isinstance(val, str) and val.startswith("${") and val.endswith("}"):
            env_var = val[2:-1]
            return os.environ.get(env_var, val)
        return val

    # Simple recursive resolution for the dict
    def resolve_dict(d):
        if isinstance(d, dict):
            return {k: resolve_dict(v) for k, v in d.items()}
        return resolve_env(d)

    resolved_dict = resolve_dict(config_dict)
    return AppConfig(**resolved_dict)

# Singleton instance
config = load_config()
