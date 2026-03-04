import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import datetime

# CONFIGURACIÓN
st.set_page_config(page_title="ES-OSINT PRO 2026 v5.3", layout="wide")

def get_osint_events():
    return [
        {"f": "2026-02-15", "e": "Inestabilidad Precios Energía", "i": "Alto"},
        {"f": "2026-02-28", "e": "Crisis Acceso Vivienda Joven", "i": "Crítico"},
        {"f": "2026-03-03", "e": "Tensión Territorial: Financiación", "i": "Medio"},
        {"f": "2026-03-04", "e": "Sincronización Maestra v5.3", "i": "OK"}
    ]

st.title("🇪🇸 Sistema de Inteligencia Geopolítica: España Vota 2026")
st.subheader("Análisis Probabilístico y Monitor de Factores Críticos")
st.markdown(f"**Soberanía de Datos:** Nodo **ODROID-C2**. Sync: 23:40 CET")
st.divider()

@st.cache_data
def load_map():
    try:
        with open('data/provincias.json') as f: return json.load(f)
    except: return None

geojson_spain = load_map()

def engine_dhondt(votos, esc):
    v_validos = {p: v for p, v in votos.items() if v >= 3.0}
    lista = []
    for p, v in v_validos.items():
        for i in range(1, esc + 1): lista.append({'p': p, 'c': v / i})
    df_c = pd.DataFrame(lista).sort_values('c', ascending=False)
    return df_c.head(esc)['p'].value_counts().to_dict()

PALETA = {
    'PP': '#1E4B8F', 'PSOE': '#E30613', 'VOX': '#63BE21', 'SUMAR': '#E53187',
    'PODEMOS': '#612D62', 'SALF': '#000000', 'ERC': '#FFB232', 'JUNTS': '#00C3B2',
    'PNV': '#008000', 'BILDU': '#B5CF18', 'BNG': '#ADCFE3', 'CC': '#FFD700', 'UPN': '#10448E'
}

st.sidebar.title("🛠️ Inferencia OSINT")
trigger = st.sidebar.select_slider("Escenario Diplomático", options=['IZQ_TENSE', 'NEUTRAL', 'RUPTURA_USA', 'MAX_CONFLICTO'])

nombres_geo = [f['properties']['name'] for f in geojson_spain['features']] if geojson_spain else []
resultados, total_escanos = [], {}
for p in nombres_geo:
    v = {'PP': 34.0, 'PSOE': 26.0, 'VOX': 16.0, 'SUMAR': 5.0, 'PODEMOS': 4.0, 'SALF': 4.5}
    if p in ['Gipuzkoa', 'Bizkaia', 'Araba']: v.update({'BILDU': 33.5, 'PNV': 25.0, 'PP': 8.5})
    elif p in ['Barcelona', 'Girona', 'Lleida', 'Tarragona']: v.update({'PSOE': 27.5, 'ERC': 17.0, 'JUNTS': 15.5})
    elif p == 'Madrid': v.update({'PP': 43.5, 'PSOE': 21.5, 'SALF': 7.0})
    if trigger == 'MAX_CONFLICTO': v['VOX'] += 6.5; v['SALF'] += 5.5
    elif trigger == 'IZQ_TENSE': v['PSOE'] += 5.0; v['PODEMOS'] += 4.5
    e = 37 if p == 'Madrid' else (32 if p == 'Barcelona' else 4)
    reparto = engine_dhondt(v, e)
    for part, esc in reparto.items(): total_escanos[part] = total_escanos.get(part, 0) + esc
    resultados.append({'Provincia': p, 'Ganador': max(reparto, key=reparto.get) if reparto else 'OTROS'})

# TABS RE-DEFINIDOS
t_map, t_radar, t_analisis, t_doc = st.tabs(["🗺️ Predominancia", "📡 Radar & Impactos", "📊 Escenario Político", "📄 Documentación & Trazabilidad"])

with t_map:
    if geojson_spain:
        fig = px.choropleth(pd.DataFrame(resultados), geojson=geojson_spain, locations='Provincia', featureidkey="properties.name", color='Ganador', color_discrete_map=PALETA, scope="europe")
        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=550)
        st.plotly_chart(fig, use_container_width=True)

with t_radar:
    c1, c2 = st.columns([1.5, 1])
    with c1:
        st.subheader("Radar de Factores Críticos")
        r_v, r_c = [85, 90, 75, 65, 80], ['Vivienda', 'Energía', 'Defensa', 'Territorio', 'Inflación']
        fig_r = go.Figure(go.Scatterpolar(r=r_v+[r_v[0]], theta=r_c+[r_c[0]], fill='toself', line_color='#E30613'))
        fig_r.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False, height=450)
        st.plotly_chart(fig_r, use_container_width=True)
    with c2:
        st.subheader("Listado Flash (30d)")
        hoy = datetime.now()
        for ev in get_osint_events():
            dias = (hoy - datetime.strptime(ev["f"], "%Y-%m-%d")).days
            if dias <= 30: st.error(f"**{ev['e']}** ({dias}d atrás)")

with t_analisis:
    df_pie = pd.DataFrame(list(total_escanos.items()), columns=['Partido', 'Escaños'])
    st.plotly_chart(px.pie(df_pie, values='Escaños', names='Partido', color='Partido', color_discrete_map=PALETA, hole=0.4), use_container_width=True)

with t_doc:
    st.header("🛠️ Trazabilidad y Operaciones")
    st.markdown("### Origen de Datos")
    st.info("Fuente: Histórico Ministerio del Interior + Inferencia OSINT v2026.")
    st.latex(r"C = \frac{V}{S + 1} \quad | \quad E = 1.96 \cdot \sqrt{\frac{p(1-p)}{n}}")
    st.markdown("### Fiabilidad y Certidumbre")
    st.write("Grado de veracidad: Simulación Probabilística basada en el nodo ODROID-C2 (mcasrom).")
    st.divider()
    st.markdown(f"**© 2026 M. Castillo** | [mybloggingnotes@gmail.com](mailto:mybloggingnotes@gmail.com)")
