"""
PVDAQ system performance viewer — public build.

Reads precomputed metrics from CSVs committed alongside this file, so the app
runs anywhere with no Databricks credentials and no warehouse. The upstream
pipeline (Bronze -> Silver -> Gold in Databricks) produces those CSVs; see
gold_export_for_public_app.py.

Chart construction is identical to the internal build.
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).parent / "data"

# Systems pinned to the top of the dropdown, in this order
FEATURED_SYSTEM_IDS = [1283, 1418, 1419]


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

@st.cache_data
def load_daily() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "system_daily_performance.csv")
    df["date"] = pd.to_datetime(df["date"])
    return df


@st.cache_data
def load_annual() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "system_annual_performance.csv")


@st.cache_data
def load_manifest() -> dict:
    path = DATA_DIR / "manifest.json"
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Plot — same construction as plot_system_pr_and_power() in the Silver notebook
# ---------------------------------------------------------------------------

def build_figure(system_id: int, daily_df: pd.DataFrame, pr_whole_series: float):
    fig, ax1 = plt.subplots(figsize=(12, 6))

    color_pr = "tab:blue"
    ax1.set_xlabel("Date")
    ax1.set_ylabel("NREL Performance Ratio", color=color_pr)
    line1 = ax1.plot(
        daily_df.index, daily_df["pr"], color=color_pr, label="Daily PR", alpha=0.8
    )
    line_base = ax1.axhline(
        pr_whole_series,
        color="red",
        linestyle="--",
        label=f"Annual PR Baseline ({pr_whole_series:.2f})",
    )
    ax1.tick_params(axis="y", labelcolor=color_pr)

    ax2 = ax1.twinx()
    color_power = "tab:orange"
    ax2.set_ylabel("Mean AC Power (kW)", color=color_power)
    line2 = ax2.plot(
        daily_df.index,
        daily_df["avg_ac_power_kw"],
        color=color_power,
        label="Mean Daily AC Power (kW)",
        alpha=0.5,
    )
    ax2.tick_params(axis="y", labelcolor=color_power)

    lines = line1 + [line_base] + line2
    ax1.legend(lines, [l.get_label() for l in lines], loc="upper left")

    ax1.set_title(f"System {system_id}: Daily NREL PR vs. Mean AC Power Output (2020)")
    fig.autofmt_xdate(rotation=25)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

st.set_page_config(page_title="PVDAQ System Performance", layout="wide")

st.markdown(
    """
    <style>
    [data-testid="stSidebar"] .app-title {
        font-size: 2.7rem;
        font-weight: 700;
        line-height: 1.08;
        letter-spacing: -0.02em;
        margin-bottom: 0.6rem;
    }
    [data-testid="stSidebar"] .app-caption {
        font-size: 1.0rem;
        line-height: 1.5;
        opacity: 0.72;
        margin-top: 0.4rem;
    }
    [data-testid="stSidebar"] .app-writeup {
        font-size: 1.0rem;
        line-height: 1.5;
        opacity: 0.72;
        margin-top: 0.7rem;
    }
    .sun-mark {
        display: flex;
        justify-content: center;
        margin: 0.2rem 0 0.6rem 0;
    }
    div[data-testid="stSelectbox"] label p {
        font-size: 1.3rem !important;
        font-weight: 600;
    }
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        font-size: 1.2rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown(
    '<div class="app-title">Solar PV System Performance in 2020</div>',
    unsafe_allow_html=True,
)

