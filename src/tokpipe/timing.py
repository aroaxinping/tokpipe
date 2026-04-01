"""Analyse TikTok performance by day of week."""

from dataclasses import dataclass

import pandas as pd

from .metrics import Report


_DAY_LABELS_ES = {
    "Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles",
    "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sábado",
    "Sunday": "Domingo",
}

_DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


@dataclass
class TimingReport:
    """Performance metrics grouped by day of week."""

    by_day: pd.DataFrame           # index=day_name, cols: n, avg_views, avg_er, avg_vpd
    best_views_day: str            # day with highest avg views
    best_er_day: str               # day with highest avg engagement rate
    best_vpd_day: str | None       # day with highest avg views/day (None if no date data)

    def summary(self) -> str:
        lines = ["Timing analysis by day of week:"]
        lines.append(self.by_day[["n", "avg_views", "avg_er"]].round(2).to_string())
        lines.append(f"\nBest day (views):      {self.best_views_day}")
        lines.append(f"Best day (ER):         {self.best_er_day}")
        if self.best_vpd_day:
            lines.append(f"Best day (views/day):  {self.best_vpd_day}")
        return "\n".join(lines)


def analyse(report: Report, date_column: str = "published_date") -> TimingReport:
    """Compute performance by day of week from a Report.

    Args:
        report: A Report produced by metrics.compute().
        date_column: Name of the date column in report.data. Defaults to
                     'published_date'.

    Returns:
        TimingReport with per-day aggregations and best-day conclusions.

    Raises:
        ValueError: If the date column is not found or has no parseable dates.
    """
    df = report.data.copy()

    # Locate date column
    if date_column not in df.columns:
        # Try to find it
        candidates = [c for c in df.columns if any(k in c for k in ("date", "time", "fecha"))]
        if not candidates:
            raise ValueError(
                f"Date column '{date_column}' not found. "
                f"Available columns: {', '.join(df.columns)}"
            )
        date_column = candidates[0]

    dates = pd.to_datetime(df[date_column], errors="coerce")
    if dates.isna().all():
        raise ValueError(f"Column '{date_column}' contains no parseable dates.")

    df["_day"] = dates.dt.day_name()
    df["_er"]  = report.engagement_rate.values

    views_col = next((c for c in df.columns if "views" in c and "per" not in c), None)
    if views_col is None:
        raise ValueError("No 'views' column found in report data.")

    agg = {"n": (views_col, "count"), "avg_views": (views_col, "mean"), "avg_er": ("_er", "mean")}

    if report.views_per_day is not None:
        df["_vpd"] = report.views_per_day.values
        agg["avg_vpd"] = ("_vpd", "mean")

    by_day = (
        df.groupby("_day")
        .agg(**agg)
        .reindex([d for d in _DAY_ORDER if d in df["_day"].unique()])
    )

    best_views_day = _DAY_LABELS_ES.get(str(by_day["avg_views"].idxmax()), "—")
    best_er_day    = _DAY_LABELS_ES.get(str(by_day["avg_er"].idxmax()), "—")
    best_vpd_day   = None
    if "avg_vpd" in by_day.columns:
        best_vpd_day = _DAY_LABELS_ES.get(str(by_day["avg_vpd"].idxmax()), "—")

    # Translate index to Spanish for readability
    by_day.index = [_DAY_LABELS_ES.get(d, d) for d in by_day.index]

    return TimingReport(
        by_day=by_day,
        best_views_day=best_views_day,
        best_er_day=best_er_day,
        best_vpd_day=best_vpd_day,
    )
