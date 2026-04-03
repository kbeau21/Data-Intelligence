"""SQLite storage layer for the Company Intelligence System."""

import json
import sqlite3
from datetime import datetime

from intelligence.models import Company, Connection, Report, SearchResult


class Database:
    def __init__(self, db_path: str = "intelligence.db"):
        self.db_path = db_path
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_schema(self):
        conn = self._connect()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address TEXT NOT NULL DEFAULT '',
                is_client BOOLEAN NOT NULL DEFAULT 0,
                upload_batch_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS search_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL,
                query TEXT NOT NULL,
                title TEXT NOT NULL,
                snippet TEXT NOT NULL DEFAULT '',
                url TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL DEFAULT '',
                published_date TEXT,
                FOREIGN KEY (company_id) REFERENCES companies(id)
            );

            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL UNIQUE,
                overview TEXT NOT NULL DEFAULT '',
                recent_news_json TEXT NOT NULL DEFAULT '[]',
                relevance_analysis TEXT NOT NULL DEFAULT '',
                outreach_suggestions_json TEXT NOT NULL DEFAULT '[]',
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies(id)
            );

            CREATE TABLE IF NOT EXISTS connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_a_id INTEGER NOT NULL,
                company_b_id INTEGER NOT NULL,
                connection_type TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                evidence_urls_json TEXT NOT NULL DEFAULT '[]',
                strength REAL NOT NULL DEFAULT 0.0,
                FOREIGN KEY (company_a_id) REFERENCES companies(id),
                FOREIGN KEY (company_b_id) REFERENCES companies(id)
            );

            CREATE INDEX IF NOT EXISTS idx_companies_batch ON companies(upload_batch_id);
            CREATE INDEX IF NOT EXISTS idx_search_results_company ON search_results(company_id);
            CREATE INDEX IF NOT EXISTS idx_connections_batch ON connections(company_a_id, company_b_id);
        """)
        conn.commit()
        conn.close()

    # -- Companies --

    def save_company(self, company: Company) -> Company:
        conn = self._connect()
        cursor = conn.execute(
            "INSERT INTO companies (name, address, is_client, upload_batch_id) VALUES (?, ?, ?, ?)",
            (company.name, company.address, company.is_client, company.upload_batch_id),
        )
        company.id = cursor.lastrowid
        conn.commit()
        conn.close()
        return company

    def get_companies_by_batch(self, batch_id: str) -> list[Company]:
        conn = self._connect()
        rows = conn.execute(
            "SELECT * FROM companies WHERE upload_batch_id = ? ORDER BY name", (batch_id,)
        ).fetchall()
        conn.close()
        return [self._row_to_company(r) for r in rows]

    def get_company(self, company_id: int) -> Company | None:
        conn = self._connect()
        row = conn.execute("SELECT * FROM companies WHERE id = ?", (company_id,)).fetchone()
        conn.close()
        return self._row_to_company(row) if row else None

    def _row_to_company(self, row: sqlite3.Row) -> Company:
        return Company(
            id=row["id"],
            name=row["name"],
            address=row["address"],
            is_client=bool(row["is_client"]),
            upload_batch_id=row["upload_batch_id"],
            created_at=row["created_at"],
        )

    # -- Search Results --

    def save_search_results(self, results: list[SearchResult]):
        conn = self._connect()
        conn.executemany(
            "INSERT INTO search_results (company_id, query, title, snippet, url, source, published_date) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            [(r.company_id, r.query, r.title, r.snippet, r.url, r.source, r.published_date) for r in results],
        )
        conn.commit()
        conn.close()

    def get_search_results(self, company_id: int) -> list[SearchResult]:
        conn = self._connect()
        rows = conn.execute(
            "SELECT * FROM search_results WHERE company_id = ?", (company_id,)
        ).fetchall()
        conn.close()
        return [
            SearchResult(
                id=r["id"],
                company_id=r["company_id"],
                query=r["query"],
                title=r["title"],
                snippet=r["snippet"],
                url=r["url"],
                source=r["source"],
                published_date=r["published_date"],
            )
            for r in rows
        ]

    def get_all_search_results_by_batch(self, batch_id: str) -> dict[int, list[SearchResult]]:
        conn = self._connect()
        rows = conn.execute(
            """SELECT sr.* FROM search_results sr
               JOIN companies c ON sr.company_id = c.id
               WHERE c.upload_batch_id = ?""",
            (batch_id,),
        ).fetchall()
        conn.close()
        results: dict[int, list[SearchResult]] = {}
        for r in rows:
            sr = SearchResult(
                id=r["id"], company_id=r["company_id"], query=r["query"],
                title=r["title"], snippet=r["snippet"], url=r["url"],
                source=r["source"], published_date=r["published_date"],
            )
            results.setdefault(sr.company_id, []).append(sr)
        return results

    # -- Reports --

    def save_report(self, report: Report) -> Report:
        conn = self._connect()
        cursor = conn.execute(
            """INSERT OR REPLACE INTO reports
               (company_id, overview, recent_news_json, relevance_analysis, outreach_suggestions_json, generated_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                report.company_id,
                report.overview,
                json.dumps(report.recent_news),
                report.relevance_analysis,
                json.dumps(report.outreach_suggestions),
                report.generated_at or datetime.now().isoformat(),
            ),
        )
        report.id = cursor.lastrowid
        conn.commit()
        conn.close()
        return report

    def get_report(self, company_id: int) -> Report | None:
        conn = self._connect()
        row = conn.execute("SELECT * FROM reports WHERE company_id = ?", (company_id,)).fetchone()
        conn.close()
        if not row:
            return None
        return Report(
            id=row["id"],
            company_id=row["company_id"],
            overview=row["overview"],
            recent_news=json.loads(row["recent_news_json"]),
            relevance_analysis=row["relevance_analysis"],
            outreach_suggestions=json.loads(row["outreach_suggestions_json"]),
            generated_at=row["generated_at"],
        )

    # -- Connections --

    def save_connections(self, connections: list[Connection]):
        conn = self._connect()
        conn.executemany(
            """INSERT INTO connections
               (company_a_id, company_b_id, connection_type, description, evidence_urls_json, strength)
               VALUES (?, ?, ?, ?, ?, ?)""",
            [
                (c.company_a_id, c.company_b_id, c.connection_type, c.description,
                 json.dumps(c.evidence_urls), c.strength)
                for c in connections
            ],
        )
        conn.commit()
        conn.close()

    def get_connections_by_batch(self, batch_id: str, client_only: bool = True) -> list[dict]:
        """Get connections for a batch. If client_only=True, only return connections
        where at least one company is marked as a client."""
        conn = self._connect()
        query = """
            SELECT conn.*, ca.name as company_a_name, ca.is_client as a_is_client,
                   cb.name as company_b_name, cb.is_client as b_is_client
            FROM connections conn
            JOIN companies ca ON conn.company_a_id = ca.id
            JOIN companies cb ON conn.company_b_id = cb.id
            WHERE ca.upload_batch_id = ?
        """
        if client_only:
            query += " AND (ca.is_client = 1 OR cb.is_client = 1)"
        query += " ORDER BY conn.strength DESC"

        rows = conn.execute(query, (batch_id,)).fetchall()
        conn.close()
        return [
            {
                "id": r["id"],
                "company_a_id": r["company_a_id"],
                "company_b_id": r["company_b_id"],
                "company_a_name": r["company_a_name"],
                "company_b_name": r["company_b_name"],
                "a_is_client": bool(r["a_is_client"]),
                "b_is_client": bool(r["b_is_client"]),
                "connection_type": r["connection_type"],
                "description": r["description"],
                "evidence_urls": json.loads(r["evidence_urls_json"]),
                "strength": r["strength"],
            }
            for r in rows
        ]

    def delete_connections_by_batch(self, batch_id: str):
        conn = self._connect()
        conn.execute(
            """DELETE FROM connections WHERE company_a_id IN
               (SELECT id FROM companies WHERE upload_batch_id = ?)""",
            (batch_id,),
        )
        conn.commit()
        conn.close()
