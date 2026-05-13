import pytest
import os
from pathlib import Path
from unittest.mock import patch
from src.code_weaver.tools.file_tools import read_file

def test_symlink_bypass(tmp_path):
    """
    Test that symbolic links pointing to blocked areas are still blocked.
    Note: Creating symlinks on Windows often requires Administrator privileges.
    We wrap this in a try-except to skip if the OS denies symlink creation.
    """
    # Setup: A blocked directory and a target file
    blocked_dir = tmp_path / "blocked_zone"
    blocked_dir.mkdir()
    secret_file = blocked_dir / "secret.txt"
    secret_file.write_text("top secret content")
    
    # Setup: An allowed directory where we will place the symlink
    allowed_dir = tmp_path / "allowed_zone"
    allowed_dir.mkdir()
    link_path = allowed_dir / "link_to_secret"
    
    try:
        # Create symlink: link_to_secret -> blocked_zone
        # On Windows, this might fail without admin rights
        link_path.symlink_to(blocked_dir)
    except OSError as e:
        pytest.skip(f"OS denied symlink creation (likely missing admin rights): {e}")

    # Config: Block the secret zone
    with patch("src.code_weaver.config.config.paths.blocked_paths", [str(blocked_dir.resolve())]), \
         patch("src.code_weaver.config.config.paths.allowed_paths", []):
        
        # Attempt to read the secret file THROUGH the symlink
        target = str(link_path / "secret.txt")
        result = read_file.invoke({"path": target})
        
        # It should be blocked because .resolve() flattens the symlink
        assert "Security Error" in result
        assert "explicitly blocked" in result

def test_case_sensitivity_bypass(tmp_path):
    """Test that path blocking is case-insensitive on Windows."""
    # Create a directory with a specific case
    secret_dir = tmp_path / "SecretsFolder"
    secret_dir.mkdir()
    secret_file = secret_dir / "data.txt"
    secret_file.write_text("secret data")
    
    # Block using lowercase version
    blocked_path = str(secret_dir).lower()
    
    with patch("src.code_weaver.config.config.paths.blocked_paths", [blocked_path]), \
         patch("src.code_weaver.config.config.paths.allowed_paths", []):
        
        # Try to access using the original case
        result = read_file.invoke({"path": str(secret_file)})
        
        # On Windows, this should be blocked. 
        # If it's not, we need to update _validate_path to use .lower()
        assert "Security Error" in result

def test_prefix_vs_directory_blocking(tmp_path):
    """
    Test that blocking '/secret' doesn't accidentally block '/secret_backup'
    unless the user intended to block the prefix.
    """
    # Setup two directories: one blocked, one similar name but not blocked
    secret_dir = tmp_path / "secret"
    secret_dir.mkdir()
    secret_file = secret_dir / "pass.txt"
    secret_file.write_text("123")
    
    backup_dir = tmp_path / "secret_backup"
    backup_dir.mkdir()
    backup_file = backup_dir / "pass.txt"
    backup_file.write_text("456")
    
    # Block only the 'secret' directory
    with patch("src.code_weaver.config.config.paths.blocked_paths", [str(secret_dir.resolve())]), \
         patch("src.code_weaver.config.config.paths.allowed_paths", []):
        
        # 1. The actual secret should be blocked
        res1 = read_file.invoke({"path": str(secret_file)})
        assert "Security Error" in res1
        
        # 2. The backup should be ALLOWED (it's a different directory)
        res2 = read_file.invoke({"path": str(backup_file)})
        assert "1: 456" in res2

def test_null_byte_injection(tmp_path):
    """Test that null bytes or weird encoding in paths don't bypass the validator."""
    test_file = tmp_path / "normal.txt"
    test_file.write_text("content")
    
    # Attempt to use a null byte to trick the path resolver
    # Note: Python's Path and os.path usually handle this, but we verify.
    dangerous_path = str(test_file) + "\0.txt"
    
    with patch("src.code_weaver.config.config.paths.allowed_paths", []), \
         patch("src.code_weaver.config.config.paths.blocked_paths", []):
        
        result = read_file.invoke({"path": dangerous_path})
        # Should return a standard "does not exist" or "invalid path" error, not a crash
        assert "Error" in result
