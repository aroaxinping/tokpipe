# Changelog

All notable changes to tokpipe will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
