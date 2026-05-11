from unittest.mock import patch, MagicMock

from src.code_weaver.tools.code_tools import execute_python_code
from src.code_weaver.tools.system_tools import run_command
from src.code_weaver.tools.web_tools import fetch_url, google_search


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


def test_google_search():
    with patch("src.code_weaver.tools.web_tools.search") as mock_search:
        mock_search.return_value = ["url1", "url2"]
        result = google_search.invoke({"query": "test query"})
        assert "url1" in result
        assert "url2" in result


def test_execute_python_code():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="Result: 42", stderr="", returncode=0)
        result = execute_python_code.invoke({"code": "print(21 * 2)"})
        assert "STDOUT:\nResult: 42" in result
        mock_run.assert_called_once()
