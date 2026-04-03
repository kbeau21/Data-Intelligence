"""Excel file parser for company uploads."""

import uuid

import pandas as pd

from intelligence.models import Company

# Flexible column name mapping
COLUMN_ALIASES = {
    "name": ["company name", "company", "name", "business name", "organization", "org"],
    "address": ["address", "location", "city", "headquarters", "hq", "office address", "street address"],
    "is_client": ["client", "is client", "is_client", "client?", "existing client", "current client", "status"],
}

TRUTHY_VALUES = {"yes", "y", "true", "1", "x", "client", "existing", "current"}


def _match_column(df_columns: list[str], aliases: list[str]) -> str | None:
    """Find a DataFrame column that matches one of the aliases."""
    normalized = {col: col.strip().lower() for col in df_columns}
    for alias in aliases:
        for orig_col, norm_col in normalized.items():
            if norm_col == alias:
                return orig_col
    return None


def parse_excel(file_path: str) -> tuple[list[Company], list[str]]:
    """Parse an Excel file into Company objects.

    Returns (companies, warnings) where warnings contains any parsing issues.
    """
    warnings = []
    batch_id = uuid.uuid4().hex[:12]

    try:
        df = pd.read_excel(file_path, engine="openpyxl")
    except Exception as e:
        return [], [f"Failed to read Excel file: {e}"]

    if df.empty:
        return [], ["Excel file is empty"]

    # Match columns
    name_col = _match_column(list(df.columns), COLUMN_ALIASES["name"])
    address_col = _match_column(list(df.columns), COLUMN_ALIASES["address"])
    client_col = _match_column(list(df.columns), COLUMN_ALIASES["is_client"])

    if not name_col:
        return [], [
            f"Could not find a company name column. "
            f"Found columns: {list(df.columns)}. "
            f"Expected one of: {COLUMN_ALIASES['name']}"
        ]

    if not address_col:
        warnings.append("No address column found — using empty addresses")

    if not client_col:
        warnings.append("No client column found — all companies marked as non-client")

    companies = []
    for idx, row in df.iterrows():
        name = str(row.get(name_col, "")).strip()
        if not name or name.lower() == "nan":
            warnings.append(f"Row {idx + 2}: skipped (empty company name)")
            continue

        address = ""
        if address_col:
            addr_val = row.get(address_col, "")
            address = str(addr_val).strip() if pd.notna(addr_val) else ""

        is_client = False
        if client_col:
            client_val = row.get(client_col, "")
            if pd.notna(client_val):
                is_client = str(client_val).strip().lower() in TRUTHY_VALUES

        companies.append(Company(
            name=name,
            address=address,
            is_client=is_client,
            upload_batch_id=batch_id,
        ))

    if not companies:
        warnings.append("No valid companies found in the file")

    return companies, warnings
