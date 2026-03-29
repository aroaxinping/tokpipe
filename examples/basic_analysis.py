"""Basic example: run tokpipe on a TikTok export file.

Usage:
    python examples/basic_analysis.py path/to/your_export.xlsx
"""

import sys

from tokpipe import ingest, clean, metrics, output


def main():
    if len(sys.argv) < 2:
        print("Usage: python examples/basic_analysis.py <export_file>")
        sys.exit(1)

    file_path = sys.argv[1]

    # 1. Load
    raw = ingest.load(file_path)
    print(f"Loaded {len(raw)} rows from {file_path}")

    # 2. Clean
    df = clean.normalize(raw)
    print(f"Cleaned: {len(df)} rows")

    # 3. Compute metrics
    report = metrics.compute(df)
    print("\n--- Summary ---")
    print(report.summary())

    # 4. Export
    output.to_csv(report, "results.csv")
    print("\nResults saved to results.csv")

    # 5. Visualize
    output.plot_engagement(report, save_to="engagement.png")
    print("Chart saved to engagement.png")


if __name__ == "__main__":
    main()
