# sheets.py — Google Sheets commission lookup

import gspread
from google.oauth2.service_account import Credentials

from config import SHEET_NAME, SHEET_TAB, COMMISSION_COL_CATEGORY, COMMISSION_COL_PERCENT

# Module-level cache
_commission_cache = None


def load_commission_sheet() -> dict:
    """Authenticate with gspread, read commission sheet, return {category: percent} dict."""
    global _commission_cache
    if _commission_cache is not None:
        return _commission_cache

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    creds = Credentials.from_service_account_file(
        "service_account.json", scopes=scopes
    )
    client = gspread.authorize(creds)

    sheet = client.open(SHEET_NAME)
    tab = sheet.worksheet(SHEET_TAB)
    rows = tab.get_all_values()

    commission_map = {}
    for row in rows[1:]:  # Skip header
        if len(row) > max(COMMISSION_COL_CATEGORY, COMMISSION_COL_PERCENT):
            category = row[COMMISSION_COL_CATEGORY].strip()
            try:
                percent = float(row[COMMISSION_COL_PERCENT].strip().replace("%", ""))
            except (ValueError, IndexError):
                percent = 0.0
            if category:
                commission_map[category] = percent

    _commission_cache = commission_map
    return _commission_cache


def get_commission(category: str, commission_map: dict) -> float:
    """Look up commission % for a category. Tries exact, case-insensitive, then partial match."""
    if not category or not commission_map:
        return 0.0

    # Exact match
    if category in commission_map:
        return commission_map[category]

    # Case-insensitive match
    cat_lower = category.lower()
    for key, val in commission_map.items():
        if key.lower() == cat_lower:
            return val

    # Partial match
    for key, val in commission_map.items():
        if cat_lower in key.lower() or key.lower() in cat_lower:
            return val

    return 0.0


def refresh_commission_cache():
    """Clear cache and reload from sheet."""
    global _commission_cache
    _commission_cache = None
    return load_commission_sheet()
