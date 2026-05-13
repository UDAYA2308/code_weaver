import urllib.request

from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool

# Initialize the DuckDuckGo search tool
ddg_search = DuckDuckGoSearchRun()


@tool
def fetch_url(url: str) -> str:
    """
    Fetch the raw content of a URL.

    Use this to read online documentation, API responses, or webpage content to gather
    external information needed for coding tasks.

    Args:
        url: The full URL to fetch (including http/https).
    """
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return r.read().decode()[:5000]
    except Exception as e:
        return f"Error fetching URL: {e}"


@tool
def duckduckgo_search(query: str) -> str:
    """
    Perform a web search using DuckDuckGo to find information, documentation, or external resources.

    Use this when you need to find answers to technical questions, search for library
    documentation, or find examples of how to implement a specific feature.

    Args:
        query: The search query string.
    """
    try:
        return ddg_search.run(query)
    except Exception as e:
        return f"Error performing web search: {e}"


web_tools = [fetch_url, duckduckgo_search]
