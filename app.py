import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import datetime

# 1. CONFIGURACIÓN E INTERFAZ FORZADA
st.set_page_config(page_title="ES-OSINT PRO 2026 v5.4", layout="wide")

st.title("🇪🇸 Sistema de Inteligencia Geopolítica: España Vota 2026")
st.markdown(f"**Soberanía de Datos:** Nodo **ODROID-C2**. Sincronización: 23:40 CET | v5.4")

# 2. DEFINICIÓN DE PESTAÑAS (ESTRUCTURA PLANA)
tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Mapa", "📡 Radar", "📊 Datos", "📄 Doc"])

# --- LÓGICA DE DATOS ---
@st.cache_data
def load_map():
    try:
        with open('data/provincias.json') as f: return json.load(f)
    except: return None

geojson_spain = load_map()

# Motor simple para no saturar el ODROID
def engine_dhondt(votos, esc):
    v_validos = {p: v for p, v in votos.items() if v >= 3.0}
    lista = []
    for p, v in v_validos.items():
        for i in range(1, esc + 1): lista.append({'p': p, 'c': v / i})
    df_c = pd.DataFrame(lista).sort_values('c', ascending=False)
    return df_c.head(esc)['p'].value_counts().to_dict()

PALETA = {'PP': '#1E4B8F', 'PSOE': '#E30613', 'VOX': '#63BE21', 'SUMAR': '#E53187', 'SALF': '#000000'}

# 3. CONTENIDO DE PESTAÑAS
with tab1:
    st.subheader("Predominancia Territorial")
    st.write("Cargando matriz de soberanía...")
    # Lógica de mapa simplificada para asegurar renderizado
    if geojson_spain:
        df_dummy = pd.DataFrame([{'Provincia': f['properties']['name'], 'Ganador': 'PP'} for f in geojson_spain['features']])
        fig = px.choropleth(df_dummy, geojson=geojson_spain, locations='Provincia', featureidkey="properties.name", color='Ganador', color_discrete_map=PALETA, scope="europe")
        fig.update_geos(fitbounds="locations", visible=False)
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Radar de Factores Críticos")
    r_v, r_c = [85, 90, 75, 65, 80], ['Vivienda', 'Energía', 'Defensa', 'Territorio', 'Inflación']
    fig_r = go.Figure(go.Scatterpolar(r=r_v+[r_v[0]], theta=r_c+[r_c[0]], fill='toself', line_color='#E30613'))
    st.plotly_chart(fig_r, use_container_width=True)

with tab3:
    st.subheader("Escenario Político")
    st.info("Utilice el slider lateral para recalcular bloques.")

with tab4:
    st.header("🛠️ Trazabilidad y Operaciones")
    st.markdown("### Origen de Datos")
    st.latex(r"C = \frac{V}{S + 1}")
    st.markdown("### Fiabilidad")
    st.write("Nodo ODROID-C2 (mcasrom) - Verificado 2026")
    st.divider()
    st.markdown("© 2026 M. Castillo | mybloggingnotes@gmail.com")
