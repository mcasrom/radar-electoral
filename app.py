import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import random
import os
from datetime import date

# ===============================
# CONFIGURACIÓN DE LA PÁGINA
# ===============================
st.set_page_config(layout="wide")
st.title("🇪🇸 Sistema Multicapa de Inteligencia Electoral - Simulación y Tendencias")

# ===============================
# PARTIDOS BASE Y COLORES
# ===============================
PARTIDOS = ["PP","PSOE","VOX","SUMAR","SALF","ERC","JUNTS","PNV","BILDU","CC","UPN","BNG","OTROS"]

PARTIDOS_COLORES = {
    "PP": "#1f77b4","PSOE": "#d62728","VOX": "#2ca02c","SUMAR": "#9467bd","SALF": "#7f7f7f",
    "ERC": "#ff7f0e","JUNTS": "#8c564b","PNV": "#17becf","BILDU": "#bcbd22","CC": "#e377c2",
    "UPN": "#7f7f7f","BNG": "#17becf","OTROS": "#c7c7c7"
}

BASE_NACIONAL = {
    "PP":30,"PSOE":27,"VOX":16,"SUMAR":8,"SALF":4,
    "ERC":2,"JUNTS":2,"PNV":1.5,"BILDU":1.2,"CC":0.8,
    "UPN":0.5,"BNG":0.7,"OTROS":6.3
}

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

st.sidebar.markdown("""
**Guía rápida:**  
- Ajusta los factores para simular impacto de la crisis vivienda, energía y percepción de fiabilidad.  
- Ninguna fuente oficial es 100% confiable; el slider de fiabilidad simula incertidumbre.  
- El objetivo es obtener **datos semanales de tendencia del voto** y proyectar escaños.  
""")

# ===============================
# HISTÓRICO SEMANAL
# ===============================
HISTORICO_FILE = "historico_semanal.csv"

if not os.path.exists(HISTORICO_FILE):
    df_hist = pd.DataFrame(columns=["Fecha","Provincia","Partido","Votos","Escaños"])
    df_hist.to_csv(HISTORICO_FILE,index=False)
else:
    df_hist = pd.read_csv(HISTORICO_FILE)

# ===============================
# FUNCIONES DE SIMULACIÓN
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
        datos["PP"] += 3; datos["VOX"] += 1.5
    if provincia in ["Barcelona","Girona","Lleida","Tarragona"]:
        datos["ERC"] += 5; datos["JUNTS"] += 4; datos["PP"] -= 2
    if provincia in ["Vizcaya","Guipúzcoa","Álava"]:
        datos["PNV"] += 6; datos["BILDU"] += 5
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
    votos_int = {p:int(v*factor) for p,v in votos.items()}
    tabla = []
    for p in votos_int:
        for i in range(1, escanos+1):
            tabla.append((p,votos_int[p]/i))
    tabla.sort(key=lambda x:x[1], reverse=True)
    resultado = {p:0 for p in votos_int}
    for i in range(escanos):
        resultado[tabla[i][0]] += 1
    return resultado

# ===============================
# CALCULO PRINCIPAL Y ACTUALIZACIÓN HISTÓRICO
# ===============================
def calcular_proyecciones():
    base_escenario = ajustar_escenario(BASE_NACIONAL)
    escanos_totales = {p:0 for p in PARTIDOS}
    datos_prov = []

    fecha_actual = str(date.today())

    for prov in PROVINCIAS:
        votos = ajustar_territorial(base_escenario, prov)
        escanos = ESCANOS[prov]
        reparto = dhondt(votos, escanos)

        fila = {"Provincia":prov,"Escaños Totales":escanos}
        fila.update(votos)
        fila.update({f"Escaños {p}":reparto[p] for p in PARTIDOS})

        # Guardar histórico
        for p in PARTIDOS:
            df_hist.loc[len(df_hist)] = [fecha_actual, prov, p, votos[p], reparto[p]]

        # Mini gráfico horizontal con tooltip histórico
        hover_text = []
        for p in PARTIDOS:
            hist_partido = df_hist[(df_hist.Provincia==prov)&(df_hist.Partido==p)]
            hist_votos = hist_partido["Votos"].tolist()
            hist_text = f"Semana actual: {votos[p]:.2f}%<br>Histórico: {', '.join(f'{v:.2f}%' for v in hist_votos[-4:])}"
            hover_text.append(hist_text)

        fig_mini = go.Figure()
        fig_mini.add_trace(go.Bar(
            x=[votos[p] for p in PARTIDOS],
            y=PARTIDOS,
            orientation='h',
            marker_color=[PARTIDOS_COLORES[p] for p in PARTIDOS],
            hovertemplate=hover_text
        ))
        fig_mini.update_layout(height=200, margin=dict(l=20,r=20,t=20,b=20), xaxis=dict(title="%", range=[0, max(votos.values())*1.2]), yaxis=dict(title="Partido"))

        fila["Mini Gráfico"] = fig_mini

        datos_prov.append(fila)
        for p in PARTIDOS:
            escanos_totales[p] += reparto[p]

    # Guardar CSV actualizado
    df_hist.to_csv(HISTORICO_FILE,index=False)
    df_prov = pd.DataFrame(datos_prov)
    return escanos_totales, df_prov, df_hist

