"""End-to-end demo: creates a sample Excel file, processes it, and prints results."""

import os
import sys

import pandas as pd

# Ensure we can import from the project root
sys.path.insert(0, os.path.dirname(__file__))

from intelligence.connection_mapper import ConnectionMapper
from intelligence.database import Database
from intelligence.excel_parser import parse_excel
from intelligence.report_generator import ReportGenerator
from intelligence.search.mock_provider import MockSearchProvider


def main():
    # ── Step 1: Create a sample Excel file ──
    print("=" * 70)
    print("  COMPANY INTELLIGENCE SYSTEM — End-to-End Demo")
    print("=" * 70)
    print()

    sample_data = {
        "Company Name": [
            "Pinnacle Solutions",
            "Meridian Group",
            "Atlas Logistics",
            "Vanguard Technologies",
            "Summit Financial",
            "Cornerstone Partners",
        ],
        "Address": [
            "100 Commerce Dr, Chicago, IL",
            "250 Market St, Denver, CO",
            "400 Industrial Blvd, Dallas, TX",
            "75 Innovation Way, Austin, TX",
            "900 Wall St, New York, NY",
            "320 Main St, Chicago, IL",
        ],
        "Client": ["Yes", "No", "Yes", "No", "No", "Yes"],
    }

    excel_path = "/tmp/demo_companies.xlsx"
    df = pd.DataFrame(sample_data)
    df.to_excel(excel_path, index=False)
    print(f"[1/5] Created sample Excel with {len(df)} companies")
    print()

    # ── Step 2: Parse the Excel file ──
    companies, warnings = parse_excel(excel_path)
    if warnings:
        for w in warnings:
            print(f"  WARNING: {w}")
    print(f"[2/5] Parsed {len(companies)} companies from Excel")
    print()

    # Show the parsed companies
    print("  ┌──────────────────────────┬────────────────────────────────┬────────┐")
    print("  │ Company                  │ Address                        │ Client │")
    print("  ├──────────────────────────┼────────────────────────────────┼────────┤")
    for c in companies:
        client_flag = " YES " if c.is_client else "  no "
        print(f"  │ {c.name:<24} │ {c.address:<30} │{client_flag} │")
    print("  └──────────────────────────┴────────────────────────────────┴────────┘")
    print()

    # ── Step 3: Save to DB & run searches ──
    db = Database(":memory:")
    for c in companies:
        db.save_company(c)

    company_names = [c.name for c in companies]
    provider = MockSearchProvider(other_company_names=company_names)

    all_results = {}
    for company in companies:
        query = f'"{company.name}" news events partnerships acquisitions'
        results = provider.search(query, company.id, num_results=10)
        all_results[company.id] = results
        db.save_search_results(results)

    total_results = sum(len(r) for r in all_results.values())
    print(f"[3/5] Searched the web — found {total_results} results across {len(companies)} companies")
    print()

    # ── Step 4: Generate reports ──
    report_gen = ReportGenerator()
    reports = {}
    for company in companies:
        report = report_gen.generate(company, all_results.get(company.id, []), companies)
        reports[company.id] = report
        db.save_report(report)

    print(f"[4/5] Generated intelligence reports")
    print()

    # Print each report
    for company in companies:
        report = reports[company.id]
        client_tag = " [CLIENT]" if company.is_client else " [PROSPECT]"
        print("─" * 70)
        print(f"  {company.name}{client_tag}")
        if company.address:
            print(f"  {company.address}")
        print("─" * 70)
        print()

        print("  OVERVIEW:")
        for line in _wrap(report.overview, 64):
            print(f"    {line}")
        print()

        print("  WHY THIS COMPANY MATTERS:")
        for line in report.relevance_analysis.split("\n"):
            if line.strip():
                for wrapped in _wrap(line.strip(), 64):
                    print(f"    {wrapped}")
        print()

        print("  REASONS TO REACH OUT:")
        for i, suggestion in enumerate(report.outreach_suggestions, 1):
            print(f"    {i}. ", end="")
            lines = _wrap(suggestion, 61)
            print(lines[0])
            for line in lines[1:]:
                print(f"       {line}")
        print()

        print(f"  RECENT NEWS ({len(report.recent_news)} articles):")
        for item in report.recent_news[:5]:
            cats = ", ".join(item.get("categories", []))
            print(f"    - [{item['source']}] {item['title']}")
            if cats:
                print(f"      Tags: {cats}")
            mentions = item.get("mentions_companies", [])
            if mentions:
                print(f"      Also mentions: {', '.join(mentions)}")
        if len(report.recent_news) > 5:
            print(f"    ... and {len(report.recent_news) - 5} more")
        print()
        print()

    # ── Step 5: Map connections ──
    conn_mapper = ConnectionMapper()
    connections = conn_mapper.find_connections(companies, all_results)
    db.save_connections(connections)

    # Get client-filtered connections from DB
    batch_id = companies[0].upload_batch_id
    client_connections = db.get_connections_by_batch(batch_id, client_only=True)
    all_connections = db.get_connections_by_batch(batch_id, client_only=False)

    print(f"[5/5] Mapped connections — {len(all_connections)} total, {len(client_connections)} involving clients")
    print()

    if client_connections:
        print("=" * 70)
        print("  CONNECTIONS (involving your clients)")
        print("=" * 70)
        print()

        for conn in client_connections:
            a_label = f"{conn['company_a_name']}"
            b_label = f"{conn['company_b_name']}"
            if conn["a_is_client"]:
                a_label += " [CLIENT]"
            if conn["b_is_client"]:
                b_label += " [CLIENT]"

            conn_type = conn["connection_type"].replace("_", " ").title()
            strength = int(conn["strength"] * 100)

            print(f"  {a_label}  <-->  {b_label}")
            print(f"  Type: {conn_type} | Confidence: {strength}%")
            print()
            for line in _wrap(conn["description"], 64):
                print(f"    {line}")
            print()

            # Inroad suggestion
            if conn["a_is_client"] and not conn["b_is_client"]:
                print(f"    >> INROAD: Ask {conn['company_a_name']} (your client) for an")
                print(f"       introduction to {conn['company_b_name']}.")
            elif conn["b_is_client"] and not conn["a_is_client"]:
                print(f"    >> INROAD: Ask {conn['company_b_name']} (your client) for an")
                print(f"       introduction to {conn['company_a_name']}.")
            elif conn["a_is_client"] and conn["b_is_client"]:
                print(f"    >> CROSS-CLIENT: Both are your clients. Their {conn_type.lower()}")
                print(f"       connection may present joint solution opportunities.")
            print()
            print("  " + "- " * 35)
            print()

    # Summary
    print("=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    clients = [c for c in companies if c.is_client]
    prospects = [c for c in companies if not c.is_client]
    print(f"  Companies analyzed:    {len(companies)}")
    print(f"  Clients:               {len(clients)} ({', '.join(c.name for c in clients)})")
    print(f"  Prospects:             {len(prospects)} ({', '.join(c.name for c in prospects)})")
    print(f"  Search results found:  {total_results}")
    print(f"  Total connections:     {len(all_connections)}")
    print(f"  Client connections:    {len(client_connections)}")
    print(f"  Actionable inroads:    {sum(1 for c in client_connections if not (c['a_is_client'] and c['b_is_client']))}")
    print()

    # Cleanup
    os.remove(excel_path)


def _wrap(text: str, width: int) -> list[str]:
    """Simple word wrap."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        if current and len(current) + 1 + len(word) > width:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}" if current else word
    if current:
        lines.append(current)
    return lines or [""]


if __name__ == "__main__":
    main()
