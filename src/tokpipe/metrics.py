"""Compute derived metrics from cleaned TikTok data."""

from dataclasses import dataclass

import pandas as pd


@dataclass
class Report:
    """Container for computed metrics and the underlying data."""

    data: pd.DataFrame
    engagement_rate: pd.Series
    avg_watch_time: pd.Series | None
    completion_rate: pd.Series | None
    best_hour: int | None
    growth_trend: pd.Series | None
    top_performers: pd.DataFrame

    def summary(self) -> str:
        lines = [
            f"Total videos: {len(self.data)}",
            f"Avg engagement rate: {self.engagement_rate.mean():.4f}",
            f"Median engagement rate: {self.engagement_rate.median():.4f}",
        ]
        if self.best_hour is not None:
            lines.append(f"Best posting hour: {self.best_hour}:00")
        lines.append(f"Top performers: {len(self.top_performers)} videos")
        return "\n".join(lines)


def _find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Find the first matching column name from a list of candidates."""
    for candidate in candidates:
        for col in df.columns:
            if candidate in col:
                return col
    return None


def compute(df: pd.DataFrame) -> Report:
    """Compute all metrics from a cleaned DataFrame.

    Expects columns for views, likes, comments, shares at minimum.
    Optional: watch time, video duration, post date/time.

    Args:
        df: Cleaned DataFrame from clean.normalize().

    Returns:
        Report with all computed metrics.
    """
    views_col = _find_column(df, ["views", "view", "reproduc"])
    likes_col = _find_column(df, ["likes", "like", "me_gusta"])
    comments_col = _find_column(df, ["comments", "comment", "comentario"])
    shares_col = _find_column(df, ["shares", "share", "compartid"])
    watch_time_col = _find_column(df, ["watch_time", "tiempo_visualizacion"])
    duration_col = _find_column(df, ["duration", "duracion", "length"])
    date_col = _find_column(df, ["date", "time", "fecha", "posted", "created"])

    if views_col is None:
        raise ValueError(
            "Could not find a 'views' column. "
            "Available columns: " + ", ".join(df.columns)
        )

    views = df[views_col].fillna(0)
    likes = df[likes_col].fillna(0) if likes_col else 0
    comments = df[comments_col].fillna(0) if comments_col else 0
    shares = df[shares_col].fillna(0) if shares_col else 0

    # Engagement rate
    engagement_rate = (likes + comments + shares) / views.replace(0, pd.NA)
    engagement_rate = engagement_rate.fillna(0)

    # Average watch time
    avg_watch_time = df[watch_time_col] if watch_time_col else None

    # Completion rate
    completion_rate = None
    if watch_time_col and duration_col:
        duration = df[duration_col].replace(0, pd.NA)
        completion_rate = df[watch_time_col] / duration

    # Best posting hour
    best_hour = None
    if date_col and pd.api.types.is_datetime64_any_dtype(df[date_col]):
        hour_engagement = pd.DataFrame({
            "hour": df[date_col].dt.hour,
            "engagement": engagement_rate,
        })
        best_hour = int(
            hour_engagement.groupby("hour")["engagement"].median().idxmax()
        )

    # Growth trend (7-day rolling average of views)
    growth_trend = None
    if date_col and pd.api.types.is_datetime64_any_dtype(df[date_col]):
        daily = (
            pd.DataFrame({"date": df[date_col].dt.date, "views": views})
            .groupby("date")["views"]
            .sum()
            .sort_index()
        )
        growth_trend = daily.rolling(7, min_periods=1).mean()

    # Top performers (above 90th percentile engagement)
    threshold = engagement_rate.quantile(0.9)
    top_performers = df[engagement_rate >= threshold].copy()

    return Report(
        data=df,
        engagement_rate=engagement_rate,
        avg_watch_time=avg_watch_time,
        completion_rate=completion_rate,
        best_hour=best_hour,
        growth_trend=growth_trend,
        top_performers=top_performers,
    )
