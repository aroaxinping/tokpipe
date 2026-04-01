"""Compute derived metrics from cleaned TikTok data."""

from dataclasses import dataclass, field
from datetime import date

import numpy as np
import pandas as pd


@dataclass
class Report:
    """Container for computed metrics and the underlying data."""

    data: pd.DataFrame
    engagement_rate: pd.Series
    like_rate: pd.Series
    comment_rate: pd.Series
    share_rate: pd.Series
    save_rate: pd.Series | None
    virality_score: pd.Series
    views_per_day: pd.Series | None
    avg_watch_time: pd.Series | None
    completion_rate: pd.Series | None
    best_hour: int | None
    growth_trend: pd.Series | None
    top_performers: pd.DataFrame

    def summary(self) -> str:
        lines = [
            f"Total videos:            {len(self.data)}",
            f"Avg engagement rate:     {self.engagement_rate.mean() * 100:.2f}%",
            f"Median engagement rate:  {self.engagement_rate.median() * 100:.2f}%",
            f"Avg like rate:           {self.like_rate.mean() * 100:.2f}%",
            f"Avg share rate:          {self.share_rate.mean() * 100:.2f}%",
            f"Avg virality score:      {self.virality_score.mean():.4f}",
        ]
        if self.views_per_day is not None:
            lines.append(
                f"Avg views/day:           {self.views_per_day.mean():.0f}"
            )
        if self.best_hour is not None:
            lines.append(f"Best posting hour:       {self.best_hour}:00")
        lines.append(f"Top performers:          {len(self.top_performers)} videos")
        return "\n".join(lines)


def _find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Return the first column whose name contains any of the candidate strings."""
    for candidate in candidates:
        for col in df.columns:
            if candidate in col:
                return col
    return None


def compute(df: pd.DataFrame, reference_date: date | None = None) -> Report:
    """Compute all metrics from a cleaned DataFrame.

    Expects columns for views, likes, comments, shares at minimum.
    Optional: saves, watch time, video duration, post date/time.

    Args:
        df: Cleaned DataFrame from clean.normalize() or ingest.load().
        reference_date: Date used to compute days_since_post and views_per_day.
                        Defaults to today.

    Returns:
        Report with all computed metrics.
    """
    if reference_date is None:
        reference_date = date.today()

    views_col    = _find_column(df, ["views", "view", "reproduc", "visualiz"])
    likes_col    = _find_column(df, ["likes", "like", "me_gusta"])
    comments_col = _find_column(df, ["comments", "comment", "comentario"])
    shares_col   = _find_column(df, ["shares", "share", "compartid"])
    saves_col    = _find_column(df, ["saves", "save", "guardad"])
    watch_col    = _find_column(df, ["watch_time", "avg_view_sec", "tiempo_visual"])
    duration_col = _find_column(df, ["duration", "duracion", "duration_sec"])
    date_col     = _find_column(df, ["published_date", "post_time", "date", "fecha"])

    if views_col is None:
        raise ValueError(
            "Could not find a 'views' column. "
            "Available columns: " + ", ".join(df.columns)
        )

    views    = df[views_col].fillna(0)
    likes    = df[likes_col].fillna(0)    if likes_col    else pd.Series(0, index=df.index)
    comments = df[comments_col].fillna(0) if comments_col else pd.Series(0, index=df.index)
    shares   = df[shares_col].fillna(0)   if shares_col   else pd.Series(0, index=df.index)
    saves    = df[saves_col].fillna(0)    if saves_col    else None

    safe_views = views.replace(0, np.nan)

    # Core rates (as fractions 0–1)
    total_interactions = likes + comments + shares + (saves if saves is not None else 0)
    engagement_rate = (total_interactions / safe_views).fillna(0)
    like_rate       = (likes    / safe_views).fillna(0)
    comment_rate    = (comments / safe_views).fillna(0)
    share_rate      = (shares   / safe_views).fillna(0)
    save_rate       = (saves    / safe_views).fillna(0) if saves is not None else None

    # Virality score: log(views/day) × engagement_rate
    views_per_day = None
    virality_score = share_rate.copy()  # fallback: just share rate
    if date_col is not None:
        dates = pd.to_datetime(df[date_col], errors="coerce")
        if dates.notna().any():
            days = (pd.Timestamp(reference_date) - dates).dt.days.clip(lower=1)
            views_per_day = (views / days).round(0)
            virality_score = (
                np.log1p(views_per_day.fillna(0)) * engagement_rate
            ).round(4)

    # Average watch time
    avg_watch_time = df[watch_col] if watch_col else None

    # Completion rate
    completion_rate = None
    if watch_col and duration_col:
        duration = df[duration_col].replace(0, np.nan)
        completion_rate = (df[watch_col] / duration).clip(0, 1)

    # Best posting hour
    best_hour = None
    if date_col:
        dates = pd.to_datetime(df[date_col], errors="coerce")
        if pd.api.types.is_datetime64_any_dtype(dates) and dates.dt.hour.notna().any():
            hour_er = pd.DataFrame({"hour": dates.dt.hour, "er": engagement_rate})
            best_hour = int(hour_er.groupby("hour")["er"].median().idxmax())

    # Growth trend: 7-day rolling avg of views (requires date column)
    growth_trend = None
    if date_col:
        dates = pd.to_datetime(df[date_col], errors="coerce")
        if dates.notna().any():
            daily = (
                pd.DataFrame({"date": dates.dt.date, "views": views})
                .groupby("date")["views"].sum()
                .sort_index()
            )
            growth_trend = daily.rolling(7, min_periods=1).mean()

    # Top performers: above 90th percentile engagement
    threshold = engagement_rate.quantile(0.9)
    top_performers = df[engagement_rate >= threshold].copy()

    return Report(
        data=df,
        engagement_rate=engagement_rate,
        like_rate=like_rate,
        comment_rate=comment_rate,
        share_rate=share_rate,
        save_rate=save_rate,
        virality_score=virality_score,
        views_per_day=views_per_day,
        avg_watch_time=avg_watch_time,
        completion_rate=completion_rate,
        best_hour=best_hour,
        growth_trend=growth_trend,
        top_performers=top_performers,
    )
