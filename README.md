# tokpipe

Data pipeline for TikTok analytics. Import your exported data, clean it, classify content, compute real metrics, and visualize what actually works.

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
  | classify  |  --> Tag each video with a topic/category
  +-----------+
        |
        v
  +-----------+
  |  metrics  |  --> Compute engagement rate, retention, trends
  +-----------+
        |
        v
  +-----------+    +-----------+    +-----------+
  |  output   |    |   excel   |    | dashboard |
  | (CSV/PNG) |    |  (.xlsx)  |    |  (.html)  |
  +-----------+    +-----------+    +-----------+
```

### Modules

| Module | What it does |
|---|---|
| `tokpipe.ingest` | Reads TikTok export files (XLSX, CSV). Detects format, validates columns, returns a raw DataFrame. |
| `tokpipe.clean` | Normalizes column names, converts date/number types, drops corrupted rows, fills missing values. |
| `tokpipe.classify` | Assigns a topic/category to each video. Configurable via YAML rules or custom function. |
| `tokpipe.metrics` | Computes derived metrics: engagement rate, average watch time, best posting hour, growth trends. |
| `tokpipe.output` | Exports results to CSV/JSON. Generates matplotlib/seaborn PNG charts. |
| `tokpipe.excel` | Generates Excel report with native formulas, formatting, and embedded charts. |
| `tokpipe.dashboard` | Generates interactive Plotly HTML dashboard with all visualizations. |
| `tokpipe.cli` | Command-line interface. Entry point for `tokpipe analyze`. |

---

## Requirements

- Python >= 3.10
- Dependencies: pandas, openpyxl, matplotlib, seaborn, plotly, pyyaml

---

## Installation

```bash
git clone https://github.com/aroaxinping/tokpipe.git
cd tokpipe

python -m venv .venv
source .venv/bin/activate

pip install -e .
```

---

## Usage

### CLI (recommended)

```bash
# Basic run
tokpipe analyze path/to/TikTok_Analytics.xlsx

# Full run with all options
tokpipe analyze path/to/TikTok_Analytics.xlsx \
  --output results/ \
  --followers 8728 \
  --period "24 Feb - 23 Mar 2026" \
  --rules my_rules.yaml

# Skip specific outputs
tokpipe analyze data.csv --no-dashboard --no-excel
tokpipe analyze data.csv --no-charts
```

This generates:
```
results/
  report.csv           # Clean data + computed metrics
  analytics.xlsx       # Excel with formulas and charts
  dashboard.html       # Interactive Plotly dashboard (open in browser)
  engagement.png       # Engagement rate distribution
  best_hours.png       # Best posting hours chart
  growth.png           # Growth trend chart
```

### Python API

```python
from tokpipe import ingest, clean, classify, metrics, output, excel, dashboard

# Load and clean
raw = ingest.load("TikTok_Analytics.xlsx")
df = clean.normalize(raw)

# Classify content
df["category"] = classify.classify(df)

# Compute metrics
report = metrics.compute(df)
print(report.summary())

# Export
output.to_csv(report, "report.csv")
excel.to_excel(report, "analytics.xlsx", followers=8728)
dashboard.generate(report, "dashboard.html")
```

---

## Content classification

By default, tokpipe classifies videos into: setup, coding, data, study, tech, other.

### Custom rules via YAML

Create a `rules.yaml`:

```yaml
setup:
  - keyboard
  - monitor
  - desk
  - compra
coding:
  - python
  - debug
  - script
data:
  - dataset
  - pandas
  - sql
study:
  - exam
  - uni
  - homework
```

```bash
tokpipe analyze data.xlsx --rules rules.yaml
```

### Custom function (Python API)

```python
def my_classifier(text: str) -> str:
    if "python" in text:
        return "coding"
    if "setup" in text:
        return "setup"
    return "other"

df["category"] = classify.classify(df, classifier_fn=my_classifier)
```

---

## SQL queries

The `sql/` directory contains reference queries for analyzing your exported CSV with DuckDB, SQLite, or any SQL engine:

```bash
# Example with DuckDB
duckdb -c "
  CREATE TABLE videos AS SELECT * FROM read_csv_auto('results/report.csv');
  SELECT * FROM videos ORDER BY engagement_rate DESC LIMIT 10;
"
```

See [sql/queries.sql](sql/queries.sql) for the full set.

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
      cli.py            # Command-line interface
      ingest.py         # Load TikTok exports
      clean.py          # Normalize and clean data
      classify.py       # Content classifier (YAML / custom function)
      metrics.py        # Compute derived metrics
      output.py         # CSV/JSON export + matplotlib charts
      excel.py          # Excel report with formulas
      dashboard.py      # Interactive Plotly HTML dashboard
  tests/
    test_ingest.py
    test_clean.py
    test_metrics.py
  sql/
    queries.sql         # Reference SQL queries
  examples/
    basic_analysis.py   # Minimal working example
  pyproject.toml
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
