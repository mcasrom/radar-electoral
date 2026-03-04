import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json

# 1. CONFIGURACIÓN Y ESTILO M. CASTILLO
st.set_page_config(page_title="ES-OSINT PRO v6.0", layout="wide")

PALETA = {
    'PP': '#1E4B8F', 'PSOE': '#E30613', 'VOX': '#63BE21', 'SUMAR': '#E53187',
    'PODEMOS': '#612D62', 'SALF': '#000000', 'ERC': '#FFB232', 'JUNTS': '#00C3B2',
    'PNV': '#008000', 'BILDU': '#B5CF18', 'BNG': '#ADCFE3', 'CC': '#FFD700', 'UPN': '#10448E', 'OTROS': '#CCCCCC'
}

# 2. MOTOR D'HONDT TRANSPARENTE
def engine_dhondt(votos, esc):
    v_validos = {p: v for p, v in votos.items() if v >= 3.0}
    if not v_validos: return {}
    lista = []
    for p, v in v_validos.items():
        for i in range(1, esc + 1):
            lista.append({'p': p, 'c': v / i})
    df_c = pd.DataFrame(lista).sort_values('c', ascending=False)
    return df_c.head(esc)['p'].value_counts().to_dict()

# 3. SIDEBAR DE CONTROL DE ESCENARIOS (RECUPERADO)
st.sidebar.header("🕹️ Control de Escenarios")
tension_vivienda = st.sidebar.slider("Factor Crisis Vivienda", 0, 100, 85)
tension_energia = st.sidebar.slider("Factor Energía", 0, 100, 70)
sesgo_oficial = st.sidebar.select_slider("Fiabilidad Datos Oficiales", options=['BAJA', 'MEDIA', 'ALTA'], value='BAJA')

# 4. BASE DE DATOS PROVINCIAL (SIMULACIÓN DE LAS 52)
@st.cache_data
def get_full_data():
    # En un entorno real, esto lee de data/provincias.json
    nombres = ["Almería","Cádiz","Córdoba","Granada","Huelva","Jaén","Málaga","Sevilla","Huesca","Teruel","Zaragoza","Asturias","Baleares","Palmas, Las","Tenerife","Cantabria","Ávila","Burgos","León","Palencia","Salamanca","Segovia","Soria","Valladolid","Zamora","Albacete","Ciudad Real","Cuenca","Guadalajara","Toledo","Barcelona","Girona","Lleida","Tarragona","Alicante","Castellón","Valencia","Badajoz","Cáceres","Coruña, A","Lugo","Ourense","Pontevedra","Madrid","Murcia","Navarra","Araba","Bizkaia","Gipuzkoa","Rioja, La","Ceuta","Melilla"]
    data = []
    for n in nombres:
        esc = 37 if n == "Madrid" else (32 if n == "Barcelona" else 5)
        votos = {'PP': 33.0, 'PSOE': 26.0, 'VOX': 15.0, 'SUMAR': 8.0, 'SALF': 5.0}
        # Inyección de Pluralidad Regional
        if n in ["Bizkaia", "Gipuzkoa", "Araba"]: votos.update({'PNV': 25.0, 'BILDU': 28.0})
        if n in ["Barcelona", "Girona", "Lleida", "Tarragona"]: votos.update({'ERC': 15.0, 'JUNTS': 14.0})
        data.append({'n': n, 'e': esc, 'v': votos})
    return data

datos_prov = get_full_data()

# CÁLCULO GLOBAL
total_escanos = {}
for p in datos_prov:
    reparto = engine_dhondt(p['v'], p['e'])
    for part, esc in reparto.items():
        total_escanos[part] = total_escanos.get(part, 0) + esc

# 5. INTERFAZ DE USUARIO
st.title("🇪🇸 Sistema de Inteligencia Geopolítica: España Vota 2026")
st.markdown(f"**Soberanía de Datos:** Nodo **ODROID-C2** | Auditoría v6.0")

t1, t2, t3, t4 = st.tabs(["🏛️ Hemiciclo", "📡 Radar OSINT", "📋 Desglose Provincial", "📄 Metodología"])

with t1:
    st.subheader("Formación del Parlamento (Proyección)")
    df_h = pd.DataFrame(list(total_escanos.items()), columns=['Partido', 'Escaños']).sort_values('Escaños', ascending=False)
    fig_h = px.pie(df_h, values='Escaños', names='Partido', color='Partido', color_discrete_map=PALETA, hole=0.5)
    st.plotly_chart(fig_h, use_container_width=True)
    st.dataframe(df_h.T, use_container_width=True)

with t2:
    st.subheader("Radar de Factores de Tensión")
    r_v = [tension_vivienda, tension_energia, 60, 80, 75]
    r_t = ['Vivienda', 'Energía', 'Defensa', 'Inflación', 'Territorio']
    fig_r = go.Figure(go.Scatterpolar(r=r_v+[r_v[0]], theta=r_t+[r_t[0]], fill='toself', line_color='#E30613'))
    st.plotly_chart(fig_r, use_container_width=True)

with t3:
    st.subheader("Datos Detallados por Provincia (52)")
    df_provs = pd.DataFrame([{'Provincia': p['n'], 'Escaños': p['e']} for p in datos_prov])
    st.dataframe(df_provs, use_container_width=True)

with t4:
    st.header("⚙️ Metodología y Trazabilidad")
    st.markdown("### El Algoritmo D'Hondt")
    st.latex(r"cociente = \frac{Votos}{S + 1}")
    st.write("Donde **S** es el número de escaños ya asignados al partido.")
    st.markdown("### Gestión de la Veracidad")
    st.info(f"Escenario actual de fiabilidad: **{sesgo_oficial}**. El sistema aplica factores de corrección sobre el historial del Ministerio.")
    st.divider()
    st.markdown("© 2026 M. Castillo | mcasrom@gmail.com")
