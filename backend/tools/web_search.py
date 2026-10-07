from ddgs import DDGS

try:
    from ..errors import SearchError
except ImportError:
    from errors import SearchError


def search_web(query: str) -> list[dict[str, str]]:
    try:
        with DDGS(timeout=15) as ddgs:
            search_results = ddgs.text(query, max_results=5)
    except Exception as exc:
        raise SearchError("Web search is temporarily unavailable.") from exc

    results = [
        {
            "title": result.get("title", ""),
            "link": result.get("href", ""),
            "snippet": result.get("body", ""),
        }
        for result in search_results
    ]
    if not results:
        raise SearchError("Web search returned no results for this task.")
    return results
