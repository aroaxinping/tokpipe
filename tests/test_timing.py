"""Tests for tokpipe.timing module."""

from datetime import date

import pandas as pd
import pytest

from tokpipe.metrics import compute
from tokpipe.timing import analyse, TimingReport


def _make_report(dates, views, likes, comments=None, shares=None, reference_date=None):
    df = pd.DataFrame({
        "published_date": dates,
        "views": views,
        "likes": likes,
        "comments": comments or [0] * len(views),
        "shares": shares or [0] * len(views),
    })
    return compute(df, reference_date=reference_date or date(2026, 4, 1))


# One video per day of the week — Monday through Sunday
_WEEK_DATES = [
    "2026-03-23",  # Monday
    "2026-03-24",  # Tuesday
    "2026-03-25",  # Wednesday
    "2026-03-26",  # Thursday
    "2026-03-27",  # Friday
    "2026-03-28",  # Saturday
    "2026-03-29",  # Sunday
]
_WEEK_VIEWS = [100, 200, 150, 300, 250, 500, 400]
_WEEK_LIKES = [10, 20, 15, 30, 25, 50, 40]


def test_timing_returns_timing_report():
    report = _make_report(_WEEK_DATES, _WEEK_VIEWS, _WEEK_LIKES)
    tr = analyse(report)
    assert isinstance(tr, TimingReport)


def test_timing_by_day_has_all_days():
    report = _make_report(_WEEK_DATES, _WEEK_VIEWS, _WEEK_LIKES)
    tr = analyse(report)
    assert len(tr.by_day) == 7


def test_timing_by_day_index_in_spanish():
    report = _make_report(_WEEK_DATES, _WEEK_VIEWS, _WEEK_LIKES)
    tr = analyse(report)
    spanish_days = {"Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"}
    assert set(tr.by_day.index) == spanish_days


def test_timing_by_day_columns():
    report = _make_report(_WEEK_DATES, _WEEK_VIEWS, _WEEK_LIKES)
    tr = analyse(report)
    for col in ("n", "avg_views", "avg_er"):
        assert col in tr.by_day.columns


def test_timing_best_views_day():
    # Saturday has most views (500)
    report = _make_report(_WEEK_DATES, _WEEK_VIEWS, _WEEK_LIKES)
    tr = analyse(report)
    assert tr.best_views_day == "Sábado"


def test_timing_best_er_day():
    # ER = likes / views; Thursday 30/300 = 0.1, same as Monday 10/100
    # Let's use a clear winner: make Tuesday have high ER
    views = [100, 200, 150, 300, 250, 500, 400]
    likes = [10, 100, 15, 30, 25, 50, 40]  # Tuesday: 100/200 = 0.5
    report = _make_report(_WEEK_DATES, views, likes)
    tr = analyse(report)
    assert tr.best_er_day == "Martes"


def test_timing_best_vpd_day_present_when_dates_available():
    report = _make_report(_WEEK_DATES, _WEEK_VIEWS, _WEEK_LIKES, reference_date=date(2026, 4, 1))
    tr = analyse(report)
    assert tr.best_vpd_day is not None


def test_timing_avg_vpd_column_present_when_dates_available():
    report = _make_report(_WEEK_DATES, _WEEK_VIEWS, _WEEK_LIKES, reference_date=date(2026, 4, 1))
    tr = analyse(report)
    assert "avg_vpd" in tr.by_day.columns


def test_timing_n_column_counts_videos_per_day():
    report = _make_report(_WEEK_DATES, _WEEK_VIEWS, _WEEK_LIKES)
    tr = analyse(report)
    # one video per day
    assert (tr.by_day["n"] == 1).all()


def test_timing_multiple_videos_same_day():
    dates = ["2026-03-23", "2026-03-23", "2026-03-24"]  # 2 Mondays, 1 Tuesday
    views = [100, 200, 300]
    likes = [10, 20, 30]
    report = _make_report(dates, views, likes)
    tr = analyse(report)
    assert tr.by_day.loc["Lunes", "n"] == 2
    assert tr.by_day.loc["Lunes", "avg_views"] == pytest.approx(150.0)


def test_timing_raises_if_no_date_column():
    df = pd.DataFrame({"views": [100, 200], "likes": [10, 20], "comments": [1, 2], "shares": [0, 0]})
    report = compute(df)
    with pytest.raises(ValueError, match="Date column"):
        analyse(report, date_column="published_date")


def test_timing_raises_if_dates_unparseable():
    df = pd.DataFrame({
        "published_date": ["not-a-date", "also-not"],
        "views": [100, 200],
        "likes": [10, 20],
        "comments": [1, 2],
        "shares": [0, 0],
    })
    report = compute(df)
    with pytest.raises(ValueError, match="no parseable dates"):
        analyse(report)


def test_timing_summary_is_string():
    report = _make_report(_WEEK_DATES, _WEEK_VIEWS, _WEEK_LIKES)
    tr = analyse(report)
    s = tr.summary()
    assert isinstance(s, str)
    assert "Sábado" in s  # best views day
