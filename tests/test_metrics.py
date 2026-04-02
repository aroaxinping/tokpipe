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
