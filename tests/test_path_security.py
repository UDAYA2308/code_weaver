import pytest
from unittest.mock import patch
from pathlib import Path
from src.code_weaver.tools.file_tools import read_file

def test_path_security_open_mode(tmp_path):
    """Test that when allowed_paths is empty, everything is allowed by default."""
    test_file = tmp_path / "open.txt"
    test_file.write_text("content")
    
    # Config: allowed_paths=[], blocked_paths=[]
    with patch("src.code_weaver.config.config.paths.allowed_paths", []), \
         patch("src.code_weaver.config.config.paths.blocked_paths", []):
        
        result = read_file.invoke({"path": str(test_file)})
        assert "1: content" in result

def test_path_security_restricted_mode_allowed(tmp_path):
    """Test that when allowed_paths is set, only those paths are accessible."""
    test_dir = tmp_path / "allowed_dir"
    test_dir.mkdir()
    test_file = test_dir / "allowed.txt"
    test_file.write_text("content")
    
    # Config: allowed_paths=[allowed_dir], blocked_paths=[]
    with patch("src.code_weaver.config.config.paths.allowed_paths", [str(test_dir.resolve())]), \
         patch("src.code_weaver.config.config.paths.blocked_paths", []):
        
        # Should be allowed
        result = read_file.invoke({"path": str(test_file)})
        assert "1: content" in result

def test_path_security_restricted_mode_denied(tmp_path):
    """Test that when allowed_paths is set, paths outside are blocked."""
    allowed_dir = tmp_path / "allowed_dir"
    allowed_dir.mkdir()
    
    forbidden_dir = tmp_path / "forbidden_dir"
    forbidden_dir.mkdir()
    forbidden_file = forbidden_dir / "secret.txt"
    forbidden_file.write_text("secret")
    
    # Config: allowed_paths=[allowed_dir], blocked_paths=[]
    with patch("src.code_weaver.config.config.paths.allowed_paths", [str(allowed_dir.resolve())]), \
         patch("src.code_weaver.config.config.paths.blocked_paths", []):
        
        result = read_file.invoke({"path": str(forbidden_file)})
        assert "Security Error" in result
        assert "not in the allowed paths list" in result

def test_path_security_block_wins(tmp_path):
    """Test that blocked_paths always override allowed_paths."""
    test_dir = tmp_path / "project"
    test_dir.mkdir()
    secret_dir = test_dir / "secrets"
    secret_dir.mkdir()
    secret_file = secret_dir / "passwords.txt"
    secret_file.write_text("12345")
    
    # Config: allowed_paths=[project], blocked_paths=[secrets]
    with patch("src.code_weaver.config.config.paths.allowed_paths", [str(test_dir.resolve())]), \
         patch("src.code_weaver.config.config.paths.blocked_paths", [str(secret_dir.resolve())]):
        
        result = read_file.invoke({"path": str(secret_file)})
        assert "Security Error" in result
        assert "explicitly blocked" in result

def test_path_security_regex_block(tmp_path):
    """Test that regex patterns in blocked_paths work."""
    test_file = tmp_path / "config.env"
    test_file.write_text("API_KEY=123")
    
    # Block any file ending in .env
    with patch("src.code_weaver.config.config.paths.allowed_paths", []), \
         patch("src.code_weaver.config.config.paths.blocked_paths", [r".*\.env$"]):
        
        result = read_file.invoke({"path": str(test_file)})
        assert "Security Error" in result
        assert "explicitly blocked" in result

def test_path_security_regex_allow(tmp_path):
    """Test that regex patterns in allowed_paths work."""
    test_file = tmp_path / "my_code_v1.py"
    test_file.write_text("print(1)")
    
    # Allow any file ending in .py
    with patch("src.code_weaver.config.config.paths.allowed_paths", [r".*\.py$"]), \
         patch("src.code_weaver.config.config.paths.blocked_paths", []):
        
        result = read_file.invoke({"path": str(test_file)})
        assert "1: print(1)" in result
