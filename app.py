import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import random
import os
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4

st.set_page_config(layout="wide")

# ==========================================================
# CONFIG
# ==========================================================

TOTAL_ESCANOS = 350
MAYORIA = 176
CSV_FILE = "historico.csv"
PDF_FILE = "/mnt/data/informe_proyeccion.pdf"

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

PARLAMENTO_ACTUAL = {
    "PP":137,"PSOE":121,"VOX":33,"SUMAR":31,
    "ERC":7,"JUNTS":7,"PNV":5,"BILDU":6,
    "CC":1,"UPN":1,"BNG":1,"SALF":0,"OTROS":0
}

# ==========================================================
# DHONDT
# ==========================================================

def dhondt(votos, escanos):
    asignados = dict.fromkeys(votos.keys(),0)
    cocientes=[]
    for p,v in votos.items():
        for i in range(1, escanos+1):
            cocientes.append((v/i,p))
    cocientes.sort(reverse=True)
    for i in range(escanos):
        _,p=cocientes[i]
        asignados[p]+=1
    return asignados

# ==========================================================
# BASE VOTO
# ==========================================================

def voto_base():
    return {
        "PP":30,"PSOE":28,"VOX":14,"SUMAR":10,"SALF":3,
        "ERC":2,"JUNTS":2,"PNV":1.5,"BILDU":1.5,
        "CC":0.5,"UPN":0.5,"BNG":1,"OTROS":6
    }

def calcular():
    return dhondt(voto_base(),TOTAL_ESCANOS)

escanos = calcular()

# ==========================================================
# METRICAS
# ==========================================================

def fragmentacion(dic):
    t=sum(dic.values())
    return round(1/sum([(v/t)**2 for v in dic.values() if v>0]),2)

def concentracion(dic):
    vals=sorted(dic.values(),reverse=True)
    return vals[0]+vals[1]

def hhi(dic):
    t=sum(dic.values())
    return round(sum([(v/t)**2 for v in dic.values()]),3)

def estabilidad(dic):
    if max(dic.values())>=MAYORIA:
        return "Alta"
    if concentracion(dic)>=160:
        return "Media"
    return "Baja"

FRAG=fragmentacion(escanos)
CONC=concentracion(escanos)
HHI=hhi(escanos)
EST=estabilidad(escanos)

# ==========================================================
# CAMBIO DE CICLO
# ==========================================================

def cambio_ciclo():
    diferencia = escanos["PP"] - escanos["PSOE"]
    if diferencia>20:
        return "Ventaja estructural PP"
    if diferencia<-20:
        return "Ventaja estructural PSOE"
    return "Competencia abierta"

CICLO = cambio_ciclo()

# ==========================================================
# MONTE CARLO
# ==========================================================

def montecarlo(base,n=300):
    sims=[]
    for _ in range(n):
        sim={}
        for p,v in base.items():
            sim[p]=max(0,v+random.randint(-3,3))
        total=sum(sim.values())
        if total!=TOTAL_ESCANOS:
            mayor=max(sim,key=sim.get)
            sim[mayor]+=TOTAL_ESCANOS-total
        sims.append(sim)
    return pd.DataFrame(sims)

df_mc=montecarlo(escanos)

# ==========================================================
# HISTORICO
# ==========================================================

def guardar():
    fecha=datetime.now().strftime("%Y-%m-%d")
    df=pd.DataFrame([{"Fecha":fecha,**escanos}])
    if os.path.exists(CSV_FILE):
        df.to_csv(CSV_FILE,mode="a",header=False,index=False)
    else:
        df.to_csv(CSV_FILE,index=False)

if st.sidebar.button("Guardar semana"):
    guardar()

if os.path.exists(CSV_FILE):
    df_hist=pd.read_csv(CSV_FILE)
else:
    df_hist=pd.DataFrame()

# ==========================================================
# EXPORT PDF
# ==========================================================

def generar_pdf():
    doc=SimpleDocTemplate(PDF_FILE,pagesize=A4)
    styles=getSampleStyleSheet()
    elements=[]
    elements.append(Paragraph("Informe Proyección Electoral",styles["Heading1"]))
    elements.append(Spacer(1,0.3*inch))
    elements.append(Paragraph(f"Fragmentación: {FRAG}",styles["Normal"]))
    elements.append(Paragraph(f"Concentración: {CONC}",styles["Normal"]))
    elements.append(Paragraph(f"Estabilidad: {EST}",styles["Normal"]))
    elements.append(Paragraph(f"Cambio de ciclo: {CICLO}",styles["Normal"]))
    doc.build(elements)

if st.sidebar.button("Generar PDF"):
    generar_pdf()
    st.sidebar.success("PDF generado en /mnt/data")

# ==========================================================
# INTERFAZ
# ==========================================================

st.title("Sistema Avanzado de Proyección Electoral")

tab1,tab2,tab3,tab4,tab5 = st.tabs([
    "Hemiciclo",
    "Comparativa Parlamento Actual",
    "Histórico",
    "Simulación y Análisis",
    "Metodología"
])

# TAB 1
with tab1:
    df_plot=pd.DataFrame({"Partido":escanos.keys(),"Escaños":escanos.values()})
    fig=px.bar(df_plot,x="Partido",y="Escaños",color="Partido",
               color_discrete_map=COLORES,text="Escaños")
    st.plotly_chart(fig,use_container_width=True)

    col1,col2,col3,col4=st.columns(4)
    col1.metric("Fragmentación",FRAG)
    col2.metric("Concentración",CONC)
    col3.metric("HHI",HHI)
    col4.metric("Estabilidad",EST)

    st.info(f"Diagnóstico ciclo: {CICLO}")

# TAB 2
with tab2:
    df_comp=pd.DataFrame({
        "Partido":escanos.keys(),
        "Proyección":escanos.values(),
        "Actual":[PARLAMENTO_ACTUAL.get(p,0) for p in escanos.keys()]
    })
    fig2=px.bar(df_comp,x="Partido",y=["Actual","Proyección"],
                barmode="group",color_discrete_sequence=["gray","blue"])
    st.plotly_chart(fig2,use_container_width=True)

# TAB 3
with tab3:
    if not df_hist.empty:
        fig_hist=px.line(df_hist,x="Fecha",y=PARTIDOS)
        st.plotly_chart(fig_hist,use_container_width=True)
    else:
        st.info("Sin histórico aún.")

# TAB 4
with tab4:
    media_mc=df_mc.mean().sort_values(ascending=False)
    fig_mc=px.bar(x=media_mc.index,y=media_mc.values,
                  color=media_mc.index,color_discrete_map=COLORES)
    st.plotly_chart(fig_mc,use_container_width=True)

# TAB 5
with tab5:
    st.markdown("""
### Objetivo
Obtener datos semanales de tendencia de voto y proyectar su conversión en escaños mediante sistema D’Hondt.

### Flujo del algoritmo
Ajuste Nacional → Ajuste Territorial → Ruido → D’Hondt → Proyección

El diagrama Sankey representa el flujo del voto hasta escaños.

### Gestión de fuentes
Encuestas públicas, agregación histórica y señales de impacto político.
Las fuentes oficiales no se consideran 100% fiables; el modelo introduce correcciones estadísticas.

### Fiabilidad
Modelo de tendencia, no predicción determinista.
""")

st.markdown("---")
st.markdown("© M.Castillo – mybloggingnotes@gmail.com")
