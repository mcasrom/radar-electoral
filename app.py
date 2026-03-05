import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import random
import os
from datetime import date
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

# ===============================
# CONFIGURACIÓN
# ===============================
st.set_page_config(layout="wide")
st.title("🇪🇸 Sistema Multicapa de Inteligencia Electoral")

# ===============================
# PARTIDOS Y COLORES
# ===============================
PARTIDOS = ["PP","PSOE","VOX","SUMAR","SALF","ERC","JUNTS","PNV","BILDU","CC","UPN","BNG","OTROS"]
PARTIDOS_COLORES = {
    "PP": "#1f77b4",
    "PSOE": "#d62728",
    "VOX": "#2ca02c",
    "SUMAR": "#9467bd",
    "SALF": "#7f7f7f",
    "ERC": "#ff7f0e",
    "JUNTS": "#8c564b",
    "PNV": "#17becf",
    "BILDU": "#bcbd22",
    "CC": "#e377c2",
    "UPN": "#8c564b",
    "BNG": "#17becf",
    "OTROS": "#c7c7c7"
}
BASE_NACIONAL = {
    "PP":30,"PSOE":27,"VOX":16,"SUMAR":8,"SALF":4,
    "ERC":2,"JUNTS":2,"PNV":1.5,"BILDU":1.2,"CC":0.8,
    "UPN":0.5,"BNG":0.7,"OTROS":6.3
}

# ===============================
# PROVINCIAS Y ESCANOS
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
# SIDEBAR CONTROL
# ===============================
st.sidebar.header("Control de Escenarios")
factor_vivienda = st.sidebar.slider("Impacto Crisis Vivienda",0,100,50)
factor_energia = st.sidebar.slider("Impacto Energía",0,100,50)
fiabilidad = st.sidebar.slider("Fiabilidad Datos Oficiales (%)",0,100,80)

st.sidebar.markdown("""
Este panel permite simular escenarios políticos estructurales.

• Crisis vivienda → Impacto en voto urbano y clases medias  
• Energía → Impacto en voto conservador y rural  
• Fiabilidad → Simula incertidumbre estadística  

El objetivo del proyecto es detectar tendencias semanales de decisión de voto.
""")

# ===============================
# HISTÓRICO
# ===============================
HIST_FILE = "historico_semanal.csv"
if os.path.exists(HIST_FILE):
    df_hist = pd.read_csv(HIST_FILE)
else:
    df_hist = pd.DataFrame(columns=["Fecha","Provincia","Partido","Votos","Escaños"])

# ===============================
# FUNCIONES
# ===============================
def normalizar(dic):
    total = sum(dic.values())
    if total == 0: return dic
    return {k: v * 100 / total for k,v in dic.items()}

def ajustar_escenario(base):
    ajuste = base.copy()
    ajuste["PP"] += (factor_vivienda - 50) * 0.02
    ajuste["PSOE"] -= (factor_vivienda - 50) * 0.015
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
    ruido = (100-fiabilidad)/100
    for p in datos:
        datos[p] += random.uniform(-ruido*2, ruido*2)
    return normalizar(datos)

def dhondt(votos, escanos):
    factor = 10000
    votos_int = {p:int(v*factor) for p,v in votos.items()}
    tabla = [(p, votos_int[p]/i) for p in votos_int for i in range(1, escanos+1)]
    tabla.sort(key=lambda x:x[1], reverse=True)
    resultado = {p:0 for p in votos_int}
    for i in range(escanos):
        resultado[tabla[i][0]] += 1
    return resultado

def export_pdf(datos_prov):
    doc = SimpleDocTemplate("reporte_electoral.pdf", pagesize=A4)
    styles = getSampleStyleSheet()
    elements = [Paragraph("Reporte Electoral Semanal", styles['Title']), Spacer(1,12)]
    for prov in datos_prov:
        elements.append(Paragraph(f"Provincia: {prov['Provincia']}", styles['Heading2']))
        for p,v in prov["Votos"].items():
            elements.append(Paragraph(f"{p}: {v:.2f}% - Escaños: {prov['Reparto'][p]}", styles['Normal']))
        elements.append(Spacer(1,12))
    doc.build(elements)

# ===============================
# CALCULO PRINCIPAL
# ===============================
def calcular():
    fecha = str(date.today())
    base_esc = ajustar_escenario(BASE_NACIONAL)
    escanos_totales = {p:0 for p in PARTIDOS}
    datos_prov = []
    for prov in PROVINCIAS:
        votos = ajustar_territorial(base_esc, prov)
        escanos = ESCANOS[prov]
        reparto = dhondt(votos, escanos)
        for p in PARTIDOS:
            if not ((df_hist["Fecha"]==fecha) & (df_hist["Provincia"]==prov) & (df_hist["Partido"]==p)).any():
                df_hist.loc[len(df_hist)] = [fecha,prov,p,votos[p],reparto[p]]
        for p in PARTIDOS:
            escanos_totales[p] += reparto[p]
        datos_prov.append({"Provincia":prov,"Escaños":escanos,"Reparto":reparto,"Votos":votos})
    df_hist.to_csv(HIST_FILE,index=False)
    total = sum(escanos_totales.values())
    if total != 350:
        diferencia = 350-total
        mayor = max(escanos_totales,key=escanos_totales.get)
        escanos_totales[mayor]+=diferencia
    return escanos_totales, datos_prov

