"""Normalize and clean raw TikTok data."""

import pandas as pd


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and normalize a raw TikTok export DataFrame.

    Steps:
        1. Normalize column names to snake_case.
        2. Convert date columns to datetime.
        3. Convert numeric columns that came as strings.
        4. Drop rows where all values are null.

    Args:
        df: Raw DataFrame from ingest.load().

    Returns:
        Cleaned DataFrame ready for metrics computation.
    """
    df = df.copy()

    # Normalize column names: lowercase, strip whitespace, replace spaces with underscores
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(r"\s+", "_", regex=True)
        .str.replace(r"[^\w]", "_", regex=True)
    )

    # Try to convert date-like columns (skip if already numeric)
    for col in df.columns:
        if any(keyword in col for keyword in ("date", "time", "created", "posted")):
            if pd.api.types.is_numeric_dtype(df[col]):
                continue
            converted = pd.to_datetime(df[col], errors="coerce")
            # Only convert if at least half the values parsed as dates
            if converted.notna().sum() > len(converted) / 2:
                df[col] = converted

    # Try to convert numeric-like string columns
    for col in df.select_dtypes(include="object").columns:
        try:
            converted = pd.to_numeric(df[col].str.replace(",", ""), errors="coerce")
            # Only convert if at least half the values parsed successfully
            if converted.notna().sum() > len(converted) / 2:
                df[col] = converted
        except (AttributeError, TypeError):
            continue

    # Drop completely empty rows
    df = df.dropna(how="all").reset_index(drop=True)

    return df
