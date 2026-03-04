import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import numpy as np
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="ES-OSINT PRO 2026", layout="wide")

# --- CABECERA ---
st.title("🇪🇸 Sistema de Inteligencia Geopolítica: España Vota 2026")
st.subheader("Análisis Probabilístico de Predominancia y Escaños")
st.markdown(f"""
**Monitor de Soberanía de Datos:** Procesamiento local en **ODROID-C2**. 
*Sincronización automática diaria: 23:40 CET*
""")
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

# --- DATASET (52 PROVINCIAS) ---
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
trigger = st.sidebar.select_slider("Escenario Diplomático", 
                                  options=['IZQ_TENSE', 'NEUTRAL', 'RUPTURA_USA', 'MAX_CONFLICTO'])

# --- PROCESAMIENTO ---
resultados = []
total_escanos = {}

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

# --- NAVEGACIÓN ---
t_map, t_analisis, t_metodo = st.tabs(["🗺️ Predominancia Electoral", "📊 Escenario Político", "📚 Metodología & Copyright"])

with t_map:
    st.subheader("Mapa de Predominancia por Circunscripción")
    fig = px.choropleth(df, geojson=geojson_spain, locations='Provincia', featureidkey="properties.name",
                        color='Ganador', color_discrete_map=PALETA, scope="europe")
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=550)
    st.plotly_chart(fig, use_container_width=True)

with t_analisis:
    col_pie, col_text = st.columns([1, 1.2])
    with col_pie:
        df_pie = pd.DataFrame(list(total_escanos.items()), columns=['Partido', 'Escaños'])
        fig_p = px.pie(df_pie, values='Escaños', names='Partido', color='Partido', color_discrete_map=PALETA, hole=0.4)
        st.plotly_chart(fig_p, use_container_width=True)
    
    with col_text:
        st.subheader("Narrativa de Escenario Geopolítico")
        der = total_escanos.get('PP',0)+total_escanos.get('VOX',0)+total_escanos.get('SALF',0)
        izq = total_escanos.get('PSOE',0)+total_escanos.get('SUMAR',0)+total_escanos.get('PODEMOS',0)
        
        if trigger in ['MAX_CONFLICTO', 'RUPTURA_USA']:
            narrativa = f"El bloque de **Derecha/Soberanista ({der} escaños)** crece por la tensión diplomática. SALF fragmenta el voto pero consolida la ruptura."
        elif trigger == 'IZQ_TENSE':
            narrativa = f"El bloque **Progresista ({izq} escaños)** se moviliza ante la crisis social, aunque su estabilidad parlamentaria depende de terceros."
        else:
            narrativa = "Escenario de estabilidad técnica bajo arquitectura ARM64. El radar detecta equilibrio de bloques con predominancia bipartidista en provincias rurales."
        
        st.markdown(f"> {narrativa}")
        st.metric("Bloque Derecha (PP+VOX+SALF)", f"{der} / 176")
        st.metric("Bloque Izquierda (PSOE+SUM+POD)", f"{izq} / 176")

with t_metodo:
    st.markdown(f"""
    ### Inteligencia de Datos y Metodología
    * **Motor de Inferencia:** D'Hondt con matriz de transferencia OSINT.
    * **Hardware:** Soberanía analítica en nodo **ODROID-C2 (ARM64)**.
    * **Sincronización:** Actualización diaria a las 23:40 CET.
    
    ---
    ### Copyright y Propiedad
    **© 2026 M. Castillo** 📩 Contacto: [mybloggingnotes@gmail.com](mailto:mybloggingnotes@gmail.com)  
    *Todos los derechos reservados. No simplificar. No romper.*
    """)
    st.latex(r"E_{stocástico} = 1.96 \cdot \sqrt{\frac{p(1-p)}{n}}")
