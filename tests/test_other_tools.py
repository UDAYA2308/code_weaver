from unittest.mock import patch, MagicMock

from src.code_weaver.tools.code_tools import execute_python_code
from src.code_weaver.tools.system_tools import run_command
from src.code_weaver.tools.web_tools import fetch_url, duckduckgo_search


def test_run_command():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="Success", stderr="", returncode=0)
        result = run_command.invoke({"command": "ls -la"})
        assert result == "Success"
        mock_run.assert_called_once()


def test_fetch_url_success():
    with patch("urllib.request.urlopen") as mock_url:
        mock_response = MagicMock()
        mock_response.read.return_value = b"Mocked content"
        mock_response.__enter__.return_value = mock_response
        mock_url.return_value = mock_response

        result = fetch_url.invoke({"url": "http://example.com"})
        assert "Mocked content" in result


def test_fetch_url_failure():
    with patch("urllib.request.urlopen") as mock_url:
        mock_url.side_effect = Exception("Connection Error")
        result = fetch_url.invoke({"url": "http://example.com"})
        assert "Error fetching URL" in result


def test_duckduckgo_search():
    with patch("src.code_weaver.tools.web_tools.DuckDuckGoSearchRun.run", create=True) as mock_run:
        mock_run.return_value = "Mocked search result"
        result = duckduckgo_search.invoke({"query": "test query"})
        assert "Mocked search result" in result
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="Result: 42", stderr="", returncode=0)
        result = execute_python_code.invoke({"code": "print(21 * 2)"})
        assert "STDOUT:\nResult: 42" in result
        mock_run.assert_called_once()