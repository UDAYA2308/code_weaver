from unittest.mock import patch
from code_weaver.tools.web_tools import fetch_url, duckduckgo_search
from code_weaver.tools.file_tools import read_file


def test_fetch_url_timeout():
    """Test how fetch_url handles a network timeout."""
    with patch("urllib.request.urlopen") as mock_url:
        mock_url.side_effect = TimeoutError("Request timed out")
        result = fetch_url.invoke({"url": "http://example.com"})
        assert "Error fetching URL" in result
        assert "timed out" in result.lower()


def test_fetch_url_404():
    """Test how fetch_url handles a 404 Not Found error."""
    with patch("urllib.request.urlopen") as mock_url:
        from urllib.error import HTTPError

        # Mocking an HTTPError
        mock_url.side_effect = HTTPError(
            "http://example.com", 404, "Not Found", {}, None
        )
        result = fetch_url.invoke({"url": "http://example.com"})
        assert "Error fetching URL" in result
        assert "404" in result


def test_duckduckgo_search_api_failure():
    """Test how duckduckgo_search handles an API failure."""
    with patch(
        "code_weaver.tools.web_tools.DuckDuckGoSearchRun.run", create=True
    ) as mock_run:
        mock_run.side_effect = Exception("API Key Expired")
        result = duckduckgo_search.invoke({"query": "test query"})
        assert "Error performing web search" in result
        assert "API Key Expired" in result
        result = duckduckgo_search.invoke({"query": "test query"})
        assert "Error performing web search" in result
        assert "API Key Expired" in result


def test_read_file_encoding_error():
    """Test read_file with a file that has invalid encoding."""
    import os
    import tempfile

    # Create a temporary file with invalid utf-8 bytes
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"Hello \xff World")  # \xff is invalid utf-8
        tmp_path = tmp.name

    try:
        # The tool uses errors="replace", so it should not crash
        result = read_file.invoke({"path": tmp_path})
        assert "Hello" in result
        assert "World" in result
    finally:
        os.remove(tmp_path)


def test_read_file_non_existent():
    """Test read_file with a path that does not exist."""
    result = read_file.invoke(
        {"path": "C:\\this_file_definitely_does_not_exist_12345.txt"}
    )
    assert "Error" in result
    assert "does not exist" in result
