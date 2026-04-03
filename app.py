"""Flask application for the Company Intelligence System."""

import json
import os
import time

from flask import Flask, Response, jsonify, redirect, render_template, request, url_for

import config
from intelligence.connection_mapper import ConnectionMapper
from intelligence.database import Database
from intelligence.excel_parser import parse_excel
from intelligence.report_generator import ReportGenerator
from intelligence.search.mock_provider import MockSearchProvider
from intelligence.search.serp_provider import SerpSearchProvider

app = Flask(__name__)
app.config["SECRET_KEY"] = config.SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = config.MAX_UPLOAD_SIZE_MB * 1024 * 1024

db = Database(config.DATABASE_PATH)


def _get_search_provider(company_names: list[str] = None):
    """Create the configured search provider."""
    if config.SEARCH_PROVIDER == "serp":
        return SerpSearchProvider(config.SERP_API_KEY)
    else:
        return MockSearchProvider(other_company_names=company_names or [])


@app.route("/")
def index():
    """Upload page."""
    return render_template("upload.html")


@app.route("/upload", methods=["POST"])
def upload():
    """Handle Excel file upload."""
    if "file" not in request.files:
        return render_template("upload.html", error="No file selected"), 400

    file = request.files["file"]
    if not file.filename:
        return render_template("upload.html", error="No file selected"), 400

    if not file.filename.endswith((".xlsx", ".xls")):
        return render_template("upload.html", error="Please upload an Excel file (.xlsx or .xls)"), 400

    # Save the uploaded file
    os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
    filepath = os.path.join(config.UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    # Parse the Excel file
    companies, warnings = parse_excel(filepath)

    if not companies:
        error = "No valid companies found. " + " ".join(warnings)
        return render_template("upload.html", error=error), 400

    # Save companies to database
    for company in companies:
        db.save_company(company)

    batch_id = companies[0].upload_batch_id

    # Clean up uploaded file
    try:
        os.remove(filepath)
    except OSError:
        pass

    return redirect(url_for("dashboard", batch_id=batch_id, autoprocess="true"))


@app.route("/api/process/<batch_id>")
def process_batch(batch_id: str):
    """Process a batch of companies via Server-Sent Events."""

    def generate():
        companies = db.get_companies_by_batch(batch_id)
        if not companies:
            yield _sse({"type": "error", "message": "No companies found for this batch"})
            return

        total = len(companies)
        company_names = [c.name for c in companies]
        provider = _get_search_provider(company_names)
        report_gen = ReportGenerator()
        conn_mapper = ConnectionMapper()

        yield _sse({"type": "start", "total": total})

        # Phase 1: Search for each company
        all_results: dict[int, list] = {}
        for i, company in enumerate(companies):
            yield _sse({
                "type": "progress",
                "phase": "search",
                "current": i + 1,
                "total": total,
                "company": company.name,
                "message": f"Searching for {company.name}...",
            })

            query = f'"{company.name}" news events partnerships acquisitions'
            if company.address:
                query += f" {company.address}"

            results = provider.search(query, company.id, config.SEARCH_RESULTS_PER_QUERY)
            all_results[company.id] = results
            db.save_search_results(results)

            time.sleep(config.SEARCH_DELAY_SECONDS)

        # Phase 2: Generate reports
        for i, company in enumerate(companies):
            yield _sse({
                "type": "progress",
                "phase": "report",
                "current": i + 1,
                "total": total,
                "company": company.name,
                "message": f"Generating report for {company.name}...",
            })

            report = report_gen.generate(
                company,
                all_results.get(company.id, []),
                companies,
            )
            db.save_report(report)

        # Phase 3: Map connections
        yield _sse({
            "type": "progress",
            "phase": "connections",
            "current": 1,
            "total": 1,
            "message": "Mapping connections between companies...",
        })

        connections = conn_mapper.find_connections(companies, all_results)
        if connections:
            db.delete_connections_by_batch(batch_id)
            db.save_connections(connections)

        yield _sse({
            "type": "complete",
            "message": f"Processing complete! Analyzed {total} companies, found {len(connections)} connections.",
            "batch_id": batch_id,
        })

    return Response(generate(), mimetype="text/event-stream")


@app.route("/dashboard/<batch_id>")
def dashboard(batch_id: str):
    """Main results dashboard."""
    companies = db.get_companies_by_batch(batch_id)
    if not companies:
        return render_template("upload.html", error="Batch not found"), 404

    # Get reports for each company
    company_reports = []
    for company in companies:
        report = db.get_report(company.id)
        company_reports.append({"company": company, "report": report})

    # Get connections (client-filtered by default)
    connections = db.get_connections_by_batch(batch_id, client_only=True)
    all_connections = db.get_connections_by_batch(batch_id, client_only=False)

    autoprocess = request.args.get("autoprocess") == "true"
    has_reports = any(cr["report"] is not None for cr in company_reports)

    return render_template(
        "dashboard.html",
        batch_id=batch_id,
        company_reports=company_reports,
        connections=connections,
        total_connections=len(all_connections),
        client_connections=len(connections),
        autoprocess=autoprocess and not has_reports,
    )


@app.route("/report/<int:company_id>")
def report_detail(company_id: int):
    """Detailed report for a single company."""
    company = db.get_company(company_id)
    if not company:
        return "Company not found", 404

    report = db.get_report(company_id)
    search_results = db.get_search_results(company_id)

    # Get all companies in the same batch for context
    all_companies = db.get_companies_by_batch(company.upload_batch_id)

    # Get connections involving this company
    all_connections = db.get_connections_by_batch(company.upload_batch_id, client_only=False)
    company_connections = [
        c for c in all_connections
        if c["company_a_id"] == company_id or c["company_b_id"] == company_id
    ]

    return render_template(
        "report.html",
        company=company,
        report=report,
        search_results=search_results,
        connections=company_connections,
        batch_id=company.upload_batch_id,
    )


@app.route("/connections/<batch_id>")
def connections_view(batch_id: str):
    """Connections view with client filter."""
    companies = db.get_companies_by_batch(batch_id)
    if not companies:
        return "Batch not found", 404

    show_all = request.args.get("show_all") == "true"
    connections = db.get_connections_by_batch(batch_id, client_only=not show_all)
    all_connections = db.get_connections_by_batch(batch_id, client_only=False)

    return render_template(
        "connections.html",
        batch_id=batch_id,
        companies=companies,
        connections=connections,
        total_connections=len(all_connections),
        show_all=show_all,
    )


def _sse(data: dict) -> str:
    """Format data as a Server-Sent Event."""
    return f"data: {json.dumps(data)}\n\n"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
