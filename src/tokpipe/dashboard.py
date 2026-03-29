"""Generate interactive HTML dashboard with Plotly."""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from tokpipe.metrics import Report


def generate(
    report: Report,
    path: str | Path,
    followers: int | None = None,
    period: str | None = None,
) -> None:
    """Generate a self-contained HTML dashboard.

    Args:
        report: Computed metrics report.
        path: Output path for the .html file.
        followers: Total follower count (shown in header).
        period: Analysis period label.
    """
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=(
            "Engagement Rate Distribution",
            "Best Posting Hours",
            "Growth Trend (7-day rolling avg)",
            "Top Performers",
            "Views vs Engagement",
            "Metrics Summary",
        ),
        specs=[
            [{"type": "histogram"}, {"type": "bar"}],
            [{"type": "scatter"}, {"type": "bar"}],
            [{"type": "scatter"}, {"type": "table"}],
        ],
        vertical_spacing=0.08,
        horizontal_spacing=0.08,
    )

    _add_engagement_distribution(fig, report, row=1, col=1)
    _add_best_hours(fig, report, row=1, col=2)
    _add_growth_trend(fig, report, row=2, col=1)
    _add_top_performers(fig, report, row=2, col=2)
    _add_views_vs_engagement(fig, report, row=3, col=1)
    _add_summary_table(fig, report, followers, period, row=3, col=2)

    title = "tokpipe dashboard"
    if period:
        title += f" | {period}"

    fig.update_layout(
        title_text=title,
        title_font_size=20,
        showlegend=False,
        height=1200,
        template="plotly_dark",
    )

    fig.write_html(str(path), include_plotlyjs=True)


def _add_engagement_distribution(fig, report: Report, row: int, col: int) -> None:
    fig.add_trace(
        go.Histogram(
            x=report.engagement_rate,
            nbinsx=30,
            marker_color="#636efa",
        ),
        row=row, col=col,
    )


def _add_best_hours(fig, report: Report, row: int, col: int) -> None:
    date_col = _find_datetime_col(report.data)
    if date_col is None:
        return

    hour_data = pd.DataFrame({
        "hour": report.data[date_col].dt.hour,
        "engagement": report.engagement_rate,
    })
    hourly = hour_data.groupby("hour")["engagement"].median()

    fig.add_trace(
        go.Bar(
            x=hourly.index,
            y=hourly.values,
            marker_color="#00cc96",
        ),
        row=row, col=col,
    )


def _add_growth_trend(fig, report: Report, row: int, col: int) -> None:
    if report.growth_trend is None:
        return

    fig.add_trace(
        go.Scatter(
            x=report.growth_trend.index,
            y=report.growth_trend.values,
            mode="lines",
            line=dict(width=2, color="#ef553b"),
        ),
        row=row, col=col,
    )


def _add_top_performers(fig, report: Report, row: int, col: int) -> None:
    from tokpipe.metrics import _find_column

    views_col = _find_column(report.top_performers, ["views", "view", "reproduc"])
    if views_col is None or len(report.top_performers) == 0:
        return

    top = report.top_performers.head(10)
    labels = [f"Video {i+1}" for i in range(len(top))]

    fig.add_trace(
        go.Bar(
            x=labels,
            y=top[views_col].values,
            marker_color="#ab63fa",
        ),
        row=row, col=col,
    )


def _add_views_vs_engagement(fig, report: Report, row: int, col: int) -> None:
    from tokpipe.metrics import _find_column

    views_col = _find_column(report.data, ["views", "view", "reproduc"])
    if views_col is None:
        return

    fig.add_trace(
        go.Scatter(
            x=report.data[views_col],
            y=report.engagement_rate,
            mode="markers",
            marker=dict(size=6, color="#ffa15a", opacity=0.7),
        ),
        row=row, col=col,
    )


def _add_summary_table(
    fig, report: Report,
    followers: int | None, period: str | None,
    row: int, col: int,
) -> None:
    labels = ["Total videos", "Avg engagement", "Median engagement"]
    values = [
        str(len(report.data)),
        f"{report.engagement_rate.mean():.4f}",
        f"{report.engagement_rate.median():.4f}",
    ]

    if followers:
        labels.append("Followers")
        values.append(str(followers))

    if report.best_hour is not None:
        labels.append("Best hour")
        values.append(f"{report.best_hour}:00")

    labels.append("Top performers")
    values.append(str(len(report.top_performers)))

    fig.add_trace(
        go.Table(
            header=dict(
                values=["Metric", "Value"],
                fill_color="#1a1a2e",
                font=dict(color="white", size=12),
                align="left",
            ),
            cells=dict(
                values=[labels, values],
                fill_color="#16213e",
                font=dict(color="white", size=11),
                align="left",
            ),
        ),
        row=row, col=col,
    )


def _find_datetime_col(df: pd.DataFrame) -> str | None:
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            return col
    return None
