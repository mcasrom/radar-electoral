#!/usr/bin/env python3
# app.py — España Vota 2026 — Sistema Multicapa de Inteligencia Electoral
# Autor: Miguel Castillo Romero
# Fecha: 2026

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os

# 1️⃣ CONFIGURACIÓN STREAMLIT
st.set_page_config(page_title="España Vota 2026", layout="wide")
st.title("🇪🇸 Sistema Multicapa de Inteligencia Electoral")
st.markdown("**Nodo:** ODROID-C2 | Auditoría v1.0 | Autor: M. Castillo")

# Paleta de colores por partido
PALETA = {
    'PP': '#1E4B8F', 'PSOE': '#E30613', 'VOX': '#63BE21', 'SUMAR': '#E53187',
    'PODEMOS': '#612D62', 'SALF': '#000000', 'ERC': '#FFB232', 'JUNTS': '#00C3B2',
    'PNV': '#008000', 'BILDU': '#B5CF18', 'BNG': '#ADCFE3', 'CC': '#FFD700', 'UPN': '#10448E', 'OTROS': '#CCCCCC'
}

# 2️⃣ SIDEBAR DE CONTROL
st.sidebar.header("🕹️ Control de Escenarios")
tension_vivienda = st.sidebar.slider("Factor Crisis Vivienda", 0, 100, 85)
tension_energia = st.sidebar.slider("Factor Energía", 0, 100, 70)
sesgo_oficial = st.sidebar.select_slider("Fiabilidad Datos Oficiales", options=['BAJA','MEDIA','ALTA'], value='BAJA')

# 3️⃣ FUNCIONES
def engine_dhondt(votos, esc):
    """Cálculo de escaños con D'Hondt, solo votos >= 3%"""
    v_validos = {p: v for p, v in votos.items() if v >= 3.0}
    if not v_validos:
        return {}
    lista = []
    for p, v in v_validos.items():
        for i in range(1, esc+1):
            lista.append({'p': p, 'c': v / i})
    df_c = pd.DataFrame(lista).sort_values('c', ascending=False)
    return df_c.head(esc)['p'].value_counts().to_dict()

# 4️⃣ CARGA DE DATOS
DATA_FILE = os.path.join("data","votos_historicos.csv")
if not os.path.exists(DATA_FILE):
    st.error(f"No se encuentra {DATA_FILE}. Ejecuta update_data.py primero.")
    st.stop()

df_historico = pd.read_csv(DATA_FILE, parse_dates=["fecha"])
df_long = df_historico.copy()  # CSV ya está en long format

# 5️⃣ CÁLCULO DE ESCAÑOS POR PROVINCIA (simulado)
# Ejemplo simplificado: 52 provincias con 5-37 escaños
PROVINCIAS = ["Madrid","Barcelona"] + [f"Provincia {i}" for i in range(1,51)]
datos_prov = []
for n in PROVINCIAS:
    esc = 37 if n=="Madrid" else (32 if n=="Barcelona" else 5)
    # Tomamos últimos votos promedio ponderado
    votos = df_long[df_long['fecha']==df_long['fecha'].max()].groupby('partido').apply(
        lambda x: np.average(x['voto'], weights=x['fiabilidad'])
    ).to_dict()
    datos_prov.append({'n':n,'e':esc,'v':votos})

# Total escaños nacionales
total_escanos = {}
for p in datos_prov:
    reparto = engine_dhondt(p['v'], p['e'])
    for part, esc in reparto.items():
        total_escanos[part] = total_escanos.get(part,0)+esc

# 6️⃣ INTERFAZ DE USUARIO — TABS
t1, t2, t3, t4 = st.tabs(["🏛️ Hemiciclo","📡 Radar OSINT","📋 Desglose Provincial","📄 Metodología"])

# TAB 1 — Hemiciclo
with t1:
    st.subheader("Formación del Parlamento (Proyección)")
    df_h = pd.DataFrame(list(total_escanos.items()), columns=['Partido','Escaños']).sort_values('Escaños', ascending=False)
    fig_h = px.pie(df_h, values='Escaños', names='Partido', color='Partido', color_discrete_map=PALETA, hole=0.5)
    st.plotly_chart(fig_h, use_container_width=True)
    st.dataframe(df_h.T, use_container_width=True)

# TAB 2 — Radar de factores
with t2:
    st.subheader("Radar de Factores de Tensión")
    r_v = [tension_vivienda, tension_energia, 60, 80, 75]
    r_t = ['Vivienda','Energía','Defensa','Inflación','Territorio']
    fig_r = go.Figure(go.Scatterpolar(r=r_v+[r_v[0]], theta=r_t+[r_t[0]], fill='toself', line_color='#E30613'))
    st.plotly_chart(fig_r, use_container_width=True)

# TAB 3 — Desglose Provincial
with t3:
    st.subheader("Datos Detallados por Provincia")
    df_provs = pd.DataFrame([{'Provincia': p['n'], 'Escaños': p['e'], **p['v']} for p in datos_prov])
    st.dataframe(df_provs, use_container_width=True)

# TAB 4 — Evolución temporal + metodología
with t4:
    st.header("📊 Evolución Temporal de Intención de Voto")
    # Media ponderada por fiabilidad
    ultimos = df_long.groupby('partido').apply(lambda x: np.average(x['voto'], weights=x['fiabilidad'])).to_dict()
    st.markdown("### Media ponderada actual por partido")
    df_ultimos = pd.DataFrame(list(ultimos.items()), columns=['Partido','Media Ponderada'])
    st.dataframe(df_ultimos)

    # Gráfico temporal
    fig_t = px.line(
        df_long,
        x="fecha",
        y="voto",
        color="partido",
        line_group="partido",
        hover_name="fuente",
        markers=True,
        title="Evolución temporal ponderada por fiabilidad"
    )
    st.plotly_chart(fig_t, use_container_width=True)

    # Metodología
    st.markdown("### Algoritmo D'Hondt")
    st.latex(r"cociente = \frac{Votos}{S + 1}")
    st.write("Donde **S** es el número de escaños ya asignados al partido.")
    st.markdown(f"### Fiabilidad de datos oficiales: **{sesgo_oficial}**")
    st.info("Todos los datos se registran con fecha, fuente y coeficiente de fiabilidad para auditoría.")
    st.divider()
    st.markdown("© 2026 M. Castillo | mcasrom@gmail.com")
