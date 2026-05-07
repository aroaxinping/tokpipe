"""Tests for tokpipe.cli module."""

import os
import subprocess
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
SAMPLE_CSV = REPO_ROOT / "examples" / "sample_data.csv"


def _run_tokpipe(*args):
    """Run tokpipe CLI via a python -c invocation with correct PYTHONPATH.

    We use ``-c`` instead of ``-m tokpipe.cli`` because the package
    does not ship a ``__main__.py`` yet.
    """
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_DIR) + os.pathsep + env.get("PYTHONPATH", "")
    env["MPLBACKEND"] = "Agg"

    argv_literal = ", ".join(repr(a) for a in ("tokpipe", *args))
    script = (
        f"import sys; sys.argv = [{argv_literal}]; "
        "from tokpipe.cli import main; main()"
    )

    return subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
    )


# ---------------------------------------------------------------------------
# No args -> help
# ---------------------------------------------------------------------------

class TestMainNoArgs:
    def test_prints_help(self):
        result = _run_tokpipe()
        combined = result.stdout + result.stderr
        assert result.returncode == 0
        assert "tokpipe" in combined.lower() or "usage" in combined.lower()


# ---------------------------------------------------------------------------
# --version
# ---------------------------------------------------------------------------

class TestMainVersion:
    def test_prints_version(self):
        result = _run_tokpipe("--version")
        combined = result.stdout + result.stderr
        assert result.returncode == 0
        assert "tokpipe" in combined
        # Version string should contain a dotted number
        assert "0." in combined or "1." in combined


# ---------------------------------------------------------------------------
# analyze with sample CSV
# ---------------------------------------------------------------------------

class TestRunAnalyze:
    @pytest.fixture()
    def output_dir(self, tmp_path):
        return tmp_path / "results"

    def test_analyze_sample_csv(self, output_dir):
        """Run the full analyze pipeline on the bundled sample data."""
        assert SAMPLE_CSV.exists(), f"Sample CSV not found at {SAMPLE_CSV}"

        result = _run_tokpipe(
            "analyze",
            str(SAMPLE_CSV),
            "--output", str(output_dir),
            "--no-dashboard",
            "--no-excel",
        )

        assert result.returncode == 0, (
            f"CLI failed.\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )

        # CSV report must exist
        csv_path = output_dir / "report.csv"
        assert csv_path.exists(), f"Expected {csv_path} to be created"
        assert csv_path.stat().st_size > 0

        # At least one chart should be generated
        engagement_png = output_dir / "engagement.png"
        assert engagement_png.exists(), f"Expected {engagement_png} to be created"

    def test_analyze_no_charts(self, output_dir):
        """--no-charts should skip PNG generation."""
        result = _run_tokpipe(
            "analyze",
            str(SAMPLE_CSV),
            "--output", str(output_dir),
            "--no-charts",
            "--no-dashboard",
            "--no-excel",
        )

        assert result.returncode == 0, (
            f"CLI failed.\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )

        # CSV should still exist
        assert (output_dir / "report.csv").exists()

        # Charts should NOT exist
        assert not (output_dir / "engagement.png").exists()
