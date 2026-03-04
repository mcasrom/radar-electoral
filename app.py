# app.py — Sistema Multicapa de Inteligencia Electoral 🇪🇸 v11.0
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json

# -----------------------------
# 1. Configuración página
# -----------------------------
st.set_page_config(
    page_title="🇪🇸 Sistema Multicapa de Inteligencia Electoral",
    layout="wide",
    initial_sidebar_state="expanded"
)

PALETA = {
    'PP': '#1E4B8F', 'PSOE': '#E30613', 'VOX': '#63BE21', 'SUMAR': '#E53187',
    'PODEMOS': '#612D62', 'SALF': '#000000', 'ERC': '#FFB232', 'JUNTS': '#00C3B2',
    'PNV': '#008000', 'BILDU': '#B5CF18', 'BNG': '#ADCFE3', 'CC': '#FFD700', 'UPN': '#10448E', 'OTROS': '#CCCCCC'
}

# -----------------------------
# 2. Sidebar
# -----------------------------
st.sidebar.header("🕹️ Control de Escenarios")
tension_vivienda = st.sidebar.slider("Factor Crisis Vivienda", 0, 100, 85)
tension_energia = st.sidebar.slider("Factor Energía", 0, 100, 70)
sesgo_oficial = st.sidebar.select_slider(
    "Fiabilidad Datos Oficiales",
    options=['BAJA', 'MEDIA', 'ALTA'],
    value='BAJA'
)

# -----------------------------
# 3. Carga de datos
# -----------------------------
with open("data/provincias.json") as f:
    provincias = json.load(f)

# Histórico de encuestas reales en formato wide
df_historico = pd.read_csv("data/votos_historicos.csv", parse_dates=["fecha"])
partidos = ["PP","PSOE","VOX","SUMAR","PODEMOS"]

# Convertimos wide -> long
df_long = df_historico.melt(
    id_vars=["fecha","fuente","fiabilidad"],
    value_vars=partidos,
    var_name="partido",
    value_name="voto"
)

# -----------------------------
# 4. Funciones auxiliares
# -----------------------------
def dhondt(votos, esc):
    v_validos = {p:v for p,v in votos.items() if v>0}
    lista = []
    for p,v in v_validos.items():
        for i in range(1, esc+1):
            lista.append({'p':p,'c':v/i})
    df = pd.DataFrame(lista).sort_values('c', ascending=False)
    return df.head(esc)['p'].value_counts().to_dict()

def monte_carlo(votos, n_sim=2000, sd=2.5):
    sims = []
    for _ in range(n_sim):
        sim = {p:max(0,np.random.normal(v,sd)) for p,v in votos.items()}
        sims.append(sim)
    return sims

def bloques_nacionales(df):
    BLOQUES = {
        "Centro-Derecha":["PP","VOX","UPN","CC","OTROS"],
        "Centro-Izquierda":["PSOE","SUMAR","PODEMOS"],
        "Regionalistas":["ERC","PNV","BILDU","JUNTS","BNG"]
    }
    total = {b:0 for b in BLOQUES}
    for b,part in BLOQUES.items():
        total[b] = sum([df.get(p,0) for p in part])
    return total

def prob_mayoria(sims, BLOQUES, meta=176):
    conteo = {b:0 for b in BLOQUES}
    n = len(sims)
    for sim in sims:
        for b, p_list in BLOQUES.items():
            if sum([sim.get(p,0) for p in p_list]) >= meta:
                conteo[b] +=1
    return {b: round(100*conteo[b]/n,2) for b in BLOQUES}

def generar_narrativa(frag):
    if frag>0.5:
        return "Parlamento fragmentado, se prevén coaliciones complejas entre bloques."
    else:
        return "Bloques relativamente estables, posibilidad de mayoría clara en simulaciones."

def fragmentacion(esc_dict):
    total = sum(esc_dict.values())
    p = np.array([v/total for v in esc_dict.values()])
    return 1/(np.sum(p**2))

def media_ponderada_tiempo(df_long):
    df_long["voto_pond"] = df_long["voto"] * df_long["fiabilidad"]
    df_grouped = df_long.groupby(["fecha","partido"]).apply(
        lambda x: x["voto_pond"].sum() / x["fiabilidad"].sum()
    ).reset_index(name="voto_pond")
    df_final = df_grouped.pivot(index="fecha", columns="partido", values="voto_pond")
    df_final = df_final[partidos]
    return df_final

# -----------------------------
# 5. Últimos votos y simulaciones
# -----------------------------
ultimos = df_long.groupby("partido").apply(
    lambda x: np.average(x["voto"], weights=x["fiabilidad"])
).to_dict()

simulaciones = monte_carlo(ultimos, n_sim=2000)

# -----------------------------
# 6. D’Hondt provincial y nacional
# -----------------------------
esc_nacional = {p:0 for p in partidos}
tabla_provincias = []

for prov in provincias:
    votos = ultimos.copy()
    esc = prov["escanos"]
    reparto = dhondt(votos, esc)
    for p,e in reparto.items():
        esc_nacional[p] += e
    fila = {"Provincia":prov["nombre"], **reparto}
    tabla_provincias.append(fila)

