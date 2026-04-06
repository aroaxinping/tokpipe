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
        help="Output directory. Default: results/",
    )
    analyze.add_argument(
        "--followers",
        type=int,
        default=None,
        help="Total follower count (used for reach rate and shown in reports).",
    )
    analyze.add_argument(
        "--period",
        type=str,
        default=None,
        help='Analysis period label, e.g. "24 Feb - 23 Mar 2026".',
    )
    analyze.add_argument(
        "--rules",
        type=str,
        default=None,
        help="Path to YAML file with classification rules.",
    )
    analyze.add_argument(
        "--no-charts",
        action="store_true",
        help="Skip chart generation.",
    )
    analyze.add_argument(
        "--no-dashboard",
        action="store_true",
        help="Skip interactive HTML dashboard.",
    )
    analyze.add_argument(
        "--no-excel",
        action="store_true",
        help="Skip Excel report generation.",
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if args.command == "analyze":
        run_analyze(args)


def run_analyze(args):
    from tokpipe import excel, dashboard, classify

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading {args.file}...")
    raw = ingest.load(args.file)
    print(f"  {len(raw)} rows loaded.")

    print("Cleaning data...")
    df = clean.normalize(raw)
    print(f"  {len(df)} rows after cleaning.")

    # Classify content
    try:
        df["category"] = classify.classify(df, rules=args.rules)
        print(f"  Classified into: {', '.join(df['category'].unique())}")
    except ValueError:
        print("  -- Skipping classification (no text column found)")

    print("Computing metrics...")
    report = metrics.compute(df)
    print(report.summary())

    # CSV
    csv_path = out_dir / "report.csv"
    output.to_csv(report, csv_path)
    print(f"\nCSV exported to {csv_path}")

    # Excel
    if not args.no_excel:
        xlsx_path = out_dir / "analytics.xlsx"
        excel.to_excel(report, xlsx_path, followers=args.followers, period=args.period)
        print(f"Excel exported to {xlsx_path}")

    # Charts (PNG)
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

    # Dashboard (HTML)
    if not args.no_dashboard:
        dash_path = out_dir / "dashboard.html"
        dashboard.generate(report, dash_path, followers=args.followers, period=args.period)
        print(f"Dashboard exported to {dash_path}")

    print("\nDone.")
