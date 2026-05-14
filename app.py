import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Mapa Eleições 2022 - 2º Turno", layout="wide")

st.title("Mapa do resultado do 2º Turno das Eleições Presidenciais de 2022 por Município")
st.markdown("---")

@st.cache_data
def load_data():
    df_mapa = gpd.read_file('BR_Municipios_2025.shp')
    df_mapa['geometry'] = df_mapa['geometry'].simplify(tolerance=0.005)
    df_votacao = pd.read_csv(
        'votacao_candidato_munzona_2022_BR.csv',
        sep=';', encoding='latin1',
        dtype={'NR_TURNO': 'int8', 'SG_UF': 'category'},
        usecols=['SG_UF', 'CD_MUNICIPIO', 'NM_MUNICIPIO', 'NR_CANDIDATO',
                 'NM_URNA_CANDIDATO', 'QT_VOTOS_NOMINAIS', 'NR_TURNO']
    )
    df_votacao = df_votacao[df_votacao['NR_TURNO'] == 2]
    df_votacao = df_votacao[df_votacao['SG_UF'] != 'ZZ']
    cols_agg = ['SG_UF', 'CD_MUNICIPIO', 'NM_MUNICIPIO', 'NR_CANDIDATO', 'NM_URNA_CANDIDATO', 'QT_VOTOS_NOMINAIS']
    df_votacao = df_votacao[cols_agg]
    df_votacao = df_votacao.groupby(
        ['SG_UF', 'CD_MUNICIPIO', 'NM_MUNICIPIO', 'NR_CANDIDATO', 'NM_URNA_CANDIDATO'],
        observed=True
    ).sum().reset_index()
    df_votacao = df_votacao.sort_values('QT_VOTOS_NOMINAIS', ascending=False) \
                           .drop_duplicates(subset='CD_MUNICIPIO', keep='first')
    df_votacao['RESULTADO'] = (df_votacao['NR_CANDIDATO'] == 22)
    return df_mapa, df_votacao

@st.cache_data
def load_correspondencia():
    link = 'https://raw.githubusercontent.com/estadao/como-votou-sua-vizinhanca/master/data/votos/correspondencia-tse-ibge.csv'
    df = pd.read_csv(link, dtype={'COD_TSE': 'int32', 'GEOCOD_IBGE': 'object'})
    return df

@st.cache_data
def merge_data(_df_mapa, _df_votacao, _df_equivalencia):
    df_vot = _df_votacao.set_index('CD_MUNICIPIO')
    df_equi = _df_equivalencia.set_index('COD_TSE')
    df_vot_equi = df_vot.join(df_equi).reset_index()
    df_vot_equi['GEOCOD_IBGE'] = df_vot_equi['GEOCOD_IBGE'].astype(str)
    df_mapa_novo = _df_mapa.set_index('CD_MUN').join(
        df_vot_equi.set_index('GEOCOD_IBGE')
    )
    df_mapa_novo = df_mapa_novo.drop(columns=['AJUSTE'], errors='ignore')
    cols_essenciais = ['SG_UF', 'CD_MUNICIPIO', 'NM_MUNICIPIO', 'NR_CANDIDATO', 'NM_URNA_CANDIDATO', 'QT_VOTOS_NOMINAIS']
    df_mapa_novo = df_mapa_novo.dropna(subset=cols_essenciais)
    return df_mapa_novo

with st.spinner("Carregando dados..."):
    df_mapa, df_votacao = load_data()
    df_equivalencia = load_correspondencia()
    df_mapa_novo = merge_data(df_mapa, df_votacao, df_equivalencia)

st.sidebar.header("Filtros")

ufs = sorted(df_mapa_novo['SG_UF'].unique())
selected_ufs = st.sidebar.multiselect("Unidade Federativa", ufs, default=ufs)

candidatos = sorted(df_mapa_novo['NM_URNA_CANDIDATO'].unique())
selected_candidatos = st.sidebar.multiselect("Candidato vencedor", candidatos, default=candidatos)

df_filtered = df_mapa_novo[
    (df_mapa_novo['SG_UF'].isin(selected_ufs)) &
    (df_mapa_novo['NM_URNA_CANDIDATO'].isin(selected_candidatos))
]

col1, col2, col3 = st.columns(3)
with col1:
    total_muni = df_filtered['CD_MUNICIPIO'].nunique()
    st.metric("Municípios exibidos", total_muni)
with col2:
    vitorias_bolsonaro = df_filtered[df_filtered['NR_CANDIDATO'] == 22]['CD_MUNICIPIO'].nunique()
    st.metric("Vitórias de Bolsonaro", vitorias_bolsonaro)
with col3:
    vitorias_lula = df_filtered[df_filtered['NR_CANDIDATO'] == 13]['CD_MUNICIPIO'].nunique()
    st.metric("Vitórias de Lula", vitorias_lula)

st.markdown("---")

st.subheader("Mapa Interativo")

def style_fn(x):
    return {
        'fillColor': '#2ecc71' if x['properties']['RESULTADO'] else '#e74c3c',
        'color': '#555555',
        'weight': 0.5,
        'fillOpacity': 0.7,
    }

def highlight_fn(x):
    return {'weight': 2, 'color': '#333333', 'fillOpacity': 0.9}

popup = folium.GeoJsonPopup(
    fields=['NM_MUNICIPIO', 'SG_UF', 'NM_URNA_CANDIDATO', 'QT_VOTOS_NOMINAIS'],
    aliases=['Município', 'UF', 'Vencedor', 'Votos'],
    localize=True,
    labels=True,
    style='font-size: 13px;',
)

tooltip = folium.GeoJsonTooltip(
    fields=['NM_MUNICIPIO', 'SG_UF'],
    aliases=['', ''],
    localize=True,
    sticky=False,
    labels=False,
    style='font-size: 12px; background: #fff; border: 1px solid #ccc; border-radius: 3px; padding: 3px 6px;',
)

m = folium.Map(location=[-15.5, -54], zoom_start=4, tiles='CartoDB positron',
               width='100%', height='100%', control_scale=True)

folium.GeoJson(
    df_filtered.__geo_interface__,
    style_function=style_fn,
    highlight_function=highlight_fn,
    tooltip=tooltip,
    popup=popup,
).add_to(m)

col_lula = '#e74c3c'
col_bolso = '#2ecc71'
legend_html = f'''
<div style="position: fixed; bottom: 30px; right: 30px; z-index: 1000;
            background: white; padding: 10px 14px; border-radius: 5px;
            box-shadow: 0 0 10px rgba(0,0,0,0.2); font-size: 13px;">
    <p style="margin: 0 0 4px 0; font-weight: bold;">Vencedor</p>
    <p style="margin: 0;"><span style="background:{col_lula}; width:12px; height:12px; display:inline-block; margin-right:6px;"></span>Lula</p>
    <p style="margin: 0;"><span style="background:{col_bolso}; width:12px; height:12px; display:inline-block; margin-right:6px;"></span>Jair Bolsonaro</p>
</div>
'''
m.get_root().html.add_child(folium.Element(legend_html))

st_folium(m, width=1400, height=750, returned_objects=[])

st.markdown("---")
st.subheader("Dados detalhados por município")
cols_mostrar = ['SG_UF', 'NM_MUNICIPIO', 'NM_URNA_CANDIDATO', 'QT_VOTOS_NOMINAIS']
st.dataframe(df_filtered[cols_mostrar].sort_values('QT_VOTOS_NOMINAIS', ascending=False))
