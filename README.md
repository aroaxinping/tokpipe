# tokpipe

Data pipeline for TikTok analytics. Import your exported data, clean it, compute real metrics, and visualize what actually works.

No APIs, no scraping, no third-party tokens. Just your TikTok export files (CSV/XLSX) and Python.

---

## Architecture

```
tokpipe follows a classic ETL pipeline structure:

  Export (TikTok XLSX/CSV)
        |
        v
  +-----------+
  |  ingest   |  --> Load and validate raw export files
  +-----------+
        |
        v
  +-----------+
  |  clean    |  --> Normalize columns, fix types, handle nulls
  +-----------+
        |
        v
  +-----------+
  |  metrics  |  --> Compute engagement rate, retention, trends
  +-----------+
        |
        v
  +-----------+
  |  output   |  --> Dataframes, CSV export, visualizations
  +-----------+
```

### Modules

| Module | What it does |
|---|---|
| `tokpipe.ingest` | Reads TikTok export files (XLSX, CSV). Detects format, validates columns, returns a raw DataFrame. |
| `tokpipe.clean` | Normalizes column names, converts date/number types, drops corrupted rows, fills missing values. |
| `tokpipe.metrics` | Computes derived metrics: engagement rate, average watch time, best posting hour, growth trends. |
| `tokpipe.output` | Exports results to CSV/JSON. Generates matplotlib/seaborn visualizations. |

---

## Requirements

- Python >= 3.10
- Dependencies: pandas, openpyxl, matplotlib, seaborn

---

## Installation

```bash
# Clone the repo
git clone https://github.com/aroaxinping/tokpipe.git
cd tokpipe

# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate

# Install in editable mode with all dependencies
pip install -e .
```

---

## Usage

### 1. Export your TikTok data

Go to TikTok > Creator Tools > Analytics > Export data. Save the XLSX/CSV file somewhere accessible.

### 2. Run the pipeline

```python
from tokpipe import ingest, clean, metrics, output

# Load your export file
raw = ingest.load("path/to/TikTok_Analytics.xlsx")

# Clean and normalize
df = clean.normalize(raw)

# Compute metrics
report = metrics.compute(df)

# Print summary
print(report.summary())

# Export results
output.to_csv(report, "results.csv")

# Generate visualizations
output.plot_engagement(report, save_to="engagement.png")
output.plot_best_hours(report, save_to="best_hours.png")
```

### 3. Quick run (CLI)

```bash
tokpipe analyze path/to/TikTok_Analytics.xlsx --output results/
```

This runs the full pipeline and saves CSV + charts to the output directory.

---

## Available metrics

| Metric | Formula / Description |
|---|---|
| Engagement rate | (likes + comments + shares) / views |
| Average watch time | Total watch time / views |
| Completion rate | Average watch time / video duration |
| Best posting hour | Hour with highest median engagement |
| Growth trend | Rolling 7-day average of views |
| Top performers | Videos above 90th percentile engagement |

---

## Project structure

```
tokpipe/
  src/
    tokpipe/
      __init__.py       # Package init, version
      ingest.py         # Load TikTok exports
      clean.py          # Normalize and clean data
      metrics.py        # Compute derived metrics
      output.py         # Export and visualize
      cli.py            # Command-line interface
  tests/
    test_ingest.py
    test_clean.py
    test_metrics.py
  examples/
    basic_analysis.py   # Minimal working example
  pyproject.toml        # Package config
  LICENSE
  CONTRIBUTING.md
  README.md
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

MIT. See [LICENSE](LICENSE).
