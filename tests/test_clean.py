"""Tests for tokpipe.clean module."""

import pandas as pd

from tokpipe.clean import normalize


def test_normalize_column_names():
    df = pd.DataFrame({"Video Views": [100], "Total Likes": [10]})
    result = normalize(df)
    assert "video_views" in result.columns
    assert "total_likes" in result.columns


def test_normalize_strips_whitespace():
    df = pd.DataFrame({" views ": [100]})
    result = normalize(df)
    assert "views" in result.columns


def test_normalize_converts_numeric_strings():
    df = pd.DataFrame({"views": ["1,000", "2,000", "3,000"]})
    result = normalize(df)
    assert result["views"].dtype in ("int64", "float64")
    assert result["views"].iloc[0] == 1000


def test_normalize_drops_empty_rows():
    df = pd.DataFrame({"views": [100, None, 200], "likes": [10, None, 20]})
    result = normalize(df)
    assert len(result) == 2


def test_normalize_converts_dates():
    df = pd.DataFrame({"post_date": ["2026-01-01", "2026-01-02"]})
    result = normalize(df)
    assert pd.api.types.is_datetime64_any_dtype(result["post_date"])
