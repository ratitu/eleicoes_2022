# Mapa Eleições 2022 - 2º Turno

Interactive map of the 2022 Brazilian presidential election runoff results by municipality, built with Streamlit and Folium.

## Data

- **Electoral results:** TSE (Superior Electoral Court) — `votacao_candidato_munzona_2022_BR.csv`
- **Municipal boundaries:** IBGE 2025 shapefile — `BR_Municipios_2025.shp`
- **TSE-IBGE correspondence:** [Estadão GitHub repository](https://github.com/estadao/como-votou-sua-vizinhanca)

## How to run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Features

- Color-coded map: green for Bolsonaro, red for Lula
- Municipality-level filtering by state (UF) and winning candidate
- Interactive tooltips and popups with vote counts
- Summary metrics (total municipalities displayed, wins per candidate)
- Sortable data table with detailed results
