"""Extract and analyse hashtags from TikTok video titles/captions."""

import re
from dataclasses import dataclass

import pandas as pd

from .metrics import Report


@dataclass
class HashtagReport:
    """Hashtag frequency and performance metrics."""

    table: pd.DataFrame    # cols: hashtag, count, avg_views, avg_er, avg_shares

    @property
    def top_by_views(self) -> pd.DataFrame:
        return self.table.sort_values("avg_views", ascending=False)

    @property
    def top_by_er(self) -> pd.DataFrame:
        return self.table.sort_values("avg_er", ascending=False)

    def summary(self, n: int = 10) -> str:
        lines = [f"Top {n} hashtags by avg views:"]
        lines.append(
            self.top_by_views.head(n)[["hashtag", "count", "avg_views", "avg_er"]]
            .round({"avg_views": 0, "avg_er": 4})
            .to_string(index=False)
        )
        return "\n".join(lines)


def _extract_hashtags(text: str) -> list[str]:
    """Return all lowercase hashtags found in text (without the # prefix)."""
    return re.findall(r"#(\w+)", str(text).lower())


def analyse(
    report: Report,
    text_column: str | None = None,
    min_count: int = 1,
) -> HashtagReport:
    """Analyse hashtag performance from a Report.

    For each unique hashtag found in the text column, computes:
    - count: number of videos it appears in
    - avg_views: mean views across those videos
    - avg_er: mean engagement rate across those videos
    - avg_shares: mean shares across those videos (if available)

    Args:
        report: A Report produced by metrics.compute().
        text_column: Column with video titles/captions. Auto-detected if None.
        min_count: Minimum number of appearances to include a hashtag. Default: 1.

    Returns:
        HashtagReport with per-hashtag metrics.

    Raises:
        ValueError: If no text column is found.
    """
    df = report.data.copy()
    df["_er"] = report.engagement_rate.values

    # Find text column
    if text_column is None:
        candidates = ["title", "caption", "description", "video_title", "texto"]
        text_column = next((c for c in candidates if c in df.columns), None)
        if text_column is None:
            raise ValueError(
                "No text column found. Specify text_column parameter. "
                f"Available columns: {', '.join(df.columns)}"
            )

    views_col  = next((c for c in df.columns if "views" in c and "per" not in c), None)
    shares_col = next((c for c in df.columns if "shares" in c), None)

    # Extract all unique hashtags
    all_tags: list[str] = []
    for text in df[text_column]:
        all_tags.extend(_extract_hashtags(text))
    unique_tags = sorted(set(all_tags))

    rows = []
    for tag in unique_tags:
        mask = df[text_column].str.lower().str.contains(f"#{tag}", regex=False)
        subset = df[mask]
        if len(subset) < min_count:
            continue
        row = {
            "hashtag": f"#{tag}",
            "count": int(mask.sum()),
            "avg_er": round(float(subset["_er"].mean()), 4),
        }
        if views_col:
            row["avg_views"] = round(float(subset[views_col].mean()), 0)
        if shares_col:
            row["avg_shares"] = round(float(subset[shares_col].mean()), 0)
        rows.append(row)

    table = pd.DataFrame(rows)
    if table.empty:
        return HashtagReport(table=table)

    # Sort by frequency descending
    table = table.sort_values("count", ascending=False).reset_index(drop=True)

    return HashtagReport(table=table)
