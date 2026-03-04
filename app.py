import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json

st.set_page_config(page_title="ES-OSINT PRO v5.8", layout="wide")

# --- PALETA DE COLORES (Soberanía de Identidad) ---
PALETA = {
    'PP': '#1E4B8F', 'PSOE': '#E30613', 'VOX': '#63BE21', 'SUMAR': '#E53187',
    'PODEMOS': '#612D62', 'SALF': '#000000', 'ERC': '#FFB232', 'JUNTS': '#00C3B2',
    'PNV': '#008000', 'BILDU': '#B5CF18', 'BNG': '#ADCFE3', 'OTROS': '#CCCCCC'
}

# --- MOTOR D'HONDT Y CÁLCULO ---
def engine_dhondt(votos, esc):
    v_validos = {p: v for p, v in votos.items() if v >= 3.0}
    lista = []
    for p, v in v_validos.items():
        for i in range(1, esc + 1):
            lista.append({'p': p, 'c': v / i})
    df_c = pd.DataFrame(lista).sort_values('c', ascending=False)
    return df_c.head(esc)['p'].value_counts().to_dict()

# --- DATOS BASE (Simplificados para estabilidad) ---
provincias_data = [
    {'n': 'Madrid', 'e': 37, 'v': {'PP': 40.5, 'PSOE': 24.0, 'VOX': 15.0, 'SALF': 7.0, 'SUMAR': 8.0}},
    {'n': 'Barcelona', 'e': 32, 'v': {'PSOE': 28.0, 'ERC': 16.0, 'JUNTS': 15.0, 'PP': 12.0, 'SUMAR': 11.0}},
    {'n': 'Bizkaia', 'e': 8, 'v': {'PNV': 30.0, 'BILDU': 28.0, 'PSOE': 18.0, 'PP': 10.0}}
]

# --- PROCESAMIENTO ---
reparto_total = {}
for prov in provincias_data:
    res = engine_dhondt(prov['v'], prov['e'])
    for k, v in res.items():
        reparto_total[k] = reparto_total.get(k, 0) + v

# --- INTERFAZ ---
st.title("🇪🇸 Sistema de Inteligencia: España Vota 2026")
st.markdown(f"**Soberanía de Datos:** Nodo **ODROID-C2** | v5.8 (Restauración de Sistemas)")

t_parlamento, t_provincias, t_radar, t_doc = st.tabs(["🏛️ Formación Parlamento", "📋 Desglose Provincial", "📡 Radar OSINT", "📄 Trazabilidad"])

with t_parlamento:
    st.subheader("Hemiciclo de la Nación (Reparto Proyectado)")
    df_parl = pd.DataFrame(list(reparto_total.items()), columns=['Partido', 'Escaños']).sort_values('Escaños', ascending=False)
    fig_pie = px.pie(df_parl, values='Escaños', names='Partido', color='Partido', 
                     color_discrete_map=PALETA, hole=0.5)
    st.plotly_chart(fig_pie, use_container_width=True)
    st.table(df_parl.T)

with t_provincias:
    st.subheader("Tablas de Opciones por Circunscripción")
    for prov in provincias_data:
        with st.expander(f"Detalle: {prov['n']}"):
            st.write(f"Escaños en juego: {prov['e']}")
            st.json(prov['v'])

with t_radar:
    st.subheader("Radar de Factores Críticos")
    r_v, r_c = [92, 85, 60, 88, 75], ['Vivienda', 'Energía', 'Defensa', 'Inflación', 'Territorio']
    fig_r = go.Figure(go.Scatterpolar(r=r_v+[r_v[0]], theta=r_c+[r_c[0]], fill='toself', line_color='#E30613'))
    st.plotly_chart(fig_r, use_container_width=True)

with t_doc:
    st.header("🛠️ Trazabilidad")
    st.latex(r"C = \frac{V}{S + 1}")
    st.markdown("© 2026 M. Castillo | mcasrom@gmail.com")
