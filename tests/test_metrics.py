"""Tests for tokpipe.metrics module."""

import pandas as pd
import pytest

from tokpipe.metrics import compute


def _make_df(**kwargs):
    return pd.DataFrame(kwargs)


def test_compute_basic():
    df = _make_df(
        views=[1000, 2000, 500],
        likes=[100, 300, 50],
        comments=[10, 30, 5],
        shares=[5, 15, 2],
    )
    report = compute(df)
    assert len(report.engagement_rate) == 3
    assert report.engagement_rate.iloc[0] == pytest.approx(0.115)


def test_compute_no_views_column():
    df = _make_df(something=[1, 2, 3])
    with pytest.raises(ValueError, match="Could not find a 'views' column"):
        compute(df)


def test_compute_with_dates():
    df = _make_df(
        post_date=pd.to_datetime(["2026-01-01 10:00", "2026-01-01 14:00", "2026-01-02 10:00"]),
        views=[1000, 2000, 500],
        likes=[100, 300, 50],
        comments=[10, 30, 5],
        shares=[5, 15, 2],
    )
    report = compute(df)
    assert report.best_hour is not None
    assert report.growth_trend is not None


def test_top_performers():
    views = [100] * 9 + [10000]
    likes = [5] * 9 + [5000]
    df = _make_df(views=views, likes=likes, comments=[0] * 10, shares=[0] * 10)
    report = compute(df)
    assert len(report.top_performers) >= 1


# --- new rate fields ---

def test_like_rate():
    df = _make_df(views=[1000], likes=[100], comments=[0], shares=[0])
    report = compute(df)
    assert report.like_rate.iloc[0] == pytest.approx(0.1)


def test_comment_rate():
    df = _make_df(views=[1000], likes=[0], comments=[50], shares=[0])
    report = compute(df)
    assert report.comment_rate.iloc[0] == pytest.approx(0.05)


def test_share_rate():
    df = _make_df(views=[1000], likes=[0], comments=[0], shares=[20])
    report = compute(df)
    assert report.share_rate.iloc[0] == pytest.approx(0.02)


def test_save_rate_present():
    df = _make_df(views=[1000], likes=[0], comments=[0], shares=[0], saves=[100])
    report = compute(df)
    assert report.save_rate is not None
    assert report.save_rate.iloc[0] == pytest.approx(0.1)


def test_save_rate_absent():
    df = _make_df(views=[1000], likes=[10], comments=[1], shares=[1])
    report = compute(df)
    assert report.save_rate is None


def test_rates_zero_views_no_nan():
    df = _make_df(views=[0], likes=[0], comments=[0], shares=[0])
    report = compute(df)
    assert report.like_rate.iloc[0] == 0.0
    assert report.comment_rate.iloc[0] == 0.0
    assert report.share_rate.iloc[0] == 0.0


# --- virality_score and views_per_day ---

def test_virality_score_with_dates(tmp_path):
    from datetime import date
    df = _make_df(
        published_date=["2026-03-01", "2026-03-15"],
        views=[2000, 500],
        likes=[200, 50],
        comments=[20, 5],
        shares=[10, 2],
    )
    report = compute(df, reference_date=date(2026, 4, 1))
    assert report.views_per_day is not None
    assert report.virality_score is not None
    # video with more views and older date should have lower vpd than if views were higher
    assert report.views_per_day.iloc[0] > 0


def test_virality_score_without_dates():
    df = _make_df(views=[1000], likes=[100], comments=[10], shares=[5])
    report = compute(df)
    # fallback: virality = share_rate
    assert report.virality_score is not None
    assert report.views_per_day is None


def test_views_per_day_uses_reference_date():
    from datetime import date
    df = _make_df(
        published_date=["2026-03-02"],
        views=[300],
        likes=[30],
        comments=[3],
        shares=[1],
    )
    report_a = compute(df, reference_date=date(2026, 3, 12))  # 10 days
    report_b = compute(df, reference_date=date(2026, 4, 1))   # 30 days
    # more days → lower vpd
    assert report_a.views_per_day.iloc[0] > report_b.views_per_day.iloc[0]


# --- summary includes new fields ---

def test_summary_includes_virality():
    df = _make_df(views=[1000], likes=[50], comments=[5], shares=[3])
    report = compute(df)
    s = report.summary()
    assert "virality" in s.lower()
    assert "like rate" in s.lower()
    assert "share rate" in s.lower()
