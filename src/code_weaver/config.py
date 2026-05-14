from pathlib import Path
import os
import yaml
from pydantic import BaseModel

class OpenAIConfig(BaseModel):
    api_key: str
    model: str = "gpt-4o"
    base_url: str = "https://api.openai.com/v1"
    temperature: float = 0.0

class PathConfig(BaseModel):
    system_prompt: str = "system_prompt.md"
    allowed_commands: list[str] = [
        "pytest", "pip", "uv", "git", "ls", "dir", "mkdir", "echo",
        "python", "node", "npm", "yarn", "pnpm", "pwd", "whoami",
        "date", "go", "cargo", "rustc", "make", "cmake", "gcc",
        "clang", "ruff", "flake8", "black", "eslint", "prettier",
        "chainlit"
    ]
    allowed_paths: list[str] = []
    blocked_paths: list[str] = []

class AppConfig(BaseModel):
    openai: OpenAIConfig
    paths: PathConfig

def load_config() -> AppConfig:
    config_path = Path.home() / ".code_weaver" / "config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found at {config_path}")

    with open(config_path, "r") as f:
        return AppConfig(**yaml.safe_load(f))

class ConfigProxy:
    """
    The simplest possible proxy: every attribute access triggers a fresh
    read of the config file from disk.
    """
    def __getattr__(self, name):
        return getattr(load_config(), name)

    def __setattr__(self, name, value):
        super().__setattr__(name, value)

config = ConfigProxy()
