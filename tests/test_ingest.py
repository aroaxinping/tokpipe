"""Tests for tokpipe.ingest module."""

import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch

from tokpipe.ingest import load


def test_load_file_not_found():
    with pytest.raises(FileNotFoundError):
        load("nonexistent_file.xlsx")


def test_load_unsupported_extension(tmp_path):
    fake_file = tmp_path / "data.txt"
    fake_file.write_text("hello")
    with pytest.raises(ValueError, match="Unsupported file type"):
        load(fake_file)


def test_load_csv(tmp_path):
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("views,likes\n100,10\n200,20\n")
    df = load(csv_file)
    assert len(df) == 2
    assert "views" in df.columns


def test_load_accepts_path_object(tmp_path):
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("views,likes\n100,10\n")
    df = load(Path(csv_file))
    assert isinstance(df, pd.DataFrame)
