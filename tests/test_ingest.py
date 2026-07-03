"""Tests for tokpipe.ingest module."""

from datetime import date

import pytest
import pandas as pd
from pathlib import Path

from tokpipe.ingest import load, _parse_spanish_date, _is_content_export, _normalise_content_export

THIS_YEAR = date.today().year


def test_load_file_not_found():
    with pytest.raises(FileNotFoundError):
        load("nonexistent_file.xlsx")


def test_load_unsupported_extension(tmp_path):
    fake_file = tmp_path / "data.txt"
    fake_file.write_text("hello")
    with pytest.raises(ValueError, match="Unsupported file type"):
        load(fake_file)


def test_load_csv(tmp_path):
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("views,likes\n100,10\n200,20\n")
    df = load(csv_file)
    assert len(df) == 2
    assert "views" in df.columns


def test_load_accepts_path_object(tmp_path):
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("views,likes\n100,10\n")
    df = load(Path(csv_file))
    assert isinstance(df, pd.DataFrame)


# --- _parse_spanish_date ---

def test_parse_spanish_date_basic():
    assert _parse_spanish_date("28 de febrero") == f"{THIS_YEAR}-02-28"


def test_parse_spanish_date_all_months():
    y = THIS_YEAR
    cases = {
        "1 de enero":       f"{y}-01-01",
        "15 de marzo":      f"{y}-03-15",
        "30 de abril":      f"{y}-04-30",
        "5 de mayo":        f"{y}-05-05",
        "10 de junio":      f"{y}-06-10",
        "20 de julio":      f"{y}-07-20",
        "8 de agosto":      f"{y}-08-08",
        "3 de septiembre":  f"{y}-09-03",
        "12 de octubre":    f"{y}-10-12",
        "22 de noviembre":  f"{y}-11-22",
        "31 de diciembre":  f"{y}-12-31",
    }
    for text, expected in cases.items():
        assert _parse_spanish_date(text) == expected, f"Failed for: {text}"


def test_parse_spanish_date_custom_year():
    assert _parse_spanish_date("14 de marzo", year=2025) == "2025-03-14"


def test_parse_spanish_date_zero_pads_day():
    assert _parse_spanish_date("5 de abril") == f"{THIS_YEAR}-04-05"


def test_parse_spanish_date_unrecognised_returns_none():
    assert _parse_spanish_date("March 15") is None
    assert _parse_spanish_date("") is None
    assert _parse_spanish_date("no-date-here") is None


# --- _is_content_export ---

def test_is_content_export_true_with_video_title():
    df = pd.DataFrame({"Video title": ["a"], "Total views": [100]})
    assert _is_content_export(df) is True


def test_is_content_export_true_with_post_time():
    df = pd.DataFrame({"Post time": ["1 de enero"], "Total views": [100]})
    assert _is_content_export(df) is True


def test_is_content_export_false_for_generic():
    df = pd.DataFrame({"views": [100], "likes": [10]})
    assert _is_content_export(df) is False


# --- _normalise_content_export ---

def test_normalise_content_export_renames_columns():
    df = pd.DataFrame({
        "Video title": ["video 1"],
        "Post time": ["10 de febrero"],
        "Total views": [500],
        "Total likes": [50],
        "Total comments": [5],
        "Total shares": [2],
    })
    out = _normalise_content_export(df)
    assert "title" in out.columns
    assert "published_date" in out.columns
    assert "views" in out.columns
    assert "likes" in out.columns
    assert "comments" in out.columns
    assert "shares" in out.columns


def test_normalise_content_export_parses_dates():
    df = pd.DataFrame({
        "Video title": ["v1", "v2"],
        "Post time": ["5 de enero", "20 de marzo"],
        "Total views": [100, 200],
        "Total likes": [10, 20],
        "Total comments": [1, 2],
        "Total shares": [0, 1],
    })
    out = _normalise_content_export(df)
    assert out["published_date"].iloc[0] == f"{THIS_YEAR}-01-05"
    assert out["published_date"].iloc[1] == f"{THIS_YEAR}-03-20"


def test_normalise_content_export_numeric_columns():
    df = pd.DataFrame({
        "Video title": ["v1"],
        "Post time": ["1 de enero"],
        "Total views": ["1,000"],
        "Total likes": ["50"],
        "Total comments": ["5"],
        "Total shares": ["2"],
    })
    out = _normalise_content_export(df)
    # pandas to_numeric with errors='coerce': "1,000" becomes NaN, "50" becomes 50
    assert pd.api.types.is_numeric_dtype(out["likes"])
    assert out["likes"].iloc[0] == 50


def test_normalise_content_export_adds_missing_optional_cols():
    df = pd.DataFrame({
        "Video title": ["v1"],
        "Post time": ["1 de febrero"],
        "Total views": [100],
        "Total likes": [10],
        "Total comments": [1],
        "Total shares": [0],
    })
    out = _normalise_content_export(df)
    for col in ["saves", "new_followers", "avg_view_sec", "completion_pct", "duration_sec"]:
        assert col in out.columns


# --- load() with Content export ---

def test_load_content_export_csv(tmp_path):
    csv_content = (
        "Video title,Post time,Total views,Total likes,Total comments,Total shares\n"
        "mi primer video,10 de febrero,1000,100,10,5\n"
        "otro video,20 de marzo,2000,200,20,10\n"
    )
    csv_file = tmp_path / "content_export.csv"
    csv_file.write_text(csv_content)
    df = load(csv_file)
    assert "title" in df.columns
    assert "published_date" in df.columns
    assert df["views"].iloc[0] == 1000
    assert df["published_date"].iloc[0] == f"{THIS_YEAR}-02-10"
    assert len(df) == 2
