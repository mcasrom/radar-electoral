import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import datetime, timedelta

# --- CONFIGURACIÓN DE SISTEMA ---
st.set_page_config(page_title="ES-OSINT PRO 2026", layout="wide")

# --- DATASET DE IMPACTOS OSINT (Últimos 30 días) ---
impactos_recientes = [
    {"fecha": "2026-02-15", "evento": "Inestabilidad Precios Energía", "impacto": "Alto"},
    {"fecha": "2026-02-28", "evento": "Crisis Acceso Vivienda Joven", "impacto": "Crítico"},
    {"fecha": "2026-03-03", "evento": "Tensión Territorial: Financiación", "impacto": "Medio"},
]

# --- CABECERA ---
st.title("🇪🇸 Sistema de Inteligencia Geopolítica: España Vota 2026")
st.subheader("Análisis Probabilístico y Monitor de Factores Críticos")
st.markdown(f"**Soberanía de Datos:** Nodo **ODROID-C2**. Sincronización: 23:40 CET")
st.divider()

# --- CARGA GEOJSON ---
@st.cache_data
def load_map():
    with open('data/provincias.json') as f:
        return json.load(f)
geojson_spain = load_map()

# --- MOTOR D'HONDT ---
def engine_dhondt(votos, esc):
    if not votos or esc == 0: return {}
    v_validos = {p: v for p, v in votos.items() if v >= 3.0}
    if not v_validos: return {}
    lista = []
    for p, v in v_validos.items():
        for i in range(1, esc + 1):
            lista.append({'p': p, 'c': v / i})
    df_c = pd.DataFrame(lista).sort_values('c', ascending=False)
    return df_c.head(esc)['p'].value_counts().to_dict()

# --- PALETA ---
PALETA = {
    'PP': '#1E4B8F', 'PSOE': '#E30613', 'VOX': '#63BE21', 'SUMAR': '#E53187',
    'PODEMOS': '#612D62', 'SALF': '#000000', 'ERC': '#FFB232', 'JUNTS': '#00C3B2',
    'PNV': '#008000', 'BILDU': '#B5CF18', 'BNG': '#ADCFE3', 'CC': '#FFD700', 'UPN': '#10448E'
}

# --- DATASET BASE ---
nombres_geo = [f['properties']['name'] for f in geojson_spain['features']]
datos_base = {}
for p in nombres_geo:
    votos_p = {'PP': 34.0, 'PSOE': 26.0, 'VOX': 16.0, 'SUMAR': 5.0, 'PODEMOS': 4.0, 'SALF': 4.5}
    if p in ['Gipuzkoa', 'Bizkaia', 'Araba']:
        votos_p.update({'BILDU': 33.5, 'PNV': 25.0, 'PP': 8.5, 'PSOE': 13.5})
    elif p in ['Barcelona', 'Girona', 'Lleida', 'Tarragona']:
        votos_p.update({'PSOE': 27.5, 'ERC': 17.0, 'JUNTS': 15.5, 'PP': 10.5, 'SUMAR': 10.0})
    elif p in ['A Coruña', 'Pontevedra']:
        votos_p.update({'PP': 45.0, 'BNG': 19.5, 'PSOE': 21.0})
    elif p == 'Madrid':
        votos_p.update({'PP': 43.5, 'PSOE': 21.5, 'VOX': 14.5, 'SALF': 7.0})
    e = 37 if p == 'Madrid' else (32 if p == 'Barcelona' else (12 if p in ['Sevilla', 'Valencia'] else 4))
    datos_base[p] = {'e': e, 'v': votos_p}

# --- SIDEBAR ---
st.sidebar.title("🛠️ Inferencia OSINT")
trigger = st.sidebar.select_slider("Escenario Diplomático", options=['IZQ_TENSE', 'NEUTRAL', 'RUPTURA_USA', 'MAX_CONFLICTO'])

# --- PROCESAMIENTO ---
resultados, total_escanos = [], {}
for p, info in datos_base.items():
    v = info['v'].copy()
    if trigger == 'MAX_CONFLICTO':
        v['VOX'] += 6.5; v['SALF'] += 5.5; v['PP'] -= 3.5
    elif trigger == 'RUPTURA_USA':
        v['PSOE'] = max(0, v.get('PSOE', 0) - 5.5); v['VOX'] += 4.5; v['PP'] += 3.0
    elif trigger == 'IZQ_TENSE':
        v['PSOE'] += 5.0; v['PODEMOS'] += 4.5; v['PP'] -= 4.0
    reparto = engine_dhondt(v, info['e'])
    ganador = max(reparto, key=reparto.get) if reparto else 'OTROS'
    for part, esc in reparto.items():
        total_escanos[part] = total_escanos.get(part, 0) + esc
    resultados.append({'Provincia': p, 'Ganador': ganador, 'Escaños': info['e']})
df = pd.DataFrame(resultados)

# --- INTERFAZ (TABS) ---
t_map, t_radar, t_analisis, t_metodo = st.tabs(["🗺️ Predominancia", "📡 Radar & Impactos", "📊 Escenario Político", "📚 Metodología"])

with t_map:
    st.subheader("Mapa de Predominancia")
    fig = px.choropleth(df, geojson=geojson_spain, locations='Provincia', featureidkey="properties.name", color='Ganador', color_discrete_map=PALETA, scope="europe")
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=550)
    st.plotly_chart(fig, use_container_width=True)

with t_radar:
    col_rad, col_feed = st.columns([1.5, 1])
    with col_rad:
        st.subheader("Radar de Factores Críticos")
        r_v, r_c = [85, 90, 75, 65, 80], ['Vivienda', 'Energía', 'Defensa', 'Territorio', 'Inflación']
        fig_r = go.Figure(go.Scatterpolar(r=r_v+[r_v[0]], theta=r_c+[r_c[0]], fill='toself', line_color='#E30613'))
        fig_r.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False, height=450)
        st.plotly_chart(fig_r, use_container_width=True)
    
    with col_feed:
        st.subheader("Eventos Recientes (OSINT)")
        hoy = datetime.now()
        for item in impactos_recientes:
            fecha_dt = datetime.strptime(item["fecha"], "%Y-%m-%d")
            dias = (hoy - fecha_dt).days
            if dias <= 30:
                st.error(f"**{item['evento']}** \nImpacto: {item['impacto']} ({dias} días atrás)")
            else:
                st.write(f"~~{item['evento']}~~ (Expirado)")

with t_analisis:
    col_p, col_t = st.columns([1, 1.2])
    with col_p:
        df_pie = pd.DataFrame(list(total_escanos.items()), columns=['Partido', 'Escaños'])
        st.plotly_chart(px.pie(df_pie, values='Escaños', names='Partido', color='Partido', color_discrete_map=PALETA, hole=0.4), use_container_width=True)
    with col_t:
        der = total_escanos.get('PP',0)+total_escanos.get('VOX',0)+total_escanos.get('SALF',0)
        izq = total_escanos.get('PSOE',0)+total_escanos.get('SUMAR',0)+total_escanos.get('PODEMOS',0)
        st.metric("Bloque Derecha", f"{der} / 176")
        st.metric("Bloque Izquierda", f"{izq} / 176")

with t_metodo:
    st.markdown(f"**© 2026 M. Castillo** | [mybloggingnotes@gmail.com](mailto:mybloggingnotes@gmail.com)")
    st.latex(r"E_{stocástico} = 1.96 \cdot \sqrt{\frac{p(1-p)}{n}}")
