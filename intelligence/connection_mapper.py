"""Connection mapper that detects relationships between companies."""

import re
from itertools import combinations

from intelligence.models import Company, Connection, SearchResult

# Relationship signal phrases (pattern, connection_type, base_strength)
RELATIONSHIP_SIGNALS = [
    (r"acquir(?:ed?|ing|es)", "merger", 0.9),
    (r"merg(?:ed?|ing|er)", "merger", 0.9),
    (r"buyout|takeover|bought", "merger", 0.85),
    (r"partner(?:ed|ing|ship)", "partnership", 0.8),
    (r"joint venture", "partnership", 0.85),
    (r"collaborat(?:ed?|ing|ion)", "partnership", 0.7),
    (r"alliance|agreement", "partnership", 0.7),
    (r"client|customer|serves|engaged", "client_relationship", 0.75),
    (r"sponsor(?:ed|ing|ship)?", "shared_event", 0.6),
    (r"conference|summit|trade show|expo|event|gala", "shared_event", 0.5),
    (r"chamber of commerce|association|industry group", "networking", 0.6),
    (r"board member|advisory|board of directors", "networking", 0.7),
    (r"same industry|competitor|competing", "same_industry", 0.4),
]


def _company_mentioned_in(company_name: str, text: str) -> bool:
    """Check if a company name appears in text (case-insensitive, word-boundary aware)."""
    if len(company_name) < 3:
        return False
    pattern = re.escape(company_name)
    return bool(re.search(pattern, text, re.IGNORECASE))


def _find_relationship_signals(text: str) -> list[tuple[str, float]]:
    """Find relationship signal phrases in text. Returns (connection_type, strength) pairs."""
    text_lower = text.lower()
    found = []
    for pattern, conn_type, strength in RELATIONSHIP_SIGNALS:
        if re.search(pattern, text_lower):
            found.append((conn_type, strength))
    return found


