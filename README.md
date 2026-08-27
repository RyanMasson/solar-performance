# solar-performance
In this project I built an end-to-end data pipeline using Databricks which pulled data from the DOE’s Photovoltaic Data Acquisition (PVDAQ) Public Datasets. The pipeline batch processed over 44 million rows of sensor data from 13 PV systems in 2020, fed them through a medallion architecture, and served the results to a Streamlit data app for reporting performance ratio over time to stakeholders. A Lakeflow Job orchestrated the pipeline for efficient scheduling and updates.

Data source: Deline, Chris, et al. Photovoltaic Data Acquisition (PVDAQ) Public Datasets. NREL, 21 Dec. 2021, Open Energy Data Initiative (OEDI). https://doi.org/10.25984/1846021

Uses the PVAnalytics library: Vining, Will, et al. pvlib/pvanalytics: Version 0.2.2. Version v0.2.2, Zenodo, 27 Nov. 2024, https://doi.org/10.5281/zenodo.14230321

Full project write-up at ryanmasson.carrd.co

Acknowledgment: I used Anthropic Claude (Opus 5) and Google Gemini (3.6 Flash) during code development for this project.
