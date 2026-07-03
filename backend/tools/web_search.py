from ddgs import DDGS


def search_web(query: str):
    results = []

    try:
        with DDGS() as ddgs:
            search_results = ddgs.text(query, max_results=5)

            for result in search_results:
                results.append({
                    "title": result.get("title", ""),
                    "link": result.get("href", ""),
                    "snippet": result.get("body", "")
                })

    except Exception as e:
        print("Search Error:", e)

    return results