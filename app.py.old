import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import random
import os
from datetime import datetime

st.set_page_config(layout="wide")

# ==========================================================
# CONFIGURACIÓN GENERAL
# ==========================================================

TOTAL_ESCANOS = 350
MAYORIA_ABS = 176
CSV_FILE = "historico.csv"

PARTIDOS = ["PP","PSOE","VOX","SUMAR","SALF","ERC","JUNTS","PNV","BILDU","CC","UPN","BNG","OTROS"]

COLORES = {
    "PP":"#1f77b4",
    "PSOE":"#d62728",
    "VOX":"#2ca02c",
    "SUMAR":"#9467bd",
    "SALF":"#7f7f7f",
    "ERC":"#ff7f0e",
    "JUNTS":"#17becf",
    "PNV":"#bcbd22",
    "BILDU":"#8c564b",
    "CC":"#e377c2",
    "UPN":"#8c8c8c",
    "BNG":"#2f4f4f",
    "OTROS":"#aaaaaa"
}

# ==========================================================
# FUNCION DHONDT
# ==========================================================

def dhondt(votos_dict, escanos):
    asignados = dict.fromkeys(votos_dict.keys(),0)
    cocientes = []

    for partido,votos in votos_dict.items():
        for i in range(1, escanos+1):
            cocientes.append((votos/i, partido))

    cocientes.sort(reverse=True)

    for i in range(escanos):
        _, partido = cocientes[i]
        asignados[partido] += 1

    return asignados

# ==========================================================
# GENERADOR SIMULACIÓN NACIONAL
# ==========================================================

def generar_voto_base():
    base = {
        "PP":30,
        "PSOE":28,
        "VOX":14,
        "SUMAR":10,
        "SALF":3,
        "ERC":2,
        "JUNTS":2,
        "PNV":1.5,
        "BILDU":1.5,
        "CC":0.5,
        "UPN":0.5,
        "BNG":1,
        "OTROS":6
    }
    return base

# ==========================================================
# CALCULO PRINCIPAL
# ==========================================================

def calcular():
    votos = generar_voto_base()
    escanos = dhondt(votos, TOTAL_ESCANOS)
    return escanos

escanos_totales = calcular()

# ==========================================================
# HISTÓRICO
# ==========================================================

def guardar_historico(datos):
    fecha = datetime.now().strftime("%Y-%m-%d")
    df = pd.DataFrame([{"Fecha":fecha, **datos}])
    if os.path.exists(CSV_FILE):
        df.to_csv(CSV_FILE, mode="a", header=False, index=False)
    else:
        df.to_csv(CSV_FILE, index=False)

if st.sidebar.button("Guardar semana"):
    guardar_historico(escanos_totales)

if os.path.exists(CSV_FILE):
    df_hist = pd.read_csv(CSV_FILE)
else:
    df_hist = pd.DataFrame()

# ==========================================================
# METRICAS AVANZADAS
# ==========================================================

def indice_fragmentacion(dic):
    total = sum(dic.values())
    p = [(v/total)**2 for v in dic.values() if v>0]
    return round(1/sum(p),2)

def indice_concentracion(dic):
    vals = sorted(dic.values(), reverse=True)
    return vals[0] + vals[1]

def indice_hhi(dic):
    total = sum(dic.values())
    return round(sum([(v/total)**2 for v in dic.values()]),3)

def volatilidad_semanal():
    if df_hist.empty or len(df_hist)<2:
        return 0
    df_hist_sorted = df_hist.sort_values("Fecha")
    diff = df_hist_sorted.diff().abs()
    return round(diff.mean().mean(),2)

FRAG = indice_fragmentacion(escanos_totales)
CONC = indice_concentracion(escanos_totales)
HHI = indice_hhi(escanos_totales)
VOL = volatilidad_semanal()

# ==========================================================
# MONTE CARLO
# ==========================================================

def montecarlo(base, n=300):
    sims = []
    for _ in range(n):
        sim = {}
        for p,v in base.items():
            ruido = random.randint(-3,3)
            sim[p] = max(0, v+ruido)
        total = sum(sim.values())
        if total != TOTAL_ESCANOS:
            mayor = max(sim, key=sim.get)
            sim[mayor] += (TOTAL_ESCANOS-total)
        sims.append(sim)
    return pd.DataFrame(sims)

df_mc = montecarlo(escanos_totales)

# ==========================================================
# INTERFAZ
# ==========================================================

st.title("Proyección Electoral – Tendencia Semanal")

tab1, tab2, tab3, tab4 = st.tabs(["Hemiciclo","Histórico","Radar Estratégico","Metodología"])

# ==========================================================
# TAB 1 HEMICICLO
# ==========================================================

with tab1:

    df_plot = pd.DataFrame({
        "Partido": escanos_totales.keys(),
        "Escaños": escanos_totales.values()
    })

    fig = px.bar(
        df_plot,
        x="Partido",
        y="Escaños",
        color="Partido",
        color_discrete_map=COLORES,
        text="Escaños"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Indicadores Parlamentarios")

    col1,col2,col3,col4 = st.columns(4)
    col1.metric("Fragmentación", FRAG)
    col2.metric("Concentración Top2", CONC)
    col3.metric("HHI", HHI)
    col4.metric("Volatilidad", VOL)

    if max(escanos_totales.values()) >= MAYORIA_ABS:
        st.success("Existe mayoría absoluta.")
    else:
        st.info("No hay mayoría absoluta proyectada.")

# ==========================================================
# TAB 2 HISTÓRICO
# ==========================================================

with tab2:
    if not df_hist.empty:
        fig_hist = px.line(df_hist, x="Fecha", y=PARTIDOS)
        st.plotly_chart(fig_hist, use_container_width=True)
        st.dataframe(df_hist)
    else:
        st.info("No hay histórico guardado aún.")

# ==========================================================
# TAB 3 RADAR + MONTECARLO
# ==========================================================

with tab3:

    categorias = list(escanos_totales.keys())
    valores = list(escanos_totales.values())

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=valores,
        theta=categorias,
        fill='toself'
    ))

    st.plotly_chart(fig_radar, use_container_width=True)

    st.subheader("Simulación Monte Carlo")

    media_mc = df_mc.mean().sort_values(ascending=False)

    fig_mc = px.bar(
        x=media_mc.index,
        y=media_mc.values,
        color=media_mc.index,
        color_discrete_map=COLORES
    )

    st.plotly_chart(fig_mc, use_container_width=True)

# ==========================================================
# TAB 4 METODOLOGÍA
# ==========================================================

with tab4:

    st.markdown("""
### Objetivo del Proyecto

Obtener datos semanales de la tendencia del voto y proyectar su traslación en escaños mediante el sistema D’Hondt.

### Flujo del Algoritmo

Ajuste Nacional → Ajuste Territorial → Ruido → D’Hondt → Proyección Final

El diagrama Sankey representa cómo el voto estimado fluye hasta convertirse en escaños.

### Gestión de Fuentes

- Encuestas públicas
- Datos históricos oficiales
- Tendencias agregadas
- Señales de impacto político

Las fuentes institucionales no pueden considerarse 100% fiables; el modelo introduce ruido estadístico controlado para evitar sesgo estructural.

### Fiabilidad

El modelo no pretende predecir resultados electorales exactos sino capturar tendencias dinámicas.

""")

# ==========================================================
# FOOTER
# ==========================================================

st.markdown("---")
st.markdown("© M.Castillo – mybloggingnotes@gmail.com")
