import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import pvanalytics
from pvanalytics.metrics import performance_ratio_nrel
from pyspark.sql import SparkSession

st.set_page_config(page_title="Solar System PR Tracker", layout="wide")
st.title("☀️ Solar System Performance Ratio Analysis")

# Initialize Spark session provided natively by Databricks Apps
spark = SparkSession.builder.getOrCreate()

# Cache data loading to prevent re-querying on every UI click
@st.cache_data(ttl=3600)
def generate_system_pr_figure(system_id: int):
    # 1. Fetch time-series data via PySpark
    df_spark = spark.table("pvdaq_catalog.silver.pvdata_2020_joined").filter(f"system_id = {system_id}")
    df = df_spark.toPandas()

    if df.empty:
        raise ValueError(f"No time-series data found for system_id {system_id}.")

    df['utc_measured_on'] = pd.to_datetime(df['utc_measured_on'])
    df = df.set_index('utc_measured_on').sort_index()

    # 2. Fetch metadata via PySpark
    capacities_df = spark.table("pvdaq_catalog.silver.system").filter(f"system_id = {system_id}").select("power").toPandas()
    
    if capacities_df.empty or pd.isna(capacities_df['power'].iloc[0]):
        raise ValueError(f"Missing valid DC capacity metadata for system_id {system_id}.")

    raw_power = float(capacities_df['power'].iloc[0])
    pdc0 = raw_power / 1000.0 if raw_power > 10000 else raw_power

    # 3. Calculate full-series PR baseline
    daytime_full = df[df['poa_irradiance'] >= 50]
    if daytime_full.empty:
        raise ValueError(f"No daytime records (POA >= 50 W/m²) found for system_id {system_id}.")

    pr_whole_series = performance_ratio_nrel(
        poa_global=daytime_full['poa_irradiance'],
        temp_air=daytime_full['ambient_temp'],
        wind_speed=daytime_full['wind_speed'],
        pac=daytime_full['ac_power_kw'],
        pdc0=pdc0
    )

    # 4. Calculate daily metrics
    daily_metrics = []
    for date, data_subset in df.groupby(df.index.date):
        daytime_data = data_subset[data_subset['poa_irradiance'] >= 50]
        if daytime_data.empty:
            continue

        pr = performance_ratio_nrel(
            poa_global=daytime_data['poa_irradiance'],
            temp_air=daytime_data['ambient_temp'],
            wind_speed=daytime_data['wind_speed'],
            pac=daytime_data['ac_power_kw'],
            pdc0=pdc0
        )
        avg_ac_power = data_subset['ac_power_kw'].mean()
        daily_metrics.append({"date": date, "PR": pr, "avg_ac_power_kw": avg_ac_power})

    daily_df = pd.DataFrame(daily_metrics).set_index('date')

    # 5. Build dual-axis Matplotlib figure
    fig, ax1 = plt.subplots(figsize=(12, 5))

    color_pr = 'tab:blue'
    ax1.set_xlabel('Date')
    ax1.set_ylabel('NREL Performance Ratio', color=color_pr)
    line1 = ax1.plot(daily_df.index, daily_df['PR'], color=color_pr, label='Daily PR', alpha=0.8)
    line_base = ax1.axhline(pr_whole_series, color='red', linestyle='--', label=f'Annual PR Baseline ({pr_whole_series:.2f})')
    ax1.tick_params(axis='y', labelcolor=color_pr)

    ax2 = ax1.twinx()
    color_power = 'tab:orange'
    ax2.set_ylabel('Mean AC Power (kW)', color=color_power)
    line2 = ax2.plot(daily_df.index, daily_df['avg_ac_power_kw'], color=color_power, label='Mean Daily AC Power (kW)', alpha=0.5)
    ax2.tick_params(axis='y', labelcolor=color_power)

    lines = line1 + [line_base] + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper left')

    plt.title(f'System {system_id}: Daily NREL PR vs. Mean AC Power Output (2020)')
    plt.xticks(rotation=25)
    plt.tight_layout()

    return fig

# --- UI Controls ---
st.sidebar.header("Controls")
available_systems = [34, 35, 1200, 1201, 1202, 1239, 1276, 1277, 1278, 1283, 1367, 1418, 1419]
selected_sys = st.sidebar.selectbox("Select System ID", available_systems, index=available_systems.index(1419))

with st.spinner("Processing data from Unity Catalog..."):
    try:
        fig = generate_system_pr_figure(selected_sys)
        st.pyplot(fig)
    except Exception as e:
        st.error(f"Error loading system {selected_sys}: {e}")