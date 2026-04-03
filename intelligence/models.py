"""Data models for the Company Intelligence System."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Company:
    name: str
    address: str
    is_client: bool
    upload_batch_id: str
    id: int | None = None
    created_at: datetime | None = None


@dataclass
class SearchResult:
    company_id: int
    query: str
    title: str
    snippet: str
    url: str
    source: str
    published_date: str | None = None
    id: int | None = None


@dataclass
class Report:
    company_id: int
    overview: str
    recent_news: list[dict] = field(default_factory=list)
    relevance_analysis: str = ""
    outreach_suggestions: list[str] = field(default_factory=list)
    generated_at: datetime | None = None
    id: int | None = None


@dataclass
class Connection:
    company_a_id: int
    company_b_id: int
    connection_type: str  # merger, shared_event, partnership, same_industry, networking, client_relationship
    description: str
    evidence_urls: list[str] = field(default_factory=list)
    strength: float = 0.0  # 0.0 to 1.0
    id: int | None = None
