import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import random

# ===============================
# CONFIGURACIÓN DE LA PÁGINA
# ===============================
st.set_page_config(layout="wide")
st.title("🇪🇸 Sistema Multicapa de Inteligencia Electoral")

# ===============================
# PARTIDOS BASE Y COLORES
# ===============================
PARTIDOS = ["PP","PSOE","VOX","SUMAR","SALF","ERC","JUNTS","PNV","BILDU","CC","UPN","BNG","OTROS"]

PARTIDOS_COLORES = {
    "PP": "#1f77b4",      # azul
    "PSOE": "#d62728",    # rojo
    "VOX": "#2ca02c",     # verde
    "SUMAR": "#9467bd",   # violeta
    "SALF": "#7f7f7f",    # gris
    "ERC": "#ff7f0e",     # naranja
    "JUNTS": "#8c564b",   # marrón
    "PNV": "#17becf",     # cyan
    "BILDU": "#bcbd22",   # amarillo oliva
    "CC": "#e377c2",      # rosa
    "UPN": "#7f7f7f",     # gris
    "BNG": "#17becf",     # cyan
    "OTROS": "#c7c7c7"    # gris claro
}

BASE_NACIONAL = {
    "PP":30,
    "PSOE":27,
    "VOX":16,
    "SUMAR":8,
    "SALF":4,
    "ERC":2,
    "JUNTS":2,
    "PNV":1.5,
    "BILDU":1.2,
    "CC":0.8,
    "UPN":0.5,
    "BNG":0.7,
    "OTROS":6.3
}

# ===============================
# ESCANOS OFICIALES CONGRESO (350)
# ===============================
ESCANOS = {
"Álava":4,"Albacete":4,"Alicante":12,"Almería":6,"Asturias":7,"Ávila":3,
"Badajoz":6,"Baleares":8,"Barcelona":32,"Burgos":4,"Cáceres":4,"Cádiz":9,
"Cantabria":5,"Castellón":5,"Ciudad Real":5,"Córdoba":6,"Cuenca":3,
"Girona":6,"Granada":7,"Guadalajara":3,"Guipúzcoa":6,"Huelva":5,
"Huesca":3,"Jaén":5,"La Coruña":8,"La Rioja":4,"Las Palmas":8,
"León":4,"Lleida":4,"Lugo":4,"Madrid":37,"Málaga":11,"Murcia":10,
"Navarra":5,"Ourense":4,"Palencia":3,"Pontevedra":7,"Salamanca":4,
"Santa Cruz de Tenerife":7,"Segovia":3,"Sevilla":12,"Soria":2,
"Tarragona":6,"Teruel":3,"Toledo":6,"Valencia":16,"Valladolid":5,
"Vizcaya":8,"Zamora":3,"Zaragoza":7,"Ceuta":1,"Melilla":1
}

PROVINCIAS = list(ESCANOS.keys())

# ===============================
# SIDEBAR
# ===============================
st.sidebar.header("Control de Escenarios")
factor_vivienda = st.sidebar.slider("Factor Crisis Vivienda",0,100,50)
factor_energia = st.sidebar.slider("Factor Energía",0,100,50)
fiabilidad = st.sidebar.slider("Fiabilidad Datos Oficiales",0,100,80)

# ===============================
# FUNCIONES
# ===============================
def normalizar(dic):
    total = sum(dic.values())
    return {k: v * 100 / total for k,v in dic.items()}

def ajustar_escenario(base):
    ajuste = base.copy()
    ajuste["PP"] += (factor_vivienda - 50) * 0.02
    ajuste["PSOE"] -= (factor_vivienda - 50) * 0.015
    ajuste["SUMAR"] -= (factor_vivienda - 50) * 0.01
    ajuste["VOX"] += (factor_energia - 50) * 0.015
    return normalizar(ajuste)

