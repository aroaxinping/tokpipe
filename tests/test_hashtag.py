"""Tests for tokpipe.hashtag module."""

from datetime import date

import pandas as pd
import pytest

from tokpipe.metrics import compute
from tokpipe.hashtag import analyse, HashtagReport, _extract_hashtags


def _make_report(titles, views, likes, comments=None, shares=None):
    df = pd.DataFrame({
        "title": titles,
        "views": views,
        "likes": likes,
        "comments": comments or [0] * len(views),
        "shares": shares or [0] * len(views),
    })
    return compute(df)


# --- _extract_hashtags ---

def test_extract_hashtags_basic():
    assert _extract_hashtags("aprende #python con #pandas") == ["python", "pandas"]


def test_extract_hashtags_lowercases():
    assert _extract_hashtags("#Python #DataScience") == ["python", "datascience"]


def test_extract_hashtags_empty_string():
    assert _extract_hashtags("") == []


def test_extract_hashtags_no_hashtags():
    assert _extract_hashtags("just a normal title") == []


def test_extract_hashtags_single():
    assert _extract_hashtags("#tiktok") == ["tiktok"]


def test_extract_hashtags_numbers_in_tag():
    assert _extract_hashtags("#python3 tutorial") == ["python3"]


# --- hashtag.analyse() ---

def test_analyse_returns_hashtag_report():
    report = _make_report(
        titles=["video #python", "otro #python #data"],
        views=[1000, 2000],
        likes=[100, 200],
    )
    hr = analyse(report)
    assert isinstance(hr, HashtagReport)


def test_analyse_table_has_correct_columns():
    report = _make_report(
        titles=["video #python"],
        views=[1000],
        likes=[100],
    )
    hr = analyse(report)
    for col in ("hashtag", "count", "avg_er"):
        assert col in hr.table.columns


def test_analyse_count_is_correct():
    report = _make_report(
        titles=["#python intro", "#python advanced", "#data basics"],
        views=[1000, 2000, 1500],
        likes=[100, 200, 150],
    )
    hr = analyse(report)
    python_row = hr.table[hr.table["hashtag"] == "#python"]
    assert python_row["count"].iloc[0] == 2
    data_row = hr.table[hr.table["hashtag"] == "#data"]
    assert data_row["count"].iloc[0] == 1


def test_analyse_avg_views_computed():
    report = _make_report(
        titles=["#python intro", "#python advanced"],
        views=[1000, 3000],
        likes=[100, 300],
    )
    hr = analyse(report)
    python_row = hr.table[hr.table["hashtag"] == "#python"]
    assert python_row["avg_views"].iloc[0] == pytest.approx(2000.0)


def test_analyse_avg_er_computed():
    # ER = (likes + comments + shares) / views
    report = _make_report(
        titles=["#python vid"],
        views=[1000],
        likes=[100],
        comments=[10],
        shares=[5],
    )
    hr = analyse(report)
    row = hr.table[hr.table["hashtag"] == "#python"]
    assert row["avg_er"].iloc[0] == pytest.approx(0.115)


def test_analyse_avg_shares_computed():
    report = _make_report(
        titles=["#python vid"],
        views=[1000],
        likes=[100],
        shares=[20],
    )
    hr = analyse(report)
    row = hr.table[hr.table["hashtag"] == "#python"]
    assert "avg_shares" in row.columns
    assert row["avg_shares"].iloc[0] == pytest.approx(20.0)


def test_analyse_min_count_filters_rare_tags():
    report = _make_report(
        titles=["#python once", "#rare solo", "#python again"],
        views=[1000, 2000, 1500],
        likes=[100, 200, 150],
    )
    hr = analyse(report, min_count=2)
    assert "#python" in hr.table["hashtag"].values
    assert "#rare" not in hr.table["hashtag"].values


def test_analyse_empty_when_no_hashtags():
    report = _make_report(
        titles=["no hashtags here", "just plain text"],
        views=[1000, 2000],
        likes=[100, 200],
    )
    hr = analyse(report)
    assert hr.table.empty


def test_analyse_raises_if_no_text_column():
    df = pd.DataFrame({"views": [1000], "likes": [100], "comments": [0], "shares": [0]})
    report = compute(df)
    with pytest.raises(ValueError, match="No text column found"):
        analyse(report)


def test_analyse_explicit_text_column():
    df = pd.DataFrame({
        "caption": ["#python tutorial"],
        "views": [1000],
        "likes": [100],
        "comments": [0],
        "shares": [0],
    })
    report = compute(df)
    hr = analyse(report, text_column="caption")
    assert "#python" in hr.table["hashtag"].values


# --- top_by_views / top_by_er ---

def test_top_by_views_ordering():
    report = _make_report(
        titles=["#python low", "#tiktok high", "#data mid"],
        views=[500, 5000, 1500],
        likes=[50, 500, 150],
    )
    hr = analyse(report)
    top = hr.top_by_views
    assert top["hashtag"].iloc[0] == "#tiktok"


def test_top_by_er_ordering():
    report = _make_report(
        titles=["#python lowER", "#data highER"],
        views=[10000, 500],
        likes=[100, 200],   # python ER=0.01, data ER=0.4
    )
    hr = analyse(report)
    top = hr.top_by_er
    assert top["hashtag"].iloc[0] == "#data"


# --- summary ---

def test_summary_returns_string():
    report = _make_report(
        titles=["#python vid", "#data vid"],
        views=[1000, 2000],
        likes=[100, 200],
    )
    hr = analyse(report)
    s = hr.summary()
    assert isinstance(s, str)
    assert "hashtag" in s.lower()
