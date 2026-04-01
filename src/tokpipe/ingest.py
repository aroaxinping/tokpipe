"""Load TikTok export files (XLSX, CSV) into raw DataFrames."""

from pathlib import Path

import pandas as pd


SUPPORTED_EXTENSIONS = {".xlsx", ".csv"}

# Spanish month names used in TikTok Studio exports
_ES_MONTHS = {
    "enero": "01", "febrero": "02", "marzo": "03", "abril": "04",
    "mayo": "05", "junio": "06", "julio": "07", "agosto": "08",
    "septiembre": "09", "octubre": "10", "noviembre": "11", "diciembre": "12",
}

# TikTok Studio Content export column mapping → internal schema
_CONTENT_EXPORT_COLS = {
    "Video title": "title",
    "Post time": "published_date",
    "Total views": "views",
    "Total likes": "likes",
    "Total comments": "comments",
    "Total shares": "shares",
}


def _parse_spanish_date(value: str, year: int = 2026) -> str | None:
    """Parse a Spanish date string like '28 de febrero' into 'YYYY-MM-DD'.

    Args:
        value: Date string from TikTok Studio export.
        year: Year to use when not present in the string. Default: 2026.

    Returns:
        ISO date string or None if parsing fails.
    """
    s = str(value).strip().lower()
    for month_name, month_num in _ES_MONTHS.items():
        if month_name in s:
            parts = s.replace(" de ", " ").split()
            try:
                day = parts[0].zfill(2)
                return f"{year}-{month_num}-{day}"
            except (IndexError, ValueError):
                return None
    return None


def _is_content_export(df: pd.DataFrame) -> bool:
    """Return True if the DataFrame looks like a TikTok Studio Content export."""
    return "Video title" in df.columns or "Post time" in df.columns


def _normalise_content_export(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise a TikTok Studio Content export into the internal schema."""
    # Strip BOM and quotes from column names
    df = df.copy()
    df.columns = df.columns.str.strip().str.lstrip("\ufeff").str.replace('"', "")

    df = df.rename(columns=_CONTENT_EXPORT_COLS)

    # Parse Spanish dates
    if "published_date" in df.columns:
        df["published_date"] = df["published_date"].apply(_parse_spanish_date)

    # Ensure numeric columns are numeric
    for col in ["views", "likes", "comments", "shares"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Add missing optional columns as None
    for col in ["saves", "new_followers", "avg_view_sec", "completion_pct", "duration_sec"]:
        if col not in df.columns:
            df[col] = None

    return df


def load(path: str | Path) -> pd.DataFrame:
    """Load a TikTok analytics export file.

    Supports:
    - TikTok Studio Content export (CSV/XLSX with 'Video title', 'Post time', …)
    - Generic TikTok analytics export (any CSV or XLSX)

    Args:
        path: Path to the XLSX or CSV file exported from TikTok.

    Returns:
        Raw DataFrame. Content exports are automatically normalised to the
        internal schema (title, published_date, views, likes, comments, shares).

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file extension is not supported.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {ext}. Use one of: {SUPPORTED_EXTENSIONS}"
        )

    if ext == ".csv":
        df = pd.read_csv(path)
    else:
        df = pd.read_excel(path, engine="openpyxl")

    if _is_content_export(df):
        df = _normalise_content_export(df)

    return df
