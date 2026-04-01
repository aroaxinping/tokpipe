# Changelog

All notable changes to tokpipe will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-04-01

### Added

- `ingest`: automatic detection and normalisation of TikTok Studio Content exports (CSV/XLSX with 'Video title', 'Post time', …).
- `ingest`: Spanish date parser — converts "28 de febrero" → "2026-02-28" from TikTok Studio exports.
- `metrics`: new fields in `Report` — `like_rate`, `comment_rate`, `share_rate`, `save_rate`, `virality_score`, `views_per_day`.
- `metrics.compute()`: accepts optional `reference_date` argument for reproducible `views_per_day` calculations.
- `timing` module: `timing.analyse(report)` — performance breakdown by day of week (avg views, ER, views/day). Returns `TimingReport` with `best_views_day`, `best_er_day`, `best_vpd_day`.
- `hashtag` module: `hashtag.analyse(report)` — extracts hashtags from titles/captions and computes avg views, ER and shares per tag. Returns `HashtagReport` with `.top_by_views` and `.top_by_er` properties.
- CLI `--timing` flag: runs timing analysis and exports `timing.csv` to output directory.
- CLI `--hashtags` flag: runs hashtag analysis and exports `hashtags.csv` to output directory.

### Changed

- `metrics.Report.summary()` now includes like rate, share rate, virality score, and avg views/day.

---

## [0.1.0] - 2026-03-30

### Added

- Core pipeline: `ingest`, `clean`, `metrics`, `output` modules.
- Content classifier with default rules, YAML config, and custom function support.
- Excel report generation with native formulas, formatting, and embedded charts.
- Interactive Plotly HTML dashboard with 6 panels.
- CLI with `tokpipe analyze` command and options for followers, period, rules.
- SQL reference queries for DuckDB/SQLite.
- Sample CSV data for testing without a TikTok account.
- GitHub Actions CI running tests on Python 3.10-3.13.
- Issue templates for bug reports and feature requests.
