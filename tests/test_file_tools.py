import pytest
from unittest.mock import patch
from src.code_weaver.tools.file_tools import (
    read_file,
    write_file,
    edit_file,
    list_dir,
    search,
)

@pytest.fixture
def test_dir(tmp_path):
    """Creates a temporary directory with some files for testing."""
    d = tmp_path / "test_project"
    d.mkdir()
    f1 = d / "hello.txt"
    f1.write_text("Hello World\nLine 2\nLine 3", encoding="utf-8")
    sub = d / "subdir"
    sub.mkdir()
    f2 = sub / "test.py"
    f2.write_text("print('test')", encoding="utf-8")
    f3 = d / "ignored.txt"
    f3.write_text("I should be ignored", encoding="utf-8")
    return d

def test_write_file(test_dir):
    path = str(test_dir / "new_file.txt")
    result = write_file.invoke({"path": path, "content": "New Content"})
    assert "Written to" in result
    assert (test_dir / "new_file.txt").read_text() == "New Content"

def test_read_file(test_dir):
    path = str(test_dir / "hello.txt")
    result = read_file.invoke({"path": path})
    assert "1: Hello World" in result
    assert "3: Line 3" in result
    result_range = read_file.invoke({"path": path, "start_line": 2, "end_line": 2})
    assert "1: Line 2" in result_range
    assert "Hello World" not in result_range

def test_edit_file(test_dir):
    path = str(test_dir / "hello.txt")
    result = edit_file.invoke(
        {"path": path, "start_line": 1, "end_line": 1, "new_content": "Hello Universe"}
    )
    assert "Edited" in result
    assert "Hello Universe" in (test_dir / "hello.txt").read_text()
    result_multi = edit_file.invoke(
        {"path": path, "start_line": 2, "end_line": 3, "new_content": "Line 2 Updated\nLine 3 Updated"}
    )
    assert "Edited" in result_multi
    content = (test_dir / "hello.txt").read_text()
    assert "Line 2 Updated" in content
    assert "Line 3 Updated" in content

def test_list_dir(test_dir):
    # Use absolute paths for blocked_paths to ensure match
    blocked = [str((test_dir / "ignored.txt").resolve())]
    with patch("src.code_weaver.config.config.paths.blocked_paths", blocked):
        result = list_dir.invoke({"path": str(test_dir), "depth": 2})
        assert "hello.txt" in result
        assert "subdir/" in result
        assert "test.py" in result
        assert "ignored.txt" not in result

def test_search(test_dir):
    # Use absolute paths for blocked_paths to ensure match
    blocked = [str((test_dir / "ignored.txt").resolve())]
    with patch("src.code_weaver.config.config.paths.blocked_paths", blocked):
        result = search.invoke({"path": str(test_dir), "pattern": "World"})
        assert "hello.txt" in result
        assert "Hello World" in result
        
        # Test blocked file search
        result_ignored = search.invoke({"path": str(test_dir), "pattern": "ignored"})
        assert "No matches found" in result_ignored