class ConnectionMapper:
    """Detects connections between companies based on search results."""

    def find_connections(
        self,
        companies: list[Company],
        results_by_company: dict[int, list[SearchResult]],
    ) -> list[Connection]:
        """Analyze all company pairs for connections."""
        connections = []
        company_map = {c.id: c for c in companies}

        for comp_a, comp_b in combinations(companies, 2):
            pair_connections = self._analyze_pair(
                comp_a, comp_b,
                results_by_company.get(comp_a.id, []),
                results_by_company.get(comp_b.id, []),
            )
            connections.extend(pair_connections)

        # Deduplicate and keep strongest
        return self._deduplicate(connections)

    def _analyze_pair(
        self,
        comp_a: Company,
        comp_b: Company,
        results_a: list[SearchResult],
        results_b: list[SearchResult],
    ) -> list[Connection]:
        connections = []

        # Strategy 1: Company A mentioned in Company B's search results (and vice versa)
        connections.extend(self._check_cross_mentions(comp_a, comp_b, results_a, results_b))

        # Strategy 2: Shared URLs between search results
        connections.extend(self._check_shared_urls(comp_a, comp_b, results_a, results_b))

        # Strategy 3: Both mentioned in same article with relationship keywords
        connections.extend(self._check_co_occurrence_with_signals(comp_a, comp_b, results_a, results_b))

        return connections

    def _check_cross_mentions(
        self,
        comp_a: Company,
        comp_b: Company,
        results_a: list[SearchResult],
        results_b: list[SearchResult],
    ) -> list[Connection]:
        connections = []

        # Check if B is mentioned in A's results
        for result in results_a:
            text = f"{result.title} {result.snippet}"
            if _company_mentioned_in(comp_b.name, text):
                signals = _find_relationship_signals(text)
                if signals:
                    for conn_type, strength in signals:
                        connections.append(Connection(
                            company_a_id=comp_a.id,
                            company_b_id=comp_b.id,
                            connection_type=conn_type,
                            description=(
                                f"{comp_b.name} is mentioned in an article about {comp_a.name}: "
                                f'"{result.title}". {result.snippet[:200]}'
                            ),
                            evidence_urls=[result.url],
                            strength=strength,
                        ))
                else:
                    # Mentioned but no specific relationship signal
                    connections.append(Connection(
                        company_a_id=comp_a.id,
                        company_b_id=comp_b.id,
                        connection_type="mentioned_together",
                        description=(
                            f"{comp_b.name} appears in search results for {comp_a.name}: "
                            f'"{result.title}".'
                        ),
                        evidence_urls=[result.url],
                        strength=0.4,
                    ))

        # Check if A is mentioned in B's results
        for result in results_b:
            text = f"{result.title} {result.snippet}"
            if _company_mentioned_in(comp_a.name, text):
                signals = _find_relationship_signals(text)
                if signals:
                    for conn_type, strength in signals:
                        connections.append(Connection(
                            company_a_id=comp_a.id,
                            company_b_id=comp_b.id,
                            connection_type=conn_type,
                            description=(
                                f"{comp_a.name} is mentioned in an article about {comp_b.name}: "
                                f'"{result.title}". {result.snippet[:200]}'
                            ),
                            evidence_urls=[result.url],
                            strength=strength,
                        ))
                else:
                    connections.append(Connection(
                        company_a_id=comp_a.id,
                        company_b_id=comp_b.id,
                        connection_type="mentioned_together",
                        description=(
                            f"{comp_a.name} appears in search results for {comp_b.name}: "
                            f'"{result.title}".'
                        ),
                        evidence_urls=[result.url],
                        strength=0.4,
                    ))

        return connections

    def _check_shared_urls(
        self,
        comp_a: Company,
        comp_b: Company,
        results_a: list[SearchResult],
        results_b: list[SearchResult],
    ) -> list[Connection]:
        urls_a = {r.url: r for r in results_a if r.url}
        urls_b = {r.url: r for r in results_b if r.url}
        shared = set(urls_a.keys()) & set(urls_b.keys())

        connections = []
        for url in shared:
            result_a = urls_a[url]
            connections.append(Connection(
                company_a_id=comp_a.id,
                company_b_id=comp_b.id,
                connection_type="shared_event",
                description=(
                    f"Both {comp_a.name} and {comp_b.name} appear in the same article: "
                    f'"{result_a.title}". This suggests they were at the same event, '
                    f"in the same industry report, or otherwise connected."
                ),
                evidence_urls=[url],
                strength=0.7,
            ))

        return connections

    def _check_co_occurrence_with_signals(
        self,
        comp_a: Company,
        comp_b: Company,
        results_a: list[SearchResult],
        results_b: list[SearchResult],
    ) -> list[Connection]:
        """Check all results from both companies for co-occurrence with relationship signals."""
        connections = []
        all_results = results_a + results_b
        seen_urls = set()

        for result in all_results:
            if result.url in seen_urls:
                continue
            seen_urls.add(result.url)

            text = f"{result.title} {result.snippet}"
            if _company_mentioned_in(comp_a.name, text) and _company_mentioned_in(comp_b.name, text):
                signals = _find_relationship_signals(text)
                for conn_type, strength in signals:
                    connections.append(Connection(
                        company_a_id=comp_a.id,
                        company_b_id=comp_b.id,
                        connection_type=conn_type,
                        description=(
                            f"Both {comp_a.name} and {comp_b.name} are mentioned together "
                            f'in "{result.title}": {result.snippet[:200]}'
                        ),
                        evidence_urls=[result.url],
                        strength=min(strength + 0.1, 1.0),  # Boost for co-occurrence
                    ))

        return connections

    def _deduplicate(self, connections: list[Connection]) -> list[Connection]:
        """Keep the strongest connection per (company_pair, connection_type)."""
        best: dict[tuple, Connection] = {}
        for conn in connections:
            key = (
                min(conn.company_a_id, conn.company_b_id),
                max(conn.company_a_id, conn.company_b_id),
                conn.connection_type,
            )
            if key not in best or conn.strength > best[key].strength:
                best[key] = conn
            else:
                # Merge evidence URLs
                existing_urls = set(best[key].evidence_urls)
                for url in conn.evidence_urls:
                    if url not in existing_urls:
                        best[key].evidence_urls.append(url)

        return sorted(best.values(), key=lambda c: c.strength, reverse=True)

    def filter_for_clients(
        self,
        connections: list[Connection],
        companies: dict[int, Company],
    ) -> list[Connection]:
        """Only return connections where at least one company is a client."""
        return [
            conn for conn in connections
            if companies.get(conn.company_a_id, Company("", "", False, "")).is_client
            or companies.get(conn.company_b_id, Company("", "", False, "")).is_client
        ]