escanos_totales, datos_prov = calcular()

# ===============================
# TABS
# ===============================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
["Hemiciclo","Desglose Provincial","Radar Estratégico","Metodología y Fuentes","Histórico Semanal","Métricas Avanzadas"]
)

# ---------------- HEMICICLO
with tab1:
    df_hemi = pd.DataFrame({"Partido":list(escanos_totales.keys()),"Escaños":list(escanos_totales.values())})
    fig = px.bar(df_hemi,x="Partido",y="Escaños",color="Partido",color_discrete_map=PARTIDOS_COLORES)
    st.plotly_chart(fig,use_container_width=True)
    st.write("Total escaños:",df_hemi["Escaños"].sum(),"/ 350")
    st.write("Mayoría absoluta:",176)

# ---------------- DESGLOSE PROVINCIAL
with tab2:
    for prov in datos_prov:
        st.subheader(prov["Provincia"])
        fig = go.Figure(go.Bar(
            x=list(prov["Votos"].values()),
            y=list(prov["Votos"].keys()),
            orientation="h",
            marker_color=[PARTIDOS_COLORES[p] for p in prov["Votos"].keys()]
        ))
        st.plotly_chart(fig,use_container_width=True)
        st.write("Reparto:",prov["Reparto"])

# ---------------- RADAR
with tab3:
    categorias=["Vivienda","Energía","Fiabilidad"]
    valores=[factor_vivienda,factor_energia,fiabilidad]
    fig=go.Figure(go.Scatterpolar(r=valores,theta=categorias,fill="toself"))
    fig.update_layout(polar=dict(radialaxis=dict(range=[0,100])))
    st.plotly_chart(fig,use_container_width=True)

# ---------------- METODOLOGÍA Y FUENTES
with tab4:
    st.header("Arquitectura del Modelo")
    st.markdown("""
Este sistema utiliza un modelo multicapa de simulación electoral:

1. Ajuste Nacional Base  
2. Ajuste Territorial Provincial  
3. Introducción de ruido estadístico controlado  
4. Aplicación del método D’Hondt  
5. Proyección consolidada de escaños  
""")
    st.header("Gestión y Gobernanza de Fuentes")
    st.markdown("""
El modelo combina:

• Resultados oficiales históricos  
• Datos públicos institucionales  
• Encuestas publicadas  
• Ajustes propios estructurales  
• Correcciones por volatilidad  
""")
    st.header("Objetivo Estratégico del Proyecto")
    st.markdown("""
Detectar variaciones semanales en la decisión de voto.

El sistema no pretende sustituir resultados oficiales,
sino anticipar tendencias estructurales y cambios graduales.
""")
    st.header("Limitaciones")
    st.markdown("""
• Modelo probabilístico, no predictivo determinista  
• Sensible a eventos exógenos bruscos  
• No sustituye escrutinio oficial  
""")

# ---------------- HISTÓRICO SEMANAL
with tab5:
    if not df_hist.empty:
        df_hist["Fecha"]=pd.to_datetime(df_hist["Fecha"])
        df_nacional=(df_hist.groupby(["Fecha","Partido"])["Votos"].mean().reset_index())
        fig_trend=go.Figure()
        for p in PARTIDOS:
            df_p=df_nacional[df_nacional["Partido"]==p]
            if not df_p.empty:
                fig_trend.add_trace(go.Scatter(
                    x=df_p["Fecha"],
                    y=df_p["Votos"],
                    mode="lines+markers",
                    name=p,
                    line=dict(color=PARTIDOS_COLORES[p],width=3)
                ))
        fig_trend.update_layout(height=500,hovermode="x unified")
        st.plotly_chart(fig_trend,use_container_width=True)
    st.dataframe(df_hist.sort_values("Fecha",ascending=False),use_container_width=True)

# ---------------- MÉTRICAS AVANZADAS
with tab6:
    st.header("Mapa de calor provincial")
    try:
        df_prov_heat = df_hist[df_hist["Fecha"]==str(date.today())].pivot("Partido","Provincia","Votos")
        fig_heat=px.imshow(df_prov_heat.values, x=df_prov_heat.columns, y=df_prov_heat.index, color_continuous_scale='Viridis')
        st.plotly_chart(fig_heat,use_container_width=True)
    except Exception as e:
        st.write("Error generando heatmap:", e)

    st.header("Exportación PDF")
    if st.button("Generar PDF"):
        try:
            export_pdf(datos_prov)
            st.success("PDF generado: reporte_electoral.pdf")
        except Exception as e:
            st.error(f"Error generando PDF: {e}")

# ===============================
# FOOTER
# ===============================
st.markdown("---")
st.markdown("© M.Castillo  |  mybloggingnotes@gmail.com")
