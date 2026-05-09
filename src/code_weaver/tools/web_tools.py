import urllib.request
from langchain_core.tools import tool

@tool
def fetch_url(url: str) -> str:
    """Fetch the first 5 KB of *url*.
    """
    with urllib.request.urlopen(url, timeout=10) as r:
        return r.read().decode()[:5000]

web_tools = [fetch_url]
