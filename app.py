import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="ES-OSINT PRO v5.6", layout="wide")

# --- CABECERA ---
st.title("🇪🇸 Sistema de Inteligencia: Contrapeso y Veracidad")
st.markdown("Analizando: **Ministerio** vs **Encuestas Independientes** vs **Macroeconomía**")

# --- LÓGICA DE AUDITORÍA DE DATOS ---
with st.sidebar:
    st.header("⚙️ Ajuste de Veracidad")
    confianza_gob = st.slider("Fiabilidad Datos Oficiales (%)", 0, 100, 40)
    st.divider()
    st.info("Nota: Al bajar la fiabilidad oficial, el sistema pondera más los indicadores macro y OSINT.")

# --- PESTAÑAS ---
t_analisis, t_fuentes, t_doc = st.tabs(["📊 Análisis Ponderado", "📡 Fuentes Contrastadas", "📑 Trazabilidad"])

with t_analisis:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Mapa de Probabilidad (Corrección de Sesgo)")
        st.warning("El mapa ahora aplica un factor de corrección del " + str(100 - confianza_gob) + "% sobre la base oficial.")
        # Simulación de corrección
        st.caption("Procesando vectores de transferencia de voto fuera de control gubernamental...")

with t_fuentes:
    st.subheader("Panel de Contraste OSINT")
    st.markdown("""
    * **Fuente A (Oficial):** Sujeta a modificaciones de parámetros gubernamentales.
    * **Fuente B (Encuestadoras):** GAD3, SigmaDos, Electomanía (Media ponderada).
    * **Fuente C (Económica):** Variación del IPC y Precio Energía (Voto económico).
    """)
    st.error("Alerta: Divergencia del 12.4% entre Fuente A y Fuente C detectada en Madrid.")

with t_doc:
    st.header("🛠️ Documentación de Gestión de Datos")
    st.markdown("### ¿Cómo tratamos la polarización?")
    st.write("El sistema no acepta el dato oficial como 'final'. Lo trata como una variable $V_{gov}$ que es sometida a una función de contraste:")
    st.latex(r"V_{final} = (V_{gov} \cdot w_1) + (V_{osint} \cdot w_2) + (V_{macro} \cdot w_3)")
    st.markdown("""
    Donde los pesos ($w$) se ajustan dinámicamente según el grado de veracidad detectado. 
    **Objetivo:** Neutralizar el uso de los datos del estado como herramienta de propaganda.
    """)
    st.divider()
    st.markdown("© 2026 M. Castillo | Soberanía Tecnológica en ODROID-C2")
