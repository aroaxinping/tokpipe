"""Configurable content classifier for TikTok videos."""

from pathlib import Path
from typing import Callable

import pandas as pd
import yaml


def classify(
    df: pd.DataFrame,
    rules: dict[str, list[str]] | str | Path | None = None,
    text_column: str | None = None,
    classifier_fn: Callable[[str], str] | None = None,
) -> pd.Series:
    """Classify each row into a topic/category.

    Three modes:
        1. Rules dict: {"topic": ["keyword1", "keyword2"]}
        2. YAML file path: loads rules from a YAML file
        3. Custom function: callable that takes text and returns a category

    Args:
        df: DataFrame with a text column (caption, description, title).
        rules: Dict of {category: [keywords]} or path to YAML file.
        text_column: Column name to classify on. Auto-detected if None.
        classifier_fn: Custom function(text) -> category. Overrides rules.

    Returns:
        Series with the assigned category for each row.
    """
    # Find text column
    if text_column is None:
        text_column = _find_text_column(df)

    if text_column is None:
        raise ValueError(
            "No text column found. Specify text_column parameter. "
            f"Available columns: {', '.join(df.columns)}"
        )

    texts = df[text_column].fillna("").astype(str).str.lower()

    # Custom function mode
    if classifier_fn is not None:
        return texts.apply(classifier_fn)

    # Load rules
    if rules is None:
        rules = _default_rules()
    elif isinstance(rules, (str, Path)):
        rules = load_rules(rules)

    return texts.apply(lambda text: _match_rules(text, rules))


def load_rules(path: str | Path) -> dict[str, list[str]]:
    """Load classification rules from a YAML file.

    Expected format:
        setup:
          - keyboard
          - monitor
          - desk
        data:
          - python
          - pandas
          - dataset
    """
    path = Path(path)
    with open(path) as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(f"YAML must be a dict of category: [keywords]. Got: {type(data)}")

    return {k: [str(w).lower() for w in v] for k, v in data.items()}


def _default_rules() -> dict[str, list[str]]:
    return {
        "setup": ["setup", "desk", "keyboard", "monitor", "mouse", "compra"],
        "coding": ["code", "coding", "python", "debug", "script", "terminal"],
        "data": ["data", "dataset", "pandas", "analysis", "csv", "sql"],
        "study": ["study", "exam", "university", "uni", "homework", "assignment"],
        "tech": ["tech", "app", "software", "tool", "gadget"],
    }


def _match_rules(text: str, rules: dict[str, list[str]]) -> str:
    best_category = "other"
    best_count = 0

    for category, keywords in rules.items():
        count = sum(1 for kw in keywords if kw in text)
        if count > best_count:
            best_count = count
            best_category = category

    return best_category


def _find_text_column(df: pd.DataFrame) -> str | None:
    candidates = ["caption", "description", "title", "text", "titulo", "descripcion"]
    for candidate in candidates:
        for col in df.columns:
            if candidate in col.lower():
                return col
    return None
