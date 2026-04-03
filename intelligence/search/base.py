"""Abstract base class for search providers."""

from abc import ABC, abstractmethod

from intelligence.models import SearchResult


class SearchProvider(ABC):
    """Interface for web search providers."""

    @abstractmethod
    def search(self, query: str, company_id: int, num_results: int = 10) -> list[SearchResult]:
        """Search the web for a given query and return results."""
        ...
