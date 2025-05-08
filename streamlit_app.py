import streamlit as st
import requests
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from io import StringIO
import json
import time

# Constants
STATISTIKAAMETI_API_URL = "https://andmed.stat.ee/api/v1/et/stat/RV032"
GEOJSON_PATH = "maakonnad.geojson"

# County code-to-name mapping (Statistikaamet -> GeoJSON match)
code_to_name = {
    "39": "Harju maakond", "44": "Hiiu maakond", "49": "Ida-Viru maakond",
    "51": "Jõgeva maakond", "57": "Järva maakond", "59": "Lääne maakond",
    "65": "Lääne-Viru maakond", "67": "Põlva maakond", "70": "Pärnu maakond",
    "74": "Rapla maakond", "78": "Saare maakond", "82": "Tartu maakond",
    "84": "Valga maakond", "86": "Viljandi maakond"
}

# API payload for 2023 data
JSON_PAYLOAD = {
    "query": [
        {"code": "Aasta", "selection": {"filter": "item", "values": ["2023"]}},
        {"code": "Maakond", "selection": {"filter": "item", "values": list(code_to_name.keys())}},
        {"code": "Sugu", "selection": {"filter": "item", "values": ["2", "3"]}}
    ],
    "response": {"format": "csv"}
}

@st.cache_data(ttl=3600)
def import_data():
    headers = {"Content-Type": "application/json"}
    start = time.time()
    response = reque
