"""Command-line interface for tokpipe."""

import argparse
import sys
from pathlib import Path

from tokpipe import __version__, ingest, clean, metrics, output


def main():
    parser = argparse.ArgumentParser(
        prog="tokpipe",
        description="Data pipeline for TikTok analytics.",
    )
    parser.add_argument("--version", action="version", version=f"tokpipe {__version__}")

    subparsers = parser.add_subparsers(dest="command")

    # analyze command
    analyze = subparsers.add_parser("analyze", help="Run the full pipeline on an export file.")
    analyze.add_argument("file", type=str, help="Path to TikTok export file (XLSX or CSV).")
    analyze.add_argument(
        "--output", "-o",
        type=str,
        default="results",
        help="Output directory for CSV and charts. Default: results/",
    )
    analyze.add_argument(
        "--no-charts",
        action="store_true",
        help="Skip chart generation, only export CSV.",
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if args.command == "analyze":
        run_analyze(args)


def run_analyze(args):
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading {args.file}...")
    raw = ingest.load(args.file)
    print(f"  {len(raw)} rows loaded.")

    print("Cleaning data...")
    df = clean.normalize(raw)
    print(f"  {len(df)} rows after cleaning.")

    print("Computing metrics...")
    report = metrics.compute(df)
    print(report.summary())

    csv_path = out_dir / "report.csv"
    output.to_csv(report, csv_path)
    print(f"\nCSV exported to {csv_path}")

    if not args.no_charts:
        print("Generating charts...")

        output.plot_engagement(report, save_to=out_dir / "engagement.png")
        print(f"  -> {out_dir / 'engagement.png'}")

        try:
            output.plot_best_hours(report, save_to=out_dir / "best_hours.png")
            print(f"  -> {out_dir / 'best_hours.png'}")
        except ValueError:
            print("  -- Skipping best hours (no datetime column found)")

        try:
            output.plot_growth(report, save_to=out_dir / "growth.png")
            print(f"  -> {out_dir / 'growth.png'}")
        except ValueError:
            print("  -- Skipping growth trend (no date data)")

    print("\nDone.")
