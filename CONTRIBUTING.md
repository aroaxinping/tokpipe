# Contributing to tokpipe

## Getting started

1. Fork the repo
2. Clone your fork
3. Create a virtual environment and install in editable mode:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Making changes

1. Create a branch from `main`:

```bash
git checkout -b your-branch-name
```

2. Make your changes
3. Run the tests:

```bash
python -m pytest tests/
```

4. Commit with a clear message describing what you changed and why
5. Push and open a pull request against `main`

## Code style

- Keep it simple. No abstractions for things that happen once.
- Functions do one thing. If a docstring needs "and", split the function.
- Name things clearly. `compute_engagement_rate` not `calc_er`.

## What to contribute

- New metrics (with formula and tests)
- Support for new TikTok export formats
- Bug fixes
- Better visualizations

## What not to contribute

- API integrations or scraping
- Dependencies on external services
- Features without tests
