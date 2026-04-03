"""Report generator that synthesizes search results into actionable intelligence."""

from datetime import datetime

from intelligence.models import Company, Report, SearchResult

# Keywords that signal specific categories
CATEGORY_KEYWORDS = {
    "merger_acquisition": ["acquire", "acquisition", "merger", "merge", "buyout", "takeover", "deal"],
    "leadership": ["ceo", "coo", "cfo", "cto", "president", "appoint", "hire", "leadership", "executive", "board"],
    "expansion": ["expand", "expansion", "new office", "new location", "growth", "open", "launch"],
    "partnership": ["partner", "partnership", "joint venture", "collaborate", "alliance", "agreement"],
    "financial": ["revenue", "earnings", "profit", "funding", "investment", "ipo", "valuation", "quarter"],
    "awards": ["award", "recognized", "best places", "top", "honor", "ranked", "named to"],
    "events": ["conference", "summit", "trade show", "expo", "gala", "event", "sponsor", "attend"],
    "community": ["charity", "community", "foundation", "donate", "volunteer", "chamber of commerce"],
    "product": ["product", "launch", "innovation", "technology", "solution", "platform", "service"],
}

# Outreach suggestion templates based on detected categories
OUTREACH_TEMPLATES = {
    "merger_acquisition": (
        "They've recently been involved in M&A activity. This often means new decision-makers, "
        "shifting priorities, and budget reallocation. Reach out to discuss how your services can "
        "support their transition or newly combined operations."
    ),
    "leadership": (
        "There's been a leadership change. New executives often bring fresh perspectives and are "
        "open to evaluating new vendors and partners. This is a prime window to introduce yourself "
        "before they settle into existing relationships."
    ),
    "expansion": (
        "They're expanding into new markets or locations. Growth creates needs — new infrastructure, "
        "services, and partnerships. Position yourself as a resource that can support their expansion."
    ),
    "partnership": (
        "They've announced a new partnership or joint venture. This signals they're open to collaboration. "
        "Consider how your offerings complement their new direction."
    ),
    "financial": (
        "They've reported strong financial results or received funding. Companies in a strong financial "
        "position are more likely to invest in new services and partnerships."
    ),
    "awards": (
        "They've been recognized with an award or industry honor. Congratulate them — it's a natural "
        "conversation starter and shows you're paying attention to their success."
    ),
    "events": (
        "They're active in industry events. Check if you'll be at the same events — it's the best way "
        "to meet in person. If not, reference the event as a shared interest."
    ),
    "community": (
        "They're involved in community or charitable initiatives. If you share similar values, "
        "mention your own community involvement to build rapport."
    ),
    "product": (
        "They've launched a new product or service line. This could create opportunities for "
        "complementary offerings or supply chain partnerships."
    ),
}


def _categorize_result(result: SearchResult) -> list[str]:
    """Determine which categories a search result belongs to."""
    text = f"{result.title} {result.snippet}".lower()
    categories = []
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            categories.append(category)
    return categories


def _mentions_other_companies(result: SearchResult, other_companies: list[Company]) -> list[str]:
    """Check if a search result mentions any other companies from the batch."""
    text = f"{result.title} {result.snippet}".lower()
    mentioned = []
    for company in other_companies:
        # Check for company name (at least 3 chars to avoid false matches)
        if len(company.name) >= 3 and company.name.lower() in text:
            mentioned.append(company.name)
    return mentioned


class ReportGenerator:
    """Generates intelligence reports from search results."""

    def generate(
        self,
        company: Company,
        results: list[SearchResult],
        all_companies: list[Company],
    ) -> Report:
        if not results:
            return Report(
                company_id=company.id,
                overview=f"No recent information found online for {company.name}.",
                recent_news=[],
                relevance_analysis="Unable to assess relevance — no search results available.",
                outreach_suggestions=["Consider a direct introductory outreach based on their industry and location."],
                generated_at=datetime.now(),
            )

        other_companies = [c for c in all_companies if c.id != company.id]

        # Categorize all results
        categorized: dict[str, list[SearchResult]] = {}
        all_categories: set[str] = set()
        for result in results:
            cats = _categorize_result(result)
            for cat in cats:
                categorized.setdefault(cat, []).append(result)
                all_categories.add(cat)

        # Build news items
        recent_news = []
        for result in results:
            cats = _categorize_result(result)
            mentioned = _mentions_other_companies(result, other_companies)
            recent_news.append({
                "title": result.title,
                "summary": result.snippet,
                "url": result.url,
                "date": result.published_date,
                "source": result.source,
                "categories": cats,
                "mentions_companies": mentioned,
            })

        # Generate overview
        overview_parts = [f"{company.name}"]
        if company.address:
            overview_parts[0] += f" ({company.address})"
        overview_parts.append(f"Based on {len(results)} sources found online:")

        activity_summary = []
        if "merger_acquisition" in all_categories:
            activity_summary.append("involved in merger/acquisition activity")
        if "expansion" in all_categories:
            activity_summary.append("expanding operations")
        if "leadership" in all_categories:
            activity_summary.append("undergoing leadership changes")
        if "partnership" in all_categories:
            activity_summary.append("forming new partnerships")
        if "financial" in all_categories:
            activity_summary.append("showing strong financial performance")
        if "events" in all_categories:
            activity_summary.append("active in industry events")
        if "product" in all_categories:
            activity_summary.append("launching new products/services")

        if activity_summary:
            overview_parts.append("The company appears to be " + ", ".join(activity_summary) + ".")
        else:
            overview_parts.append("General business activity detected but no major events identified.")

        # Check cross-references
        all_mentioned = set()
        for result in results:
            all_mentioned.update(_mentions_other_companies(result, other_companies))

        if all_mentioned:
            overview_parts.append(
                f"Notable: Search results also mention these companies from your list: "
                f"{', '.join(all_mentioned)}. See the Connections tab for details."
            )

        overview = " ".join(overview_parts)

        # Relevance analysis
        relevance_parts = []
        if company.is_client:
            relevance_parts.append(
                f"{company.name} is marked as an existing client. "
                "Monitoring their activity helps you stay ahead of their needs and identify upsell opportunities."
            )
        else:
            relevance_parts.append(
                f"{company.name} is a prospect. Here's why they might be worth reaching out to:"
            )

        for cat in all_categories:
            if cat in OUTREACH_TEMPLATES:
                relevance_parts.append(f"- {OUTREACH_TEMPLATES[cat]}")

        if all_mentioned:
            client_mentions = [name for name in all_mentioned
                             if any(c.name == name and c.is_client for c in other_companies)]
            if client_mentions:
                relevance_parts.append(
                    f"- WARM LEAD: This company appears connected to your existing client(s): "
                    f"{', '.join(client_mentions)}. This gives you a potential warm introduction."
                )

        relevance_analysis = "\n".join(relevance_parts)

        # Outreach suggestions
        outreach = []
        for cat in all_categories:
            if cat in OUTREACH_TEMPLATES:
                outreach.append(OUTREACH_TEMPLATES[cat])

        if not outreach:
            outreach.append(
                "No specific trigger events detected, but their general business activity suggests "
                "they're an active company worth a standard introductory outreach."
            )

        return Report(
            company_id=company.id,
            overview=overview,
            recent_news=recent_news,
            relevance_analysis=relevance_analysis,
            outreach_suggestions=outreach,
            generated_at=datetime.now(),
        )
