import yaml
from pathlib import Path
from pydantic import BaseModel


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

    return AppConfig(**config_dict)


# Singleton instance
config = load_config()
