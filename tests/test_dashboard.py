"""Tests for tokpipe.dashboard module."""

import pandas as pd
import pytest

from tokpipe.dashboard import generate
from tokpipe.metrics import Report


def _make_report(*, with_dates: bool = True) -> Report:
    """Build a minimal Report object for testing.

    Args:
        with_dates: If True, include a datetime column so that
                    growth_trend and best_hour are populated.
    """
    data = {
        "views": [1000, 2000, 500, 800, 1500],
        "likes": [100, 300, 50, 80, 200],
        "comments": [10, 30, 5, 8, 20],
        "shares": [5, 15, 2, 4, 10],
    }
    if with_dates:
        data["post_date"] = pd.to_datetime([
            "2026-01-01 10:00",
            "2026-01-02 14:00",
            "2026-01-03 10:00",
            "2026-01-04 18:00",
            "2026-01-05 10:00",
        ])

    df = pd.DataFrame(data)
    views = df["views"]
    safe_views = views.replace(0, float("nan"))
    engagement_rate = (df["likes"] + df["comments"] + df["shares"]) / safe_views
    engagement_rate = engagement_rate.fillna(0)
    like_rate = (df["likes"] / safe_views).fillna(0)
    comment_rate = (df["comments"] / safe_views).fillna(0)
    share_rate = (df["shares"] / safe_views).fillna(0)
    threshold = engagement_rate.quantile(0.9)
    top_performers = df[engagement_rate >= threshold].copy()

    best_hour = None
    growth_trend = None
    if with_dates:
        hour_eng = pd.DataFrame({
            "hour": df["post_date"].dt.hour,
            "engagement": engagement_rate,
        })
        best_hour = int(hour_eng.groupby("hour")["engagement"].median().idxmax())

        daily = (
            pd.DataFrame({"date": df["post_date"].dt.date, "views": views})
            .groupby("date")["views"]
            .sum()
            .sort_index()
        )
        growth_trend = daily.rolling(7, min_periods=1).mean()

    return Report(
        data=df,
        engagement_rate=engagement_rate,
        like_rate=like_rate,
        comment_rate=comment_rate,
        share_rate=share_rate,
        save_rate=None,
        virality_score=share_rate.copy(),
        views_per_day=None,
        avg_watch_time=None,
        completion_rate=None,
        best_hour=best_hour,
        growth_trend=growth_trend,
        top_performers=top_performers,
    )


class TestGenerate:
    """Tests for dashboard.generate()."""

    def test_creates_html_file(self, tmp_path):
        out = tmp_path / "dash.html"
        generate(_make_report(), out)
        assert out.exists()
        assert out.stat().st_size > 0

    def test_html_contains_plotly(self, tmp_path):
        out = tmp_path / "dash.html"
        generate(_make_report(), out)
        html = out.read_text()
        assert "plotly" in html.lower()

    def test_html_contains_dashboard_title(self, tmp_path):
        out = tmp_path / "dash.html"
        generate(_make_report(), out)
        html = out.read_text()
        assert "tokpipe dashboard" in html

    def test_generate_with_followers(self, tmp_path):
        out = tmp_path / "dash.html"
        generate(_make_report(), out, followers=50_000)
        html = out.read_text()
        assert "50000" in html

    def test_generate_with_period(self, tmp_path):
        out = tmp_path / "dash.html"
        generate(_make_report(), out, period="Jan 2026")
        html = out.read_text()
        assert "Jan 2026" in html

    def test_generate_with_followers_and_period(self, tmp_path):
        out = tmp_path / "dash.html"
        generate(_make_report(), out, followers=12_000, period="Q1 2026")
        html = out.read_text()
        assert "12000" in html
        assert "Q1 2026" in html

    def test_period_appears_in_title(self, tmp_path):
        out = tmp_path / "dash.html"
        generate(_make_report(), out, period="Feb-Mar 2026")
        html = out.read_text()
        assert "tokpipe dashboard | Feb-Mar 2026" in html

    def test_generate_without_dates(self, tmp_path):
        """Dashboard still generates when no datetime columns exist
        (no growth trend, no best hours)."""
        out = tmp_path / "dash.html"
        report = _make_report(with_dates=False)
        assert report.growth_trend is None
        assert report.best_hour is None
        generate(report, out)
        assert out.exists()
        html = out.read_text()
        assert "tokpipe dashboard" in html
        assert "plotly" in html.lower()
