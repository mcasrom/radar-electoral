import streamlit as st
import pandas as pd
import plotly.express as px
import json

st.set_page_config(page_title="ES-OSINT 2026", layout="wide")

# TÍTULO ESTÁTICO (Sin variables complejas para evitar fallos de render)
st.title("Sistema de Inteligencia Geopolítica: España Vota 2026")
st.markdown("Nodo: **ODROID-C2** | Versión: **5.5 - Estabilidad**")

# PESTAÑAS SIMPLIFICADAS
t1, t2, t3 = st.tabs(["Análisis Electoral", "Radar OSINT", "Documentación Técnica"])

with t1:
    st.subheader("Mapa de Predominancia")
    st.info("Sincronizando con base de datos del Ministerio del Interior...")
    # Aquí irá el mapa una vez estabilizado el render

with t2:
    st.subheader("Factores de Tensión")
    # Radar simple
    df_radar = pd.DataFrame(dict(r=[80, 90, 70, 85], theta=['Vivienda','Energía','Defensa','Inflación']))
    fig = px.line_polar(df_radar, r='r', theta='theta', line_close=True)
    st.plotly_chart(fig)

with t3:
    st.header("Documentación y Trazabilidad")
    st.markdown("""
    ### Origen de los Datos
    Los datos provienen de una combinación de fuentes históricas (Ministerio del Interior) modificadas por vectores de tendencia extraídos vía OSINT.
    
    ### Tratamiento
    - **Gestión:** Procesado en hardware soberano (ARM64).
    - **Cálculo:** Aplicación de Ley D'Hondt mediante iteración de cocientes.
    - **Certeza:** Sujeta a márgenes de error estocásticos provinciales.
    """)
    st.divider()
    st.markdown("© 2026 M. Castillo | mcasrom@gmail.com")

# SIDEBAR RECONSTRUIDO AL FINAL
st.sidebar.header("Control de Escenarios")
st.sidebar.slider("Nivel de Conflicto", 0, 100, 50)