escanos_totales, df_prov, df_hist = calcular_proyecciones()

# ===============================
# TABS
# ===============================
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Hemiciclo","Desglose Provincial","Radar Estratégico","Metodología y Fuentes","Histórico Semanal"])

# ---------- HEMICICLO ----------
with tab1:
    st.subheader("Proyección de Escaños (350 oficiales)")
    df_hemi = pd.DataFrame({"Partido": list(escanos_totales.keys()),"Escaños": list(escanos_totales.values())})
    df_hemi = df_hemi.sort_values("Escaños",ascending=False)
    fig = px.bar(df_hemi, x="Partido", y="Escaños", color="Partido", color_discrete_map=PARTIDOS_COLORES)
    st.plotly_chart(fig,use_container_width=True)
    total = df_hemi["Escaños"].sum()
    st.write(f"Total escaños asignados: {total:.0f} / 350")
    mayoria = 176
    st.write(f"Mayoría absoluta: {mayoria}")

# ---------- DESGLOSE PROVINCIAL ----------
with tab2:
    st.subheader("Datos por Provincia y Reparto de Escaños")
    for _, fila in df_prov.iterrows():
        st.markdown(f"### {fila['Provincia']} ({fila['Escaños Totales']} escaños)")
        st.plotly_chart(fila["Mini Gráfico"], use_container_width=True)
        escanos_detalle = {p:fila[f"Escaños {p}"] for p in PARTIDOS}
        st.write("Reparto de Escaños:", escanos_detalle)
        if st.button(f"Ver evolución {fila['Provincia']}", key=f"hist_{fila['Provincia']}"):
            df_hist_prov = df_hist[df_hist.Provincia==fila['Provincia']]
            fig_line = go.Figure()
            for p in PARTIDOS:
                df_p = df_hist_prov[df_hist_prov.Partido==p]
                fig_line.add_trace(go.Scatter(x=pd.to_datetime(df_p.Fecha), y=df_p.Votos, mode='lines+markers', name=p, line=dict(color=PARTIDOS_COLORES[p])))
            fig_line.update_layout(title=f"Evolución de Votos - {fila['Provincia']}", xaxis_title="Fecha", yaxis_title="Votos (%)", height=400)
            st.plotly_chart(fig_line,use_container_width=True)

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
    st.subheader("Flujo de Cálculo Interactivo (Sankey)")
    st.markdown("Ajuste Nacional → Ajuste Territorial → Ruido → D’Hondt → Proyección")
    fig_flow = go.Figure(go.Sankey(
        node=dict(pad=15, thickness=20, line=dict(color="black", width=0.5),
                  label=["Ajuste Nacional","Ajuste Territorial","Ruido","D’Hondt","Proyección"],
                  color=["#636EFA","#EF553B","#00CC96","#AB63FA","#FFA15A"]),
        link=dict(source=[0,1,2,3], target=[1,2,3,4], value=[1,1,1,1], color=["#636EFA","#EF553B","#00CC96","#AB63FA"])
    ))
    fig_flow.update_layout(height=300, margin=dict(l=20,r=20,t=20,b=20))
    st.plotly_chart(fig_flow,use_container_width=True)

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

# ---------- HISTÓRICO SEMANAL ----------
with tab5:
    st.subheader("Histórico Semanal de Votos y Escaños")
    st.dataframe(df_hist, use_container_width=True)
    st.markdown("Se puede filtrar por provincia, partido o fecha usando la funcionalidad de Streamlit DataFrame.")

# ---------- PIE DE PÁGINA ----------
st.markdown("---")
st.markdown("© Miguel Castillo | contacto: [mybloggingnotes@gmail.com](mailto:mybloggingnotes@gmail.com)")
