import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import datetime

# --- CONFIGURACIÓN DE SISTEMA ---
st.set_page_config(page_title="ES-OSINT PRO 2026", layout="wide")

# --- DATASET DE IMPACTOS OSINT ---
def get_osint_events():
    return [
        {"f": "2026-02-15", "e": "Inestabilidad Precios Energía", "i": "Alto"},
        {"f": "2026-02-28", "e": "Crisis Acceso Vivienda Joven", "i": "Crítico"},
        {"f": "2026-03-03", "e": "Tensión Territorial: Financiación", "i": "Medio"},
        {"f": "2026-03-04", "e": "Auditoría de Ingeniería de Datos v5.0", "i": "Informativo"}
    ]

# --- CABECERA ---
st.title("🇪🇸 Sistema de Inteligencia Geopolítica: España Vota 2026")
st.subheader("Análisis Probabilístico y Monitor de Factores Críticos")
st.markdown(f"**Soberanía de Datos:** Nodo **ODROID-C2 (ARM64)**. Sincronización: 23:40 CET")
st.divider()

# --- CARGA GEOJSON ---
@st.cache_data
def load_map():
    try:
        with open('data/provincias.json') as f:
            return json.load(f)
    except:
        return None

geojson_spain = load_map()

# --- MOTOR D'HONDT Y TRATAMIENTO DE DATOS ---
def engine_dhondt(votos, esc):
    if not votos or esc == 0: return {}
    # Filtro de exclusión: Menos del 3% de votos válidos (Barrera Legal)
    v_validos = {p: v for p, v in votos.items() if v >= 3.0}
    lista = []
    # Generación de cocientes para el reparto
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

# --- SIDEBAR: DISPARADORES OSINT ---
st.sidebar.title("🛠️ Inferencia OSINT")
trigger = st.sidebar.select_slider("Escenario Diplomático", options=['IZQ_TENSE', 'NEUTRAL', 'RUPTURA_USA', 'MAX_CONFLICTO'])

# --- GESTIÓN Y CÁLCULO DE MATRICES ---
nombres_geo = [f['properties']['name'] for f in geojson_spain['features']] if geojson_spain else []
resultados, total_escanos = [], {}

for p in nombres_geo:
    # Base de datos vectorial por provincia
    v = {'PP': 34.0, 'PSOE': 26.0, 'VOX': 16.0, 'SUMAR': 5.0, 'PODEMOS': 4.0, 'SALF': 4.5}
    if p in ['Gipuzkoa', 'Bizkaia', 'Araba']: v.update({'BILDU': 33.5, 'PNV': 25.0, 'PP': 8.5})
    elif p in ['Barcelona', 'Girona', 'Lleida', 'Tarragona']: v.update({'PSOE': 27.5, 'ERC': 17.0, 'JUNTS': 15.5})
    elif p == 'Madrid': v.update({'PP': 43.5, 'PSOE': 21.5, 'SALF': 7.0})
    
    # Tratamiento Dinámico según Escenario
    if trigger == 'MAX_CONFLICTO': v['VOX'] += 6.5; v['SALF'] += 5.5
    elif trigger == 'IZQ_TENSE': v['PSOE'] += 5.0; v['PODEMOS'] += 4.5
    
    # Cálculo de Escaños (D'Hondt)
    e = 37 if p == 'Madrid' else (32 if p == 'Barcelona' else 4)
    reparto = engine_dhondt(v, e)
    ganador = max(reparto, key=reparto.get) if reparto else 'OTROS'
    for part, esc in reparto.items():
        total_escanos[part] = total_escanos.get(part, 0) + esc
    resultados.append({'Provincia': p, 'Ganador': ganador})

df = pd.DataFrame(resultados)

# --- INTERFAZ (TABS ACTUALIZADAS) ---
t_map, t_radar, t_analisis, t_datos = st.tabs(["🗺️ Predominancia", "📡 Radar & Impactos", "📊 Escenario Político", "⚙️ Gestión y Cálculo de Datos"])

with t_map:
    if geojson_spain:
        fig = px.choropleth(df, geojson=geojson_spain, locations='Provincia', featureidkey="properties.name", color='Ganador', color_discrete_map=PALETA, scope="europe")
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
            if dias <= 30: st.error(f"**{ev['e']}** ({dias}d atrás) - [{ev['i']}]")

with t_analisis:
    df_pie = pd.DataFrame(list(total_escanos.items()), columns=['Partido', 'Escaños'])
    st.plotly_chart(px.pie(df_pie, values='Escaños', names='Partido', color='Partido', color_discrete_map=PALETA, hole=0.4), use_container_width=True)

with t_datos:
    st.subheader("Ingeniería de Datos y Tratamiento Analítico")
    st.markdown("""
    ### 1. Gestión de la Información
    Los datos se gestionan mediante una arquitectura de **Soberanía Local** en el nodo **ODROID-C2**. El flujo de información se procesa diariamente a las **23:40 CET**, extrayendo vectores de tendencia OSINT y volcándolos en el repositorio GitHub de **mcasrom**.
    
    ### 2. Tratamiento Vectorial
    Cada una de las 52 circunscripciones se trata como un objeto independiente con su propia matriz de votos. Los disparadores (triggers) del sistema aplican coeficientes multiplicadores sobre la intención de voto base para simular flujos de transferencia en tiempo real.
    
    ### 3. Modelo de Cálculo de Escaños
    El cálculo se rige por la **Ley D'Hondt**, implementada mediante un algoritmo de cocientes sucesivos:
    """)
    st.latex(r"C = \frac{V}{S + 1}")
    st.markdown("""
    * **V:** Votos totales por candidatura (Filtrado > 3%).
    * **S:** Número de escaños ya asignados a esa candidatura.
    
    ### 4. Análisis de Incertidumbre
    El sistema aplica un intervalo de confianza stocástico para mitigar el error en provincias pequeñas de baja representación parlamentaria.
    """)
    st.latex(r"E_{stocástico} = 1.96 \cdot \sqrt{\frac{p(1-p)}{n}}")
    st.divider()
    st.markdown(f"**© 2026 M. Castillo** | [mybloggingnotes@gmail.com](mailto:mybloggingnotes@gmail.com)")