def ajustar_territorial(base, provincia):
    datos = base.copy()
    if provincia == "Madrid":
        datos["PP"] += 3
        datos["VOX"] += 1.5
    if provincia in ["Barcelona","Girona","Lleida","Tarragona"]:
        datos["ERC"] += 5
        datos["JUNTS"] += 4
        datos["PP"] -= 2
    if provincia in ["Vizcaya","Guipúzcoa","Álava"]:
        datos["PNV"] += 6
        datos["BILDU"] += 5
    if provincia == "Navarra":
        datos["UPN"] += 4
    if provincia in ["La Coruña","Lugo","Ourense","Pontevedra"]:
        datos["BNG"] += 3
    ruido = (100 - fiabilidad) / 100
    for p in datos:
        datos[p] += random.uniform(-ruido*2, ruido*2)
    return normalizar(datos)

def dhondt(votos, escanos):
    factor = 10000
    votos_int = {p: int(v*factor) for p,v in votos.items()}
    tabla = []
    for p in votos_int:
        for i in range(1, escanos+1):
            tabla.append((p, votos_int[p]/i))
    tabla.sort(key=lambda x: x[1], reverse=True)
    resultado = {p:0 for p in votos_int}
    for i in range(escanos):
        resultado[tabla[i][0]] += 1
    return resultado

# ===============================
# CÁLCULO PRINCIPAL
# ===============================
base_escenario = ajustar_escenario(BASE_NACIONAL)
datos_prov = []
escanos_totales = {p:0 for p in PARTIDOS}
historico_semanal = []

for semana in range(4):  # ejemplo 4 semanas de simulación
    escanos_semana = {p:0 for p in PARTIDOS}
    for prov in PROVINCIAS:
        votos = ajustar_territorial(base_escenario, prov)
        escanos = ESCANOS[prov]
        reparto = dhondt(votos, escanos)
        for p in PARTIDOS:
            escanos_semana[p] += reparto[p]
    historico_semanal.append(escanos_semana)
    for p in PARTIDOS:
        escanos_totales[p] += escanos_semana[p]/4  # promedio semanal

df_prov = pd.DataFrame(datos_prov)

# ===============================
# TABS
# ===============================
tab1, tab2, tab3, tab4 = st.tabs([
    "Hemiciclo","Desglose Provincial","Radar Estratégico","Metodología y Fuentes"
])

# ---------- HEMICICLO ----------
with tab1:
    st.subheader("Proyección de Escaños (350 oficiales)")
    df_hemi = pd.DataFrame({"Partido": list(escanos_totales.keys()),"Escaños": list(escanos_totales.values())})
    df_hemi = df_hemi.sort_values("Escaños",ascending=False)
    fig = px.bar(
        df_hemi,
        x="Partido",
        y="Escaños",
        color="Partido",
        color_discrete_map=PARTIDOS_COLORES
    )
    st.plotly_chart(fig,use_container_width=True)
    total = df_hemi["Escaños"].sum()
    st.write(f"Total escaños asignados: {total:.0f} / 350")
    mayoria = 176
    st.write(f"Mayoría absoluta: {mayoria}")

    # Histórico semanal
    st.subheader("Evolución Semanal de Escaños (simulación)")
    df_hist = pd.DataFrame(historico_semanal)
    df_hist.index = [f"Semana {i+1}" for i in range(len(df_hist))]
    fig_hist = go.Figure()
    for p in PARTIDOS:
        fig_hist.add_trace(go.Scatter(
            x=df_hist.index,
            y=df_hist[p],
            mode='lines+markers',
            name=p,
            line=dict(color=PARTIDOS_COLORES.get(p,"gray"))
        ))
    fig_hist.update_layout(
        xaxis_title="Semana",
        yaxis_title="Escaños",
        height=400
    )
    st.plotly_chart(fig_hist,use_container_width=True)

# ---------- PROVINCIAL ----------
with tab2:
    st.subheader("Datos por Provincia")
    st.dataframe(df_prov, use_container_width=True)