df_provincias = pd.DataFrame(tabla_provincias).fillna(0)

# -----------------------------
# 7. Bloques y fragmentación
# -----------------------------
BLOQUES = {
    "Centro-Derecha":["PP","VOX","UPN","CC","OTROS"],
    "Centro-Izquierda":["PSOE","SUMAR","PODEMOS"],
    "Regionalistas":["ERC","PNV","BILDU","JUNTS","BNG"]
}

prob_bloques = prob_mayoria(simulaciones, BLOQUES)
frag_index = fragmentacion(esc_nacional)

# -----------------------------
# 8. Evolución temporal
# -----------------------------
df_evolucion = media_ponderada_tiempo(df_long)

# -----------------------------
# 9. Layout principal
# -----------------------------
st.markdown("<h1 style='text-align:center; color:#1E4B8F;'>Sistema Multicapa de Inteligencia Electoral 🇪🇸</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align:center; color:#555;'>Monitorización académica y OSINT estratégico</h4>", unsafe_allow_html=True)
st.markdown("---", unsafe_allow_html=True)

tabs = st.tabs([
    "🏛️ Hemiciclo Nacional",
    "📍 Provincias",
    "📊 Evolución Temporal",
    "📡 Radar OSINT",
    "📝 Metodología y Fuentes",
    "🛰️ Narrativa Estratégica"
])

# Tab 1: Hemiciclo Nacional
with tabs[0]:
    st.subheader("Distribución Nacional de Escaños")
    df_bar = pd.DataFrame(list(esc_nacional.items()), columns=["Partido","Escaños"])
    fig_bar = px.bar(df_bar, x="Partido", y="Escaños", color="Partido", color_discrete_map=PALETA, text="Escaños")
    st.plotly_chart(fig_bar, use_container_width=True)
    st.metric("Índice de Fragmentación Nacional", round(frag_index,2))
    st.subheader("Probabilidad de Mayoría Absoluta por Bloque")
    df_prob = pd.DataFrame(list(prob_bloques.items()), columns=["Bloque","Probabilidad %"])
    st.dataframe(df_prob, use_container_width=True)
    fig_bloque = px.bar(
        df_prob, x="Bloque", y="Probabilidad %", text="Probabilidad %",
        color="Bloque",
        color_discrete_map={"Centro-Derecha":"#1E4B8F","Centro-Izquierda":"#E30613","Regionalistas":"#63BE21"}
    )
    st.plotly_chart(fig_bloque, use_container_width=True)

# Tab 2: Provincias
with tabs[1]:
    st.subheader("Tabla de Reparto por Provincia")
    st.dataframe(df_provincias, use_container_width=True)
    fig_prov = px.bar(
        df_provincias.melt(id_vars=["Provincia"], var_name="Partido", value_name="Escaños"),
        x="Provincia", y="Escaños", color="Partido", color_discrete_map=PALETA
    )
    st.plotly_chart(fig_prov, use_container_width=True)

# Tab 3: Evolución Temporal
with tabs[2]:
    st.subheader("📈 Evolución Temporal de Intención de Voto (Datos Reales)")
    fig_time = px.line(
        df_evolucion.reset_index(),
        x="fecha",
        y=df_evolucion.columns,
        markers=True,
        labels={"value":"Intención de Voto (%)","variable":"Partido"},
        color_discrete_map={
            "PP": "#1E4B8F",
            "PSOE": "#E30613",
            "VOX": "#63BE21",
            "SUMAR": "#E53187",
            "PODEMOS": "#612D62"
        }
    )
    fig_time.update_layout(title="Intención de Voto Temporal (ponderada por fiabilidad)", title_x=0.5)
    st.plotly_chart(fig_time, use_container_width=True)
    st.dataframe(df_evolucion.tail(5), use_container_width=True)

# Tab 4: Radar OSINT
with tabs[3]:
    st.subheader("Radar de Factores Estratégicos")
    factores = [tension_vivienda, tension_energia, 60, 80, 75]
    etiquetas = ['Vivienda','Energía','Defensa','Inflación','Territorio']
    fig_radar = go.Figure(go.Scatterpolar(r=factores+[factores[0]], theta=etiquetas+[etiquetas[0]], fill='toself', line_color='#E30613'))
    st.plotly_chart(fig_radar, use_container_width=True)

# Tab 5: Metodología y Fuentes
with tabs[4]:
    st.subheader("Metodología y Trazabilidad")
    st.markdown(f"""
- Escenario de fiabilidad: **{sesgo_oficial}**
- Fuentes: CIS, GAD3, Sigma Dos, 40dB
- Monte Carlo: 2000 iteraciones
- Algoritmo D’Hondt provincial y suma nacional
- Bloques y probabilidad de mayoría absoluta
- Indicadores: Fragmentación y Volatilidad
""")

# Tab 6: Narrativa OSINT
with tabs[5]:
    st.subheader("Narrativa Estratégica")
    st.info(generar_narrativa(frag_index))
