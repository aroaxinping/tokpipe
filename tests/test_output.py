"""Tests for tokpipe.output module."""

import csv
import json

import matplotlib
matplotlib.use("Agg")

import pandas as pd
import pytest

from tokpipe.metrics import Report, compute
from tokpipe.output import plot_best_hours, plot_engagement, plot_growth, to_csv, to_json


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_report(*, with_dates=False, with_growth=False):
    """Build a minimal Report for testing."""
    data = {
        "views": [1000, 2000, 500, 800, 1500, 3000, 700, 1200, 900, 2500],
        "likes": [100, 300, 50, 60, 200, 400, 30, 150, 80, 350],
        "comments": [10, 30, 5, 8, 20, 40, 3, 15, 9, 35],
        "shares": [5, 15, 2, 4, 10, 20, 1, 8, 4, 18],
    }
    if with_dates:
        data["post_date"] = pd.to_datetime([
            "2026-01-01 08:00",
            "2026-01-02 10:00",
            "2026-01-03 14:00",
            "2026-01-04 16:00",
            "2026-01-05 09:00",
            "2026-01-06 11:00",
            "2026-01-07 13:00",
            "2026-01-08 15:00",
            "2026-01-09 08:00",
            "2026-01-10 10:00",
        ])

    df = pd.DataFrame(data)
    report = compute(df)

    if not with_growth:
        report = Report(
            data=report.data,
            engagement_rate=report.engagement_rate,
            like_rate=report.like_rate,
            comment_rate=report.comment_rate,
            share_rate=report.share_rate,
            save_rate=report.save_rate,
            virality_score=report.virality_score,
            views_per_day=report.views_per_day,
            avg_watch_time=report.avg_watch_time,
            completion_rate=report.completion_rate,
            best_hour=report.best_hour,
            growth_trend=None if not with_dates else report.growth_trend,
            top_performers=report.top_performers,
        )

    return report


# ---------------------------------------------------------------------------
# to_csv
# ---------------------------------------------------------------------------

class TestToCsv:
    def test_creates_valid_csv_with_engagement_rate(self, tmp_path):
        report = _make_report()
        csv_path = tmp_path / "out.csv"
        to_csv(report, csv_path)

        assert csv_path.exists()

        with open(csv_path) as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert "engagement_rate" in rows[0]
        assert len(rows) == len(report.data)
        # Verify values are parseable floats
        for row in rows:
            float(row["engagement_rate"])


# ---------------------------------------------------------------------------
# to_json
# ---------------------------------------------------------------------------

class TestToJson:
    def test_creates_valid_json(self, tmp_path):
        report = _make_report()
        json_path = tmp_path / "out.json"
        to_json(report, json_path)

        assert json_path.exists()

        with open(json_path) as f:
            records = json.load(f)

        assert isinstance(records, list)
        assert len(records) == len(report.data)
        assert "engagement_rate" in records[0]


# ---------------------------------------------------------------------------
# plot_engagement
# ---------------------------------------------------------------------------

class TestPlotEngagement:
    def test_generates_png(self, tmp_path):
        report = _make_report()
        png_path = tmp_path / "engagement.png"
        plot_engagement(report, save_to=png_path)

        assert png_path.exists()
        assert png_path.stat().st_size > 0


# ---------------------------------------------------------------------------
# plot_best_hours
# ---------------------------------------------------------------------------

class TestPlotBestHours:
    def test_generates_png_with_datetime(self, tmp_path):
        report = _make_report(with_dates=True)
        png_path = tmp_path / "best_hours.png"
        plot_best_hours(report, save_to=png_path)

        assert png_path.exists()
        assert png_path.stat().st_size > 0

    def test_raises_without_datetime_column(self, tmp_path):
        report = _make_report(with_dates=False)
        with pytest.raises(ValueError, match="No datetime column"):
            plot_best_hours(report, save_to=tmp_path / "nope.png")


# ---------------------------------------------------------------------------
# plot_growth
# ---------------------------------------------------------------------------

class TestPlotGrowth:
    def test_generates_png_with_growth_trend(self, tmp_path):
        report = _make_report(with_dates=True, with_growth=True)
        assert report.growth_trend is not None  # sanity check
        png_path = tmp_path / "growth.png"
        plot_growth(report, save_to=png_path)

        assert png_path.exists()
        assert png_path.stat().st_size > 0

    def test_raises_without_growth_trend(self, tmp_path):
        report = _make_report(with_dates=False)
        assert report.growth_trend is None  # sanity check
        with pytest.raises(ValueError, match="No growth trend"):
            plot_growth(report, save_to=tmp_path / "nope.png")