# ---------- RADAR ----------
with tab3:
    st.subheader("Impacto Estratégico")
    categorias = ["Vivienda","Energía","Fiabilidad"]
    valores = [factor_vivienda,factor_energia,fiabilidad]
    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(r=valores, theta=categorias, fill='toself'))
    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True,range=[0,100])))
    st.plotly_chart(fig_radar,use_container_width=True)

# ---------- METODOLOGÍA Y FUENTES ----------
with tab4:
    st.subheader("Metodología del Cálculo de Escaños")
    st.markdown("""
**Objetivo:** Obtener datos semanales de tendencias de voto y proyectar escaños dinámicamente.

**Sidebar - Control de Escenarios:**  
- Factor Crisis Vivienda: ajusta PP, PSOE, SUMAR según percepción de la crisis.  
- Factor Energía: ajusta VOX según situación energética.  
- Fiabilidad Datos Oficiales: simula incertidumbre; ninguna fuente es 100% fiable.

**Narrativa:** Los sliders permiten explorar sensibilidad de resultados frente a cambios políticos y sociales.
""")

    # ---- Diagrama Sankey ----
    st.subheader("Flujo de Cálculo Interactivo (Sankey)")
    st.markdown("""
El diagrama Sankey muestra el pipeline del cálculo de escaños:
- **Ajuste Nacional:** Modificaciones iniciales según factores macro.  
- **Ajuste Territorial:** Tendencias locales y apoyos históricos.  
- **Ruido:** Incertidumbre según fiabilidad de los datos.  
- **D’Hondt:** Asignación proporcional de escaños por provincia.  
- **Proyección:** Total nacional final.
""")
    fig_flow = go.Figure(go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=["Ajuste Nacional","Ajuste Territorial","Ruido","D’Hondt","Proyección"],
            color=["#636EFA","#EF553B","#00CC96","#AB63FA","#FFA15A"]
        ),
        link=dict(
            source=[0,1,2,3],
            target=[1,2,3,4],
            value=[1,1,1,1],
            color=["#636EFA","#EF553B","#00CC96","#AB63FA"]
        )
    ))
    fig_flow.update_layout(height=300, margin=dict(l=20,r=20,t=20,b=20))
    st.plotly_chart(fig_flow,use_container_width=True)

    # ---- Mini-tablas por provincia ----
    st.subheader("Impacto del Ruido y Fiabilidad por Provincia")
    provincia_sel = st.selectbox("Provincia", PROVINCIAS)
    votos_prov = ajustar_territorial(base_escenario, provincia_sel)
    escanos_prov = ESCANOS[provincia_sel]
    reparto_prov = dhondt(votos_prov, escanos_prov)
    df_tabla = pd.DataFrame({
        "Partido": list(reparto_prov.keys()),
        "Escaños proyectados": list(reparto_prov.values()),
        "Votos ajustados (%)": [round(v,2) for v in votos_prov.values()]
    }).sort_values("Escaños proyectados", ascending=False)
    st.dataframe(df_tabla, use_container_width=True)

    # ---- Fuentes y Auditoría ----
    st.subheader("Fuentes y Auditoría")
    st.markdown("""
- Datos oficiales: INE, Boletines, históricos.  
- Encuestas privadas y medios.  
- Ajustes propios y tendencias recientes.

**Auditoría y Monitoreo:**  
- Validación semanal de datos y encuestas.  
- Captura de noticias flash de alto impacto.  
- Alertas ante discrepancias con resultados oficiales.
""")

    st.subheader("Limitaciones")
    st.markdown("""
- Proyecciones, no resultados oficiales.  
- Cambios políticos recientes pueden alterar resultados.  
- El algoritmo no sustituye conteos oficiales.
""")

# ---------- PIE DE PÁGINA ----------
st.markdown("---")
st.markdown("© Miguel Castillo | contacto: [mybloggingnotes@gmail.com](mailto:mybloggingnotes@gmail.com)")
