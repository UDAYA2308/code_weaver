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

    with patch("pathlib.Path.home", return_value=tmp_path):
        yield _set_config

def test_symlink_bypass(tmp_path, mock_config_env):
    """
    Test that symbolic links pointing to blocked areas are still blocked.
    """
    blocked_dir = tmp_path / "blocked_zone"
    blocked_dir.mkdir()
    secret_file = blocked_dir / "secret.txt"
    secret_file.write_text("top secret content")

    allowed_dir = tmp_path / "allowed_zone"
    allowed_dir.mkdir()
    link_path = allowed_dir / "link_to_secret"

    try:
        link_path.symlink_to(blocked_dir)
    except OSError as e:
        pytest.skip(f"OS denied symlink creation: {e}")

    mock_config_env(paths_cfg={
        "system_prompt": "test.md", 
        "allowed_commands": [], 
        "allowed_paths": [], 
        "blocked_paths": [str(blocked_dir.resolve())]
    })

    target = str(link_path / "secret.txt")
    result = read_file.invoke({"path": target})
    assert "Security Error" in result
    assert "explicitly blocked" in result

def test_case_sensitivity_bypass(tmp_path, mock_config_env):
    """Test that path blocking is case-insensitive on Windows."""
    secret_dir = tmp_path / "SecretsFolder"
    secret_dir.mkdir()
    secret_file = secret_dir / "data.txt"
    secret_file.write_text("secret data")

    blocked_path = str(secret_dir).lower()

    mock_config_env(paths_cfg={
        "system_prompt": "test.md", 
        "allowed_commands": [], 
        "allowed_paths": [], 
        "blocked_paths": [blocked_path]
    })

    result = read_file.invoke({"path": str(secret_file)})
    import platform
    if platform.system() == "Windows":
        assert "Security Error" in result

def test_prefix_vs_directory_blocking(tmp_path, mock_config_env):
    """
    Test that blocking '/secret' doesn't accidentally block '/secret_backup'
    """
    secret_dir = tmp_path / "secret"
    secret_dir.mkdir()
    secret_file = secret_dir / "pass.txt"
    secret_file.write_text("123")

    backup_dir = tmp_path / "secret_backup"
    backup_dir.mkdir()
    backup_file = backup_dir / "pass.txt"
    backup_file.write_text("456")

    mock_config_env(paths_cfg={
        "system_prompt": "test.md", 
        "allowed_commands": [], 
        "allowed_paths": [], 
        "blocked_paths": [str(secret_dir.resolve())]
    })

    res1 = read_file.invoke({"path": str(secret_file)})
    assert "Security Error" in res1

    res2 = read_file.invoke({"path": str(backup_file)})
    assert "1: 456" in res2

def test_null_byte_injection(tmp_path, mock_config_env):
    """Test that null bytes in paths don't bypass the validator."""
    test_file = tmp_path / "normal.txt"
    test_file.write_text("content")

    dangerous_path = str(test_file) + "\0.txt"

    mock_config_env(paths_cfg={
        "system_prompt": "test.md", 
        "allowed_commands": [], 
        "allowed_paths": [], 
        "blocked_paths": []
    })

    result = read_file.invoke({"path": dangerous_path})
    assert "Error" in result or "Invalid path" in result
