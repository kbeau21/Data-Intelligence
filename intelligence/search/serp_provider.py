"""SerpAPI search provider for real web searches."""

import requests

from intelligence.models import SearchResult
from intelligence.search.base import SearchProvider


class SerpSearchProvider(SearchProvider):
    """Search provider using SerpAPI (Google Search)."""

    BASE_URL = "https://serpapi.com/search"

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("SERP_API_KEY is required for SerpSearchProvider")
        self.api_key = api_key

    def search(self, query: str, company_id: int, num_results: int = 10) -> list[SearchResult]:
        params = {
            "q": query,
            "api_key": self.api_key,
            "engine": "google",
            "num": num_results,
        }

        try:
            resp = requests.get(self.BASE_URL, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            print(f"SerpAPI search failed for query '{query}': {e}")
            return []

        results = []
        for item in data.get("organic_results", []):
            results.append(SearchResult(
                company_id=company_id,
                query=query,
                title=item.get("title", ""),
                snippet=item.get("snippet", ""),
                url=item.get("link", ""),
                source="Google Search",
                published_date=item.get("date"),
            ))

        # Also grab news results if present
        for item in data.get("news_results", []):
            results.append(SearchResult(
                company_id=company_id,
                query=query,
                title=item.get("title", ""),
                snippet=item.get("snippet", ""),
                url=item.get("link", ""),
                source=item.get("source", "Google News"),
                published_date=item.get("date"),
            ))

        return results[:num_results]
