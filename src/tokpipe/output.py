"""Export results and generate visualizations."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from tokpipe.metrics import Report


sns.set_theme(style="whitegrid", palette="muted")


def to_csv(report: Report, path: str | Path) -> None:
    """Export the report data with engagement rate to CSV."""
    df = report.data.copy()
    df["engagement_rate"] = report.engagement_rate
    if report.completion_rate is not None:
        df["completion_rate"] = report.completion_rate
    df.to_csv(path, index=False)


def to_json(report: Report, path: str | Path) -> None:
    """Export the report data with engagement rate to JSON."""
    df = report.data.copy()
    df["engagement_rate"] = report.engagement_rate
    df.to_json(path, orient="records", indent=2, date_format="iso")


def plot_engagement(report: Report, save_to: str | Path | None = None) -> None:
    """Plot engagement rate distribution."""
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(report.engagement_rate, bins=30, edgecolor="black", alpha=0.7)
    ax.set_xlabel("Engagement Rate")
    ax.set_ylabel("Number of Videos")
    ax.set_title("Engagement Rate Distribution")
    ax.axvline(
        report.engagement_rate.median(),
        color="red",
        linestyle="--",
        label=f"Median: {report.engagement_rate.median():.4f}",
    )
    ax.legend()
    fig.tight_layout()

    if save_to:
        fig.savefig(save_to, dpi=150)
        plt.close(fig)
    else:
        plt.show()


def plot_best_hours(report: Report, save_to: str | Path | None = None) -> None:
    """Plot median engagement by hour of day."""
    date_col = None
    for col in report.data.columns:
        if pd.api.types.is_datetime64_any_dtype(report.data[col]):
            date_col = col
            break

    if date_col is None:
        raise ValueError("No datetime column found. Cannot plot by hour.")

    hour_data = pd.DataFrame({
        "hour": report.data[date_col].dt.hour,
        "engagement": report.engagement_rate,
    })
    hourly = hour_data.groupby("hour")["engagement"].median()

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(hourly.index, hourly.values, edgecolor="black", alpha=0.7)
    ax.set_xlabel("Hour of Day")
    ax.set_ylabel("Median Engagement Rate")
    ax.set_title("Best Posting Hours")
    ax.set_xticks(range(24))
    fig.tight_layout()

    if save_to:
        fig.savefig(save_to, dpi=150)
        plt.close(fig)
    else:
        plt.show()


def plot_growth(report: Report, save_to: str | Path | None = None) -> None:
    """Plot 7-day rolling average of views."""
    if report.growth_trend is None:
        raise ValueError("No growth trend data. Check that your data has dates.")

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(report.growth_trend.index, report.growth_trend.values, linewidth=2)
    ax.set_xlabel("Date")
    ax.set_ylabel("Views (7-day rolling avg)")
    ax.set_title("Growth Trend")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()

    if save_to:
        fig.savefig(save_to, dpi=150)
        plt.close(fig)
    else:
        plt.show()
