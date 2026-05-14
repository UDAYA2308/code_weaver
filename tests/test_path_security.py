import pytest
import yaml
from pathlib import Path
from unittest.mock import patch
from code_weaver.tools.file_tools import read_file

@pytest.fixture
def mock_config_env(tmp_path):
    """
    Creates a temporary config.yaml and mocks Path.home() 
    to point to the temporary directory.
    """
    config_dir = tmp_path / ".code_weaver"
    config_dir.mkdir()
    config_file = config_dir / "config.yaml"
    
    def _set_config(openai_cfg=None, paths_cfg=None):
        cfg = {
            "openai": openai_cfg or {"api_key": "test", "model": "gpt-4o"},
            "paths": paths_cfg or {"system_prompt": "test.md", "allowed_commands": [], "allowed_paths": [], "blocked_paths": []}
        }
        config_file.write_text(yaml.dump(cfg))

    # Mock Path.home to return the tmp_path
    with patch("pathlib.Path.home", return_value=tmp_path):
        yield _set_config

def test_path_security_open_mode(tmp_path, mock_config_env):
    """Test that when allowed_paths is empty, everything is allowed by default."""
    test_file = tmp_path / "open.txt"
    test_file.write_text("content")

    mock_config_env(paths_cfg={"system_prompt": "test.md", "allowed_commands": [], "allowed_paths": [], "blocked_paths": []})
    
    result = read_file.invoke({"path": str(test_file)})
    assert "1: content" in result

def test_path_security_restricted_mode_allowed(tmp_path, mock_config_env):
    """Test that when allowed_paths is set, only those paths are accessible."""
    test_dir = tmp_path / "allowed_dir"
    test_dir.mkdir()
    test_file = test_dir / "allowed.txt"
    test_file.write_text("content")

    mock_config_env(paths_cfg={
        "system_prompt": "test.md", 
        "allowed_commands": [], 
        "allowed_paths": [str(test_dir.resolve())], 
        "blocked_paths": []
    })
    
    result = read_file.invoke({"path": str(test_file)})
    assert "1: content" in result

def test_path_security_restricted_mode_denied(tmp_path, mock_config_env):
    """Test that when allowed_paths is set, paths outside are blocked."""
    allowed_dir = tmp_path / "allowed_dir"
    allowed_dir.mkdir()

    forbidden_dir = tmp_path / "forbidden_dir"
    forbidden_dir.mkdir()
    forbidden_file = forbidden_dir / "secret.txt"
    forbidden_file.write_text("secret")

    mock_config_env(paths_cfg={
        "system_prompt": "test.md", 
        "allowed_commands": [], 
        "allowed_paths": [str(allowed_dir.resolve())], 
        "blocked_paths": []
    })
    
    result = read_file.invoke({"path": str(forbidden_file)})
    assert "Security Error" in result
    assert "not in the allowed paths list" in result

def test_path_security_block_wins(tmp_path, mock_config_env):
    """Test that blocked_paths always override allowed_paths."""
    test_dir = tmp_path / "project"
    test_dir.mkdir()
    secret_dir = test_dir / "secrets"
    secret_dir.mkdir()
    secret_file = secret_dir / "passwords.txt"
    secret_file.write_text("12345")

    mock_config_env(paths_cfg={
        "system_prompt": "test.md", 
        "allowed_commands": [], 
        "allowed_paths": [str(test_dir.resolve())], 
        "blocked_paths": [str(secret_dir.resolve())]
    })
    
    result = read_file.invoke({"path": str(secret_file)})
    assert "Security Error" in result
    assert "explicitly blocked" in result

def test_path_security_regex_block(tmp_path, mock_config_env):
    """Test that regex patterns in blocked_paths work."""
    test_file = tmp_path / "config.env"
    test_file.write_text("API_KEY=123")

    mock_config_env(paths_cfg={
        "system_prompt": "test.md", 
        "allowed_commands": [], 
        "allowed_paths": [], 
        "blocked_paths": [r".*\.env$"]
    })
    
    result = read_file.invoke({"path": str(test_file)})
    assert "Security Error" in result
    assert "explicitly blocked" in result

def test_path_security_regex_allow(tmp_path, mock_config_env):
    """Test that regex patterns in allowed_paths work."""
    test_file = tmp_path / "my_code_v1.py"
    test_file.write_text("print(1)")

    mock_config_env(paths_cfg={
        "system_prompt": "test.md", 
        "allowed_commands": [], 
        "allowed_paths": [r".*\.py$"], 
        "blocked_paths": []
    })
    
    result = read_file.invoke({"path": str(test_file)})
    assert "1: print(1)" in result
