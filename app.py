"""
PVDAQ system performance viewer.

Reproduces the dual-axis Daily NREL PR vs. Mean AC Power chart from the Silver
notebook, reading precomputed daily metrics from the Gold layer over a SQL
warehouse. No Spark session exists in the Databricks Apps runtime, so all data
access goes through databricks-sql-connector.
"""

import os

import matplotlib
matplotlib.use("Agg")  # headless server, no display

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from databricks import sql
from databricks.sdk.core import Config

CATALOG = os.getenv("PVDAQ_CATALOG", "pvdaq_catalog")
SCHEMA = os.getenv("PVDAQ_GOLD_SCHEMA", "gold")
WAREHOUSE_ID = os.getenv("DATABRICKS_WAREHOUSE_ID")

DAILY_TABLE = f"{CATALOG}.{SCHEMA}.system_daily_performance"
ANNUAL_TABLE = f"{CATALOG}.{SCHEMA}.system_annual_performance"


# ---------------------------------------------------------------------------
# Data access
# ---------------------------------------------------------------------------

def _connection():
    """Open a SQL warehouse connection as the app's service principal."""
    if not WAREHOUSE_ID:
        raise RuntimeError(
            "DATABRICKS_WAREHOUSE_ID is not set. Attach a SQL warehouse resource "
            "to the app and confirm the resource key matches app.yaml."
        )

    cfg = Config()  # picks up host + service principal credentials from the runtime
    return sql.connect(
        server_hostname=cfg.host,
        http_path=f"/sql/1.0/warehouses/{WAREHOUSE_ID}",
        credentials_provider=lambda: cfg.authenticate,
    )


def query(statement: str, params: tuple = ()) -> pd.DataFrame:
    with _connection() as conn:
        with conn.cursor() as cur:
            cur.execute(statement, params)
            return cur.fetchall_arrow().to_pandas()


@st.cache_data(ttl=3600)
def load_system_ids() -> list[int]:
    df = query(f"SELECT DISTINCT system_id FROM {ANNUAL_TABLE} ORDER BY system_id")
    return df["system_id"].tolist()


@st.cache_data(ttl=3600)
def load_daily(system_id: int) -> pd.DataFrame:
    df = query(
        f"""
        SELECT date, pr, avg_ac_power_kw
        FROM {DAILY_TABLE}
        WHERE system_id = ?
        ORDER BY date
        """,
        (system_id,),
    )
    df["date"] = pd.to_datetime(df["date"])
    return df.set_index("date")


@st.cache_data(ttl=3600)
def load_annual(system_id: int) -> dict:
    df = query(
        f"""
        SELECT pr_annual, pdc0_kw, public_name
        FROM {ANNUAL_TABLE}
        WHERE system_id = ?
        """,
        (system_id,),
    )
    if df.empty:
        raise ValueError(f"No annual summary found for system_id {system_id}.")
    return df.iloc[0].to_dict()


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

    ax1.set_title(
        f"System {system_id}: Daily NREL PR vs. Mean AC Power Output (2020)"
    )
    fig.autofmt_xdate(rotation=25)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

st.set_page_config(page_title="PVDAQ System Performance", layout="wide")

st.title("PVDAQ system performance, 2020")
st.caption(
    "Daily NREL performance ratio and mean AC power output for PVDAQ systems, "
    "derived from the NREL Photovoltaic Data Acquisition public dataset."
)

try:
    system_ids = load_system_ids()
except Exception as exc:
    st.error(f"Could not reach the Gold tables: {exc}")
    st.stop()

if not system_ids:
    st.warning("No systems found in the Gold layer. Run the Gold notebook first.")
    st.stop()

system_id = st.sidebar.selectbox("System", system_ids)

try:
    annual = load_annual(system_id)
    daily_df = load_daily(system_id)
except Exception as exc:
    st.error(f"Could not load data for system {system_id}: {exc}")
    st.stop()

if daily_df.empty:
    st.warning(f"System {system_id} has no days with usable daytime data.")
    st.stop()

col1, col2, col3 = st.columns(3)
col1.metric("Annual PR", f"{annual['pr_annual']:.3f}")
col2.metric("DC capacity", f"{annual['pdc0_kw']:.1f} kW")
col3.metric("Days with data", f"{len(daily_df):,}")

st.pyplot(build_figure(system_id, daily_df, float(annual["pr_annual"])))

with st.expander("Daily values"):
    st.dataframe(daily_df, use_container_width=True)

st.download_button(
    "Download daily values (CSV)",
    daily_df.to_csv().encode("utf-8"),
    file_name=f"system_{system_id}_daily_performance_2020.csv",
    mime="text/csv",
)