st.sidebar.markdown(
    """
    <div class="sun-mark">
    <svg viewBox="0 0 200 200" width="150" height="150" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <radialGradient id="sunCore" cx="42%" cy="38%">
          <stop offset="0%" stop-color="#FFF0BE"/>
          <stop offset="55%" stop-color="#FCB92C"/>
          <stop offset="100%" stop-color="#EF8620"/>
        </radialGradient>
      </defs>
      <g stroke="#F5A623" stroke-width="7" stroke-linecap="round">
        <line x1="100" y1="16" x2="100" y2="40" transform="rotate(0 100 100)"/>
        <line x1="100" y1="24" x2="100" y2="41" transform="rotate(30 100 100)"/>
        <line x1="100" y1="16" x2="100" y2="40" transform="rotate(60 100 100)"/>
        <line x1="100" y1="24" x2="100" y2="41" transform="rotate(90 100 100)"/>
        <line x1="100" y1="16" x2="100" y2="40" transform="rotate(120 100 100)"/>
        <line x1="100" y1="24" x2="100" y2="41" transform="rotate(150 100 100)"/>
        <line x1="100" y1="16" x2="100" y2="40" transform="rotate(180 100 100)"/>
        <line x1="100" y1="24" x2="100" y2="41" transform="rotate(210 100 100)"/>
        <line x1="100" y1="16" x2="100" y2="40" transform="rotate(240 100 100)"/>
        <line x1="100" y1="24" x2="100" y2="41" transform="rotate(270 100 100)"/>
        <line x1="100" y1="16" x2="100" y2="40" transform="rotate(300 100 100)"/>
        <line x1="100" y1="24" x2="100" y2="41" transform="rotate(330 100 100)"/>
      </g>
      <circle cx="100" cy="100" r="44" fill="url(#sunCore)"/>
      <circle cx="100" cy="100" r="44" fill="none" stroke="#EF8620"
              stroke-width="2" opacity="0.5"/>
    </svg>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown(
    '<div class="app-caption">Daily NREL performance ratio and mean AC power '
    "output for 13 PV systems in the NREL Photovoltaic Data Acquisition "
    "(PVDAQ) public dataset.</div>",
    unsafe_allow_html=True,
)

st.sidebar.markdown(
    '<div class="app-writeup">Full project write-up at '
    '<a href="https://ryanmasson.carrd.co" target="_blank">ryanmasson.carrd.co</a></div>',
    unsafe_allow_html=True,
)

try:
    daily_all = load_daily()
    annual_all = load_annual()
except FileNotFoundError:
    st.error(
        "Data files not found. Run the export cell in the Gold notebook and commit "
        "the CSVs under `data/`."
    )
    st.stop()

manifest = load_manifest()

# --- system selection ------------------------------------------------------

labels = {}
for _, row in annual_all.iterrows():
    name = str(row.get("public_name", "")).strip()
    labels[int(row["system_id"])] = (
        name if name and name != "nan" else str(int(row["system_id"]))
    )

featured = [sid for sid in FEATURED_SYSTEM_IDS if sid in labels]
remaining = sorted(sid for sid in labels if sid not in featured)
system_options = featured + remaining

system_id = st.selectbox(
    "System",
    system_options,
    format_func=lambda sid: labels[sid],
)

# --- main ------------------------------------------------------------------

annual_row = annual_all[annual_all["system_id"] == system_id].iloc[0]
daily_df = (
    daily_all[daily_all["system_id"] == system_id]
    .set_index("date")
    .sort_index()[["pr", "avg_ac_power_kw"]]
)

if daily_df.empty:
    st.warning(f"System {system_id} has no days with usable daytime data.")
    st.stop()

col1, col2, col3 = st.columns(3)
col1.metric("Annual PR", f"{annual_row['pr_annual']:.3f}")
col2.metric("DC capacity", f"{annual_row['pdc0_kw']:.1f} kW")
col3.metric("Days with data", f"{len(daily_df):,} of 366")

st.pyplot(build_figure(system_id, daily_df, float(annual_row["pr_annual"])))

with st.expander("Daily values"):
    st.dataframe(daily_df, use_container_width=True)

st.download_button(
    "Download daily values (CSV)",
    daily_df.to_csv().encode("utf-8"),
    file_name=f"system_{system_id}_daily_performance_2020.csv",
    mime="text/csv",
)

# --- footer ----------------------------------------------------------------

st.markdown("---")
generated = manifest.get("generated_at_utc")
st.caption(
    "Source: NREL Photovoltaic Data Acquisition (PVDAQ) public data lake, via the "
    "U.S. Department of Energy Open Energy Data Initiative "
    "(https://data.openei.org/submissions/4568). Metrics computed with "
    "[pvanalytics](https://pvanalytics.readthedocs.io) in a Databricks "
    "medallion pipeline."
    + (f"  \nData generated {generated}." if generated else "")
)