"""Mock search provider for development and testing."""

import hashlib
import random

from intelligence.models import SearchResult
from intelligence.search.base import SearchProvider

# Realistic mock data templates
MOCK_ARTICLES = [
    {
        "title": "{company} Announces Strategic Partnership with Regional Firm",
        "snippet": "{company} based in {location} has entered into a strategic partnership to expand its services across the region. The deal is expected to increase revenue by 15% over the next fiscal year.",
        "source": "Business Wire",
        "url": "https://example.com/news/{slug}-partnership",
    },
    {
        "title": "{company} Reports Record Q4 Earnings",
        "snippet": "{company} reported earnings that exceeded analyst expectations, driven by strong demand in its core business segments. CEO noted expansion plans for 2025.",
        "source": "Reuters",
        "url": "https://example.com/news/{slug}-earnings",
    },
    {
        "title": "{company} Acquires Local Tech Startup",
        "snippet": "{company} has completed the acquisition of a local technology startup, strengthening its digital capabilities. The acquisition includes 50 employees and proprietary technology.",
        "source": "TechCrunch",
        "url": "https://example.com/news/{slug}-acquisition",
    },
    {
        "title": "{company} CEO Speaks at Industry Leadership Summit",
        "snippet": "The CEO of {company} delivered a keynote address at the Annual Industry Leadership Summit, discussing innovation and market trends affecting businesses in {location}.",
        "source": "Industry Today",
        "url": "https://example.com/news/{slug}-summit",
    },
    {
        "title": "{company} Expands Operations to New Markets",
        "snippet": "{company} announced plans to open new offices in three additional cities, creating over 200 jobs. The expansion reflects growing demand for the company's services.",
        "source": "PR Newswire",
        "url": "https://example.com/news/{slug}-expansion",
    },
    {
        "title": "{company} Named to Best Places to Work List",
        "snippet": "{company} in {location} has been recognized as one of the best places to work in the region, citing its employee benefits, culture, and growth opportunities.",
        "source": "Glassdoor",
        "url": "https://example.com/news/{slug}-workplace",
    },
    {
        "title": "{company} Launches New Product Line",
        "snippet": "{company} unveiled a new product line aimed at mid-market enterprises. The launch follows 18 months of development and early customer trials.",
        "source": "Bloomberg",
        "url": "https://example.com/news/{slug}-product-launch",
    },
    {
        "title": "Leadership Change at {company}",
        "snippet": "{company} has appointed a new Chief Operating Officer as part of its leadership restructuring. The new COO brings 20 years of industry experience from major firms.",
        "source": "Business Journal",
        "url": "https://example.com/news/{slug}-leadership",
    },
    {
        "title": "{company} Joins Regional Chamber of Commerce Initiative",
        "snippet": "{company} has joined a collaborative initiative organized by the {location} Chamber of Commerce focused on workforce development and community investment.",
        "source": "Local Business News",
        "url": "https://example.com/news/{slug}-chamber",
    },
    {
        "title": "{company} Sponsors Annual Charity Gala",
        "snippet": "{company} served as the title sponsor for the annual charity gala benefiting local education programs. The event raised over $500,000 for community initiatives.",
        "source": "Community Press",
        "url": "https://example.com/news/{slug}-charity",
    },
    {
        "title": "{company} Partners with {other_company} on Joint Venture",
        "snippet": "{company} and {other_company} have announced a joint venture to develop integrated solutions for their shared client base. The partnership combines complementary strengths.",
        "source": "Deal Street",
        "url": "https://example.com/news/{slug}-joint-venture",
    },
    {
        "title": "{company} and {other_company} Both Attend National Trade Show",
        "snippet": "Both {company} and {other_company} exhibited at the National Trade Show this week. Industry observers noted both companies are competing for market share in the same segment.",
        "source": "Trade Show Weekly",
        "url": "https://example.com/news/{slug}-tradeshow",
    },
]


class MockSearchProvider(SearchProvider):
    """Returns realistic but fake search results for development."""

    def __init__(self, other_company_names: list[str] | None = None):
        self.other_company_names = other_company_names or []

    def search(self, query: str, company_id: int, num_results: int = 10) -> list[SearchResult]:
        # Use company name from the query for templating
        company_name = query.split('"')[1] if '"' in query else query.split()[0]
        slug = company_name.lower().replace(" ", "-").replace(".", "")
        location = "the region"

        # Deterministic but varied selection based on company name
        seed = int(hashlib.md5(company_name.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)

        # Pick a subset of articles
        selected = rng.sample(MOCK_ARTICLES, min(num_results, len(MOCK_ARTICLES)))

        # Pick a random "other company" for cross-reference articles
        other_companies = [n for n in self.other_company_names if n != company_name]
        other = rng.choice(other_companies) if other_companies else "Acme Corp"

        results = []
        for i, template in enumerate(selected):
            title = template["title"].format(company=company_name, location=location, other_company=other)
            snippet = template["snippet"].format(company=company_name, location=location, other_company=other)
            url = template["url"].format(slug=slug)

            results.append(SearchResult(
                company_id=company_id,
                query=query,
                title=title,
                snippet=snippet,
                url=url,
                source=template["source"],
                published_date=f"2025-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}",
            ))

        return results
