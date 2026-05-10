import urllib.request
from langchain_core.tools import tool
from googlesearch import search


@tool
def fetch_url(url: str) -> str:
    """Fetch the first 5 KB of *url*."""
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return r.read().decode()[:5000]
    except Exception as e:
        return f"Error fetching URL: {e}"


@tool
def google_search(query: str, num_results: int = 5) -> str:
    """
    Perform a Google search and return a list of URLs.
    Use this when you need to find information, documentation, or external resources.
    """
    try:
        results = search(query, num_results=num_results)
        return "\n".join(results)
    except Exception as e:
        return f"Error performing Google search: {e}"


web_tools = [fetch_url, google_search]
