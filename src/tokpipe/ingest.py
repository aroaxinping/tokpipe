"""Load TikTok export files (XLSX, CSV) into raw DataFrames."""

from pathlib import Path

import pandas as pd


SUPPORTED_EXTENSIONS = {".xlsx", ".csv"}


def load(path: str | Path) -> pd.DataFrame:
    """Load a TikTok analytics export file.

    Args:
        path: Path to the XLSX or CSV file exported from TikTok.

    Returns:
        Raw DataFrame with the original columns and data.

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
        return pd.read_csv(path)

    return pd.read_excel(path, engine="openpyxl")
