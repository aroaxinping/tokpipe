"""
Streamlit demo for tokpipe — runs the full pipeline on the bundled sample data.

Run: streamlit run streamlit_app.py
"""

import tempfile
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from tokpipe import ingest, clean, metrics, dashboard, classify

st.set_page_config(page_title="tokpipe demo", layout="wide", page_icon="📱")

_root = Path(__file__).parent
SAMPLE_PATH = _root / "examples" / "sample_data.csv"


@st.cache_data
def run_pipeline():
    raw = ingest.load(SAMPLE_PATH)
    df = clean.normalize(raw)
    try:
        df["category"] = classify.classify(df)
    except ValueError:
        pass
    report = metrics.compute(df)

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
        dashboard.generate(report, f.name, period="Sample data — Jan 2026")
        html = Path(f.name).read_text()

    return report, html


report, dashboard_html = run_pipeline()

st.sidebar.title("tokpipe")
st.sidebar.markdown("Data pipeline for TikTok analytics")
st.sidebar.markdown("---")
st.sidebar.markdown(
    "This demo runs the full pipeline (ingest → clean → classify → metrics) "
    "on the sample dataset bundled with the package — no TikTok account needed."
)
st.sidebar.markdown(
    "[View on GitHub](https://github.com/aroaxinping/tokpipe) · "
    "[PyPI](https://pypi.org/project/tokpipe/)"
)

st.title("tokpipe — sample analysis")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Videos analyzed", len(report.data))
col2.metric("Avg. engagement rate", f"{report.engagement_rate.mean() * 100:.2f}%")
col3.metric("Avg. virality score", f"{report.virality_score.mean():.3f}")
if report.views_per_day is not None:
    col4.metric("Avg. views/day", f"{report.views_per_day.mean():.0f}")

st.markdown("### Interactive dashboard")
components.html(dashboard_html, height=1400, scrolling=True)

st.markdown("### Top performers")
st.dataframe(report.top_performers, width="stretch", hide_index=True)
