import streamlit as st
import requests
import pandas as pd
from io import StringIO
import json
import geopandas as gpd
import matplotlib.pyplot as plt

st.title("Estonian Population Natural Growth by County")

STATISTIKAAMETI_API_URL = "https://andmed.stat.ee/api/v1/et/stat/RV032"
GEOJSON_FILE = "maakonnad.geojson"

JSON_PAYLOAD_STR = """ {
  "query": [
    {
      "code": "Aasta",
      "selection": {
        "filter": "item",
        "values": [
          "2014","2015","2016","2017","2018",
          "2019","2020","2021","2022","2023"
        ]
      }
    },
    {
      "code": "Maakond",
      "selection": {
        "filter": "item",
        "values": [
          "39","44","49","51","57","59","65",
          "67","70","74","78","82","84","86"
        ]
      }
    },
    {
      "code": "Sugu",
      "selection": {
        "filter": "item",
        "values": ["2","3"]
      }
    }
  ],
  "response": { "format": "csv" }
}
"""

@st.cache_data
def import_data():
    headers = {'Content-Type': 'application/json'}
    payload = json.loads(JSON_PAYLOAD_STR)
    with st.spinner('Fetching data from Statistics Estonia...'):
        r = requests.post(STATISTIKAAMETI_API_URL, json=payload, headers=headers)
    if r.status_code == 200:
        text = r.content.decode('utf-8-sig')
        df = pd.read_csv(StringIO(text))
        return df
    else:
        st.error(f"Failed to retrieve data: {r.status_code}")
        st.write(r.text)
        return None

@st.cache_data
def import_geojson():
    try:
        with st.spinner('Loading geographic data...'):
            return gpd.read_file(GEOJSON_FILE)
    except Exception as e:
        st.error(f"Error loading GeoJSON file: {e}")
        return None

def get_data_for_year(df, year):
    return df[df.Aasta == year] if df is not None else None

def create_plot(df, year):
    if df is None or df.empty:
        return None
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    df.plot(
        column='Loomulik iive',
        ax=ax,
        legend=True,
        cmap='viridis',
        legend_kwds={'label': "Loomulik iive"}
    )
    ax.set_title(f'Loomulik iive maakonniti aastal {year}')
    ax.axis('off')
    plt.tight_layout()
    return fig

# --- Main ---
df = import_data()
gdf = import_geojson()

if df is not None and gdf is not None:
    merged = gdf.merge(df, left_on='MNIMI', right_on='Maakond')
    merged['Loomulik iive'] = merged['Mehed Loomulik iive'] + merged['Naised Loomulik iive']

    st.subheader("Data Overview")
    st.write(f"Years: {merged['Aasta'].min()}–{merged['Aasta'].max()}")
    st.write(f"{len(gdf)} counties loaded")

    years = sorted(merged['Aasta'].unique())
    sel = st.selectbox("Select Year", years, index=len(years)-1)

    year_df = get_data_for_year(merged, sel)
    fig = create_plot(year_df, sel)
    if fig:
        st.pyplot(fig)
    else:
        st.warning("No data for that year.")

    with st.expander("View Data Table"):
        st.dataframe(year_df)

    csv = year_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", csv, file_name=f"growth_{sel}.csv")

else:
    st.warning("Make sure both the API data and GeoJSON file are available.")
