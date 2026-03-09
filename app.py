import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import random
import os
import math
from datetime import date, datetime

# ===============================
# CONFIGURACIÓN
# ===============================
st.set_page_config(layout="wide", page_title="España Vota 2026", page_icon="🗳️")
st.title("🇪🇸 Sistema Multicapa de Inteligencia Electoral v2.0")

# ===============================
# PARTIDOS Y COLORES (sin cambios)
# ===============================
PARTIDOS = ["PP","PSOE","VOX","SUMAR","SALF","ERC","JUNTS","PNV","BILDU","CC","UPN","BNG","OTROS"]
PARTIDOS_COLORES = {
    "PP": "#1f77b4","PSOE": "#d62728","VOX": "#2ca02c","SUMAR": "#9467bd",
    "SALF": "#7f7f7f","ERC": "#ff7f0e","JUNTS": "#8c564b","PNV": "#17becf",
    "BILDU": "#bcbd22","CC": "#e377c2","UPN": "#8c564b","BNG": "#17becf","OTROS": "#c7c7c7"
}
BASE_NACIONAL = {
    "PP":30,"PSOE":27,"VOX":16,"SUMAR":8,"SALF":4,
    "ERC":2,"JUNTS":2,"PNV":1.5,"BILDU":1.2,"CC":0.8,
    "UPN":0.5,"BNG":0.7,"OTROS":6.3
}

# ===============================
# CASTILLA Y LEÓN — DATOS ELECTORALES
# ===============================
# Composición actual Cortes de CyL (2022, 84 procuradores)
CYL_COMPOSICION_ACTUAL = {
    "PP": 31,
    "PSOE": 28,
    "VOX": 13,
    "UPL": 1,    # Unión del Pueblo Leonés
    "Por Ávila": 1,
    "OTROS": 10   # agrupa IU, Cs en liquidación, etc.
}

# Partidos relevantes en CyL para elecciones autonómicas
PARTIDOS_CYL = ["PP", "PSOE", "VOX", "SUMAR", "Por Ávila", "UPL", "OTROS"]
COLORES_CYL = {
    "PP": "#1f77b4",
    "PSOE": "#d62728",
    "VOX": "#2ca02c",
    "SUMAR": "#9467bd",
    "Por Ávila": "#e67e22",
    "UPL": "#8e44ad",
    "OTROS": "#c7c7c7"
}

# Intención de voto base en CyL (estimación estructural, ajustada al perfil demográfico)
# CyL: envejecida, rural, histórico conservador, alta abstención en interior
BASE_CYL = {
    "PP": 32.0,    # consenso encuestas mar2026: 29-35%
    "PSOE": 28.0,  # recupera vs 2022 — encuestas 27-32%
    "VOX": 19.0,   # subida fuerte — SocioMétrica+Gesop ~20%
    "SUMAR": 3.5,  # debacle nacional se refleja en CyL
    "Por Ávila": 1.5,
    "UPL": 4.5,    # refuerzo leonesismo — encuestas 4-5%
    "OTROS": 11.0  # abstención + indecisos
}

# Provincias de CyL y escaños en Cortes de CyL (elecciones autonómicas)
# 84 procuradores + 2 por Ceuta y Melilla (solo nacionales; aquí usamos la distribución autonómica)
ESCANOS_CYL = {
    "Ávila": 9,
    "Burgos": 12,
    "León": 14,
    "Palencia": 7,
    "Salamanca": 11,
    "Segovia": 7,
    "Soria": 5,
    "Valladolid": 14,
    "Zamora": 7
}
# Nota: En realidad son 82 procuradores en 2024 tras reforma. Usamos 82.
TOTAL_CYL = sum(ESCANOS_CYL.values())  # 86 → ajustar al total real

# Variables estructurales CyL
VARIABLES_CYL = {
    "Despoblación": {"impacto_PP": +1.2, "impacto_PSOE": -0.8, "impacto_VOX": +0.5},
    "Desempleo Juvenil": {"impacto_PP": -1.0, "impacto_PSOE": +0.8, "impacto_SUMAR": +1.5},
    "Gestión Sanitaria": {"impacto_PP": -1.5, "impacto_PSOE": +1.2, "impacto_VOX": +0.3},
    "Infraestructuras": {"impacto_PP": -0.8, "impacto_PSOE": +0.5, "impacto_VOX": +0.2},
    "Cuestión Leonesa": {"impacto_PP": -1.0, "impacto_UPL": +3.0, "impacto_PSOE": +0.5},
}

# ===============================
# PROVINCIAS NACIONALES Y ESCANOS
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
st.sidebar.header("🎛️ Control de Escenarios")
factor_vivienda = st.sidebar.slider("🏠 Impacto Crisis Vivienda", 0, 100, 50)
factor_energia = st.sidebar.slider("⚡ Impacto Energía", 0, 100, 50)
fiabilidad = st.sidebar.slider("📊 Fiabilidad Datos Oficiales (%)", 0, 100, 80)

st.sidebar.markdown("---")

st.sidebar.markdown("---")
st.sidebar.markdown("---")
st.sidebar.subheader("🏴󠁥󠁳󠁰󠁶󠁿 Escenarios Euskadi")
factor_independentismo = st.sidebar.slider("Independentismo vasco",   0,100,50)
factor_izq_abertzale   = st.sidebar.slider("Izq. abertzale vs PNV",   0,100,50)
factor_economia_vasca  = st.sidebar.slider("Economía vasca (empleo)", 0,100,60)
factor_concierto_eco   = st.sidebar.slider("Concierto Económico",     0,100,55)
umbral_eus             = st.sidebar.slider("Umbral electoral Eus.(%)",3,5,3)
st.sidebar.subheader("🌿 Escenarios Galicia")
factor_despoblacion_gal = st.sidebar.slider("Despoblación Galicia",   0, 100, 60)
factor_bng_urbano       = st.sidebar.slider("BNG Urbano (Vigo/Coruña)",0,100, 55)
factor_pesca            = st.sidebar.slider("Sector Pesquero",         0, 100, 50)
factor_autogobierno_gal = st.sidebar.slider("Autogobierno Galicia",    0, 100, 45)
umbral_gal              = st.sidebar.slider("Umbral electoral Gal.(%)",3, 5,   5)

st.sidebar.markdown("---")
st.sidebar.subheader("🏙️ Escenarios Madrid")
factor_vivienda_mad = st.sidebar.slider("Vivienda Madrid",      0, 100, 70)
factor_ayuso        = st.sidebar.slider("Efecto Ayuso",         0, 100, 65)
factor_fiscal       = st.sidebar.slider("Fiscalidad Baja",      0, 100, 60)
factor_migracion    = st.sidebar.slider("Migración Madrid",     0, 100, 55)
umbral_mad          = st.sidebar.slider("Umbral Madrid (%)",    3, 5,    5)
st.sidebar.subheader("🌞 Escenarios Andalucía")
factor_desempleo_and  = st.sidebar.slider("Desempleo Andalucía",     0, 100, 65)
factor_vivienda_and   = st.sidebar.slider("Vivienda/Turismo And.",    0, 100, 60)
factor_agua           = st.sidebar.slider("Crisis Agua/Sequía",       0, 100, 55)
factor_rural_urbano   = st.sidebar.slider("Peso Rural vs Urbano",     0, 100, 50)
umbral_and            = st.sidebar.slider("Umbral electoral And.(%)", 3, 5,    3)

st.sidebar.markdown("---")
st.sidebar.subheader("🏛️ Escenarios CyL")
factor_despoblacion = st.sidebar.slider("Despoblación CyL", 0, 100, 60)
factor_cuestion_leonesa = st.sidebar.slider("Cuestión Leonesa", 0, 100, 40)
factor_sanidad_cyl = st.sidebar.slider("Crisis Sanitaria CyL", 0, 100, 55)
umbral_cyl = st.sidebar.slider("Umbral electoral CyL (%)", 3, 5, 3)

st.sidebar.markdown("---")
st.sidebar.markdown("""
**Leyenda de Variables**  
• **Vivienda** → Voto urbano y clases medias  
• **Energía** → Voto conservador y rural  
• **Fiabilidad** → Incertidumbre estadística  
• **Despoblación** → Variable clave CyL  
• **Cuestión Leonesa** → Fragmentación territorial  
""")

# ===============================
# HISTÓRICO
# ===============================
HIST_FILE = "historico_semanal.csv"
HIST_CYL_FILE = "historico_cyl.csv"

if os.path.exists(HIST_FILE):
    df_hist = pd.read_csv(HIST_FILE)
else:
    df_hist = pd.DataFrame(columns=["Fecha","Provincia","Partido","Votos","Escaños"])

if os.path.exists(HIST_CYL_FILE):
    df_hist_cyl = pd.read_csv(HIST_CYL_FILE)
else:
    df_hist_cyl = pd.DataFrame(columns=["Fecha","Provincia","Partido","Votos","Escaños","Escenario"])

# ===============================
# FUNCIONES BASE (compatibles con código original)
# ===============================
def normalizar(dic):
    total = sum(dic.values())
    if total == 0:
        return dic
    return {k: v*100/total for k,v in dic.items()}

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
    ruido = (100 - fiabilidad) / 100
    for p in datos:
        datos[p] += random.uniform(-ruido*2, ruido*2)
    return normalizar(datos)

def dhondt(votos, escanos):
    factor = 10000
    votos_int = {p: int(v * factor) for p, v in votos.items()}
    tabla = [(p, votos_int[p] / i) for p in votos_int for i in range(1, escanos+1)]
    tabla.sort(key=lambda x: x[1], reverse=True)
    resultado = {p: 0 for p in votos_int}
    for i in range(escanos):
        resultado[tabla[i][0]] += 1
    return resultado

# ===============================
# FUNCIONES AVANZADAS — MÉTRICAS
# ===============================

def calcular_indice_polarizacion(votos_dict):
    """
    Índice de polarización bipolar (Esteban & Ray adaptado).
    Mide concentración en extremos vs centro.
    Rango 0 (baja) → 1 (alta).
    """
    valores = list(votos_dict.values())
    total = sum(valores)
    if total == 0:
        return 0
    proporciones = [v / total for v in valores]
    # Índice de Herfindahl-Hirschman normalizado como proxy de polarización
    hhi = sum(p**2 for p in proporciones)
    n = len(proporciones)
    hhi_min = 1 / n
    hhi_max = 1.0
    polarizacion = (hhi - hhi_min) / (hhi_max - hhi_min) if hhi_max > hhi_min else 0
    return round(polarizacion, 3)

def calcular_indice_fragmentacion(escanos_dict):
    """
    Número Efectivo de Partidos (Laakso-Taagepera).
    NEP = 1 / Σ(pi²)  donde pi = fracción de escaños.
    NEP < 2.5 → sistema dominante; 2.5-4 → pluralismo moderado; >4 → alta fragmentación.
    """
    total = sum(escanos_dict.values())
    if total == 0:
        return 0
    proporciones = [v / total for v in escanos_dict.values() if v > 0]
    nep = 1 / sum(p**2 for p in proporciones)
    return round(nep, 2)

def calcular_volatilidad(df_hist_local, partido, ventana=4):
    """
    Volatilidad electoral: desviación estándar del % de voto en las últimas N semanas.
    """
    if df_hist_local.empty:
        return 0
    df_p = df_hist_local[df_hist_local["Partido"] == partido].sort_values("Fecha")
    if len(df_p) < 2:
        return 0
    serie = df_p["Votos"].tail(ventana)
    return round(serie.std(), 2)

def calcular_indice_gobernabilidad(escanos_dict, umbral=176):
    """
    Distancia a mayoría absoluta para los dos bloques principales.
    Retorna dict con análisis de coaliciones viables.
    """
    total = sum(escanos_dict.values())
    bloque_derecha = escanos_dict.get("PP", 0) + escanos_dict.get("VOX", 0) + escanos_dict.get("UPN", 0)
    bloque_izquierda = escanos_dict.get("PSOE", 0) + escanos_dict.get("SUMAR", 0) + escanos_dict.get("BILDU", 0)
    bloque_pp_salf = escanos_dict.get("PP", 0) + escanos_dict.get("SALF", 0)

    return {
        "Bloque D (PP+VOX+UPN)": bloque_derecha,
        "Bloque I (PSOE+SUMAR+BILDU)": bloque_izquierda,
        "PP+SALF": bloque_pp_salf,
        "Distancia MA Derecha": umbral - bloque_derecha,
        "Distancia MA Izquierda": umbral - bloque_izquierda,
        "Gobierno posible Derecha": bloque_derecha >= umbral,
        "Gobierno posible Izquierda": bloque_izquierda >= umbral,
    }

def calcular_sesgo_sistema(votos_dict, escanos_dict):
    """
    Índice de proporcionalidad de Gallagher (least squares index).
    LSq = sqrt(0.5 * Σ(vi - si)²)
    Valores bajos = sistema proporcional; valores altos = sistema mayoritario/distorsionado.
    """
    total_votos = sum(votos_dict.values())
    total_escanos = sum(escanos_dict.values())
    if total_votos == 0 or total_escanos == 0:
        return 0
    partidos = set(list(votos_dict.keys()) + list(escanos_dict.keys()))
    suma = 0
    for p in partidos:
        vi = (votos_dict.get(p, 0) / total_votos) * 100
        si = (escanos_dict.get(p, 0) / total_escanos) * 100
        suma += (vi - si) ** 2
    lsq = math.sqrt(0.5 * suma)
    return round(lsq, 2)

# ===============================
# FUNCIONES CYL ESPECÍFICAS
# ===============================

def ajustar_escenario_cyl(base_cyl):
    """
    Ajuste de intención de voto para CyL según variables estructurales del sidebar.
    """
    ajuste = base_cyl.copy()
    # Despoblación → beneficia PP (gestión percibida como suya), penaliza PSOE
    ajuste["PP"] += (factor_despoblacion - 50) * 0.015
    ajuste["PSOE"] -= (factor_despoblacion - 50) * 0.01
    # Cuestión leonesa → beneficia UPL, perjudica ligeramente PP y PSOE
    ajuste["UPL"] += (factor_cuestion_leonesa - 50) * 0.03
    ajuste["PP"] -= (factor_cuestion_leonesa - 50) * 0.008
    # Sanidad CyL → penaliza PP (gestión autonómica), beneficia PSOE y SUMAR
    ajuste["PP"] -= (factor_sanidad_cyl - 50) * 0.02
    ajuste["PSOE"] += (factor_sanidad_cyl - 50) * 0.012
    ajuste["SUMAR"] += (factor_sanidad_cyl - 50) * 0.008
    return normalizar(ajuste)

def ajustar_provincial_cyl(base, provincia_cyl):
    """
    Ajustes territoriales específicos por provincia de CyL.
    """
    datos = base.copy()
    # León: mayor peso UPL y voto leonesista
    if provincia_cyl == "León":
        datos["UPL"] += 4.5
        datos["PP"] -= 1.5
    # Salamanca: PP muy fuerte históricamente
    if provincia_cyl == "Salamanca":
        datos["PP"] += 2.5
        datos["PSOE"] -= 1.0
    # Valladolid: más urbano, PSOE más competitivo
    if provincia_cyl == "Valladolid":
        datos["PSOE"] += 1.5
        datos["SUMAR"] += 1.0
        datos["PP"] -= 1.0
    # Ávila: Por Ávila con presencia local
    if provincia_cyl == "Ávila":
        datos["Por Ávila"] += 2.5
    # Soria: muy pequeña, PP histórico
    if provincia_cyl == "Soria":
        datos["PP"] += 3.0
    # Burgos: equilibrado
    if provincia_cyl == "Burgos":
        datos["PP"] += 1.0
        datos["PSOE"] += 0.5
    # Palencia, Segovia, Zamora: perfil rural-conservador
    if provincia_cyl in ["Palencia", "Segovia", "Zamora"]:
        datos["PP"] += 1.5
        datos["VOX"] += 0.5

    # Ruido estadístico calibrado a fiabilidad
    ruido = (100 - fiabilidad) / 100
    for p in datos:
        datos[p] += random.uniform(-ruido * 2.5, ruido * 2.5)
        datos[p] = max(0, datos[p])  # no negativos

    return normalizar(datos)

def aplicar_umbral_cyl(votos, umbral_pct):
    """
    Filtra partidos por debajo del umbral electoral (3% en CyL autonómicas).
    Los votos de partidos eliminados se redistribuyen proporcionalmente.
    """
    votos_filtrados = {p: v for p, v in votos.items() if v >= umbral_pct}
    return normalizar(votos_filtrados)

def calcular_cyl():
    """
    Cálculo completo del parlamento autonómico de CyL.
    Retorna escaños totales, datos provinciales y métricas.
    """
    fecha = str(date.today())
    base_esc = ajustar_escenario_cyl(BASE_CYL)
    escanos_totales = {p: 0 for p in PARTIDOS_CYL}
    datos_prov = []

    for prov, num_esc in ESCANOS_CYL.items():
        votos_raw = ajustar_provincial_cyl(base_esc, prov)
        # Aplicar umbral electoral
        votos = aplicar_umbral_cyl(votos_raw, umbral_cyl)
        reparto = dhondt(votos, num_esc)
        for p in PARTIDOS_CYL:
            escanos_totales[p] = escanos_totales.get(p, 0) + reparto.get(p, 0)

        datos_prov.append({
            "Provincia": prov,
            "Escaños_total": num_esc,
            "Reparto": reparto,
            "Votos": votos,
            "Votos_raw": votos_raw
        })

        # Guardar histórico CyL
        escenario_label = f"Desp:{factor_despoblacion}_Leon:{factor_cuestion_leonesa}_San:{factor_sanidad_cyl}"
        for p in PARTIDOS_CYL:
            if not ((df_hist_cyl["Fecha"] == fecha) & (df_hist_cyl["Provincia"] == prov) &
                    (df_hist_cyl["Partido"] == p) & (df_hist_cyl["Escenario"] == escenario_label)).any():
                df_hist_cyl.loc[len(df_hist_cyl)] = [fecha, prov, p,
                                                      votos.get(p, 0), reparto.get(p, 0), escenario_label]

    df_hist_cyl.to_csv(HIST_CYL_FILE, index=False)
    return escanos_totales, datos_prov

# ===============================
# CÁLCULO NACIONAL (original preservado)
# ===============================
def calcular():
    fecha = str(date.today())
    base_esc = ajustar_escenario(BASE_NACIONAL)
    escanos_totales = {p: 0 for p in PARTIDOS}
    datos_prov = []
    for prov in PROVINCIAS:
        votos = ajustar_territorial(base_esc, prov)
        escanos = ESCANOS[prov]
        reparto = dhondt(votos, escanos)
        for p in PARTIDOS:
            if not ((df_hist["Fecha"] == fecha) & (df_hist["Provincia"] == prov) &
                    (df_hist["Partido"] == p)).any():
                df_hist.loc[len(df_hist)] = [fecha, prov, p, votos[p], reparto[p]]
        for p in PARTIDOS:
            escanos_totales[p] += reparto[p]
        datos_prov.append({"Provincia": prov, "Escaños": escanos, "Reparto": reparto, "Votos": votos})
    total = sum(escanos_totales.values())
    if total != 350:
        diff = 350 - total
        mayor = max(escanos_totales, key=escanos_totales.get)
        escanos_totales[mayor] += diff
    df_hist.to_csv(HIST_FILE, index=False)
    return escanos_totales, datos_prov

# ===============================
# EJECUCIÓN
# ===============================
escanos_totales, datos_prov = calcular()
escanos_cyl, datos_prov_cyl = calcular_cyl()

# Métricas nacionales
votos_nacionales_agregados = {}
for dp in datos_prov:
    for p, v in dp["Votos"].items():
        votos_nacionales_agregados[p] = votos_nacionales_agregados.get(p, 0) + v
votos_nacionales_avg = {p: v / len(datos_prov) for p, v in votos_nacionales_agregados.items()}

polarizacion_nac = calcular_indice_polarizacion(votos_nacionales_avg)
nep_nac = calcular_indice_fragmentacion(escanos_totales)
lsq_nac = calcular_sesgo_sistema(votos_nacionales_avg, escanos_totales)
gobernabilidad_nac = calcular_indice_gobernabilidad(escanos_totales)

# Métricas CyL
votos_cyl_agregados = {}
for dp in datos_prov_cyl:
    for p, v in dp["Votos"].items():
        votos_cyl_agregados[p] = votos_cyl_agregados.get(p, 0) + v
votos_cyl_avg = {p: v / len(datos_prov_cyl) for p, v in votos_cyl_agregados.items()}

polarizacion_cyl = calcular_indice_polarizacion(votos_cyl_avg)
nep_cyl = calcular_indice_fragmentacion(escanos_cyl)
lsq_cyl = calcular_sesgo_sistema(votos_cyl_avg, escanos_cyl)

# ===============================
# TABS
# ===============================

# ===============================
# ANDALUCÍA — DATOS ELECTORALES
# ===============================
# Composición actual Parlamento de Andalucía (elecciones 2022, 109 diputados)
AND_COMPOSICION_ACTUAL = {
    "PP":    58,   # mayoría absoluta histórica (Moreno Bonilla)
    "PSOE":  30,
    "VOX":   14,
    "Por Andalucía": 5,   # confluencia IU+Podemos+Más País
    "Cs":     2,          # en liquidación política
    "OTROS":  0
}

PARTIDOS_AND = ["PP", "PSOE", "VOX", "Por Andalucía", "OTROS"]
COLORES_AND = {
    "PP":            "#1f77b4",
    "PSOE":          "#d62728",
    "VOX":           "#2ca02c",
    "Por Andalucía": "#9467bd",
    "OTROS":         "#c7c7c7"
}

# Intención de voto base en Andalucía (estimación estructural 2026)
# PP consolida hegemonía; PSOE recupera algo; VOX erosiona; Cs desaparece
BASE_AND = {
    "PP":            38.0,   # fortaleza del gobierno autonómico
    "PSOE":          26.0,   # recuperación lenta post-2022
    "VOX":           10.5,   # bajada tras máximos
    "Por Andalucía":  8.0,   # estabilización SUMAR/IU
    "OTROS":         17.5    # indecisos, abstención, nulos, Cs residual
}

# Escaños por provincia — Parlamento de Andalucía (109 diputados)
ESCANOS_AND = {
    "Almería":  12,
    "Cádiz":    15,
    "Córdoba":  12,
    "Granada":  13,
    "Huelva":    9,
    "Jaén":     10,
    "Málaga":   17,
    "Sevilla":  21
}
TOTAL_AND = sum(ESCANOS_AND.values())  # 109

# ===============================
# SIDEBAR — VARIABLES ANDALUCÍA
# ===============================
# (añadir en el bloque sidebar existente)

# ===============================
# FUNCIONES ANDALUCÍA
# ===============================

def ajustar_escenario_and(base_and,
                           f_desempleo, f_vivienda_and,
                           f_agua, f_rural_urbano):
    """
    Ajuste de intención de voto para Andalucía según variables estructurales.
    """
    ajuste = base_and.copy()

    # Desempleo estructural → penaliza PP (gobierno), beneficia PSOE y Por Andalucía
    ajuste["PP"]            -= (f_desempleo - 50) * 0.018
    ajuste["PSOE"]          += (f_desempleo - 50) * 0.010
    ajuste["Por Andalucía"] += (f_desempleo - 50) * 0.008

    # Vivienda/turismo → tensión urbana costera → beneficia Por Andalucía, penaliza PP
    ajuste["PP"]            -= (f_vivienda_and - 50) * 0.015
    ajuste["Por Andalucía"] += (f_vivienda_and - 50) * 0.012
    ajuste["PSOE"]          += (f_vivienda_and - 50) * 0.006

    # Agua y sequía → moviliza voto rural conservador (PP y VOX)
    ajuste["PP"]  += (f_agua - 50) * 0.010
    ajuste["VOX"] += (f_agua - 50) * 0.008

    # Rural vs urbano → mayor ruralidad → PP y VOX más fuertes
    ajuste["PP"]            += (f_rural_urbano - 50) * 0.012
    ajuste["VOX"]           += (f_rural_urbano - 50) * 0.006
    ajuste["Por Andalucía"] -= (f_rural_urbano - 50) * 0.010

    return normalizar(ajuste)


def ajustar_provincial_and(base, provincia_and):
    """
    Ajustes territoriales específicos por provincia andaluza.
    Perfil socioeconómico y electoral histórico de cada provincia.
    """
    datos = base.copy()

    # Sevilla: capital política, PSOE históricamente fuerte, más urbano
    if provincia_and == "Sevilla":
        datos["PSOE"]          += 2.5
        datos["Por Andalucía"] += 1.5
        datos["PP"]            -= 1.5

    # Málaga: PP muy fuerte, turismo, clase media-alta costera
    if provincia_and == "Málaga":
        datos["PP"]  += 3.5
        datos["VOX"] += 1.0
        datos["PSOE"] -= 1.5

    # Cádiz: bastión histórico PSOE, industria naval, Podemos fuerte
    if provincia_and == "Cádiz":
        datos["PSOE"]          += 2.0
        datos["Por Andalucía"] += 2.5
        datos["PP"]            -= 2.0

    # Almería: PP muy fuerte, agricultura intensiva, inmigración como variable
    if provincia_and == "Almería":
        datos["PP"]  += 4.0
        datos["VOX"] += 2.0
        datos["PSOE"] -= 1.5

    # Jaén: olivar, desempleo alto, PSOE tradicional, interior profundo
    if provincia_and == "Jaén":
        datos["PSOE"] += 1.5
        datos["PP"]   -= 1.0
        datos["VOX"]  += 1.0

    # Granada: universidad, turismo cultural, equilibrado
    if provincia_and == "Granada":
        datos["PP"]            += 1.0
        datos["Por Andalucía"] += 1.0

    # Huelva: minería, fresa, PSOE tradicional, rural
    if provincia_and == "Huelva":
        datos["PSOE"] += 1.5
        datos["PP"]   -= 0.5

    # Córdoba: IU históricamente fuerte, industrial, equilibrado
    if provincia_and == "Córdoba":
        datos["Por Andalucía"] += 2.0
        datos["PSOE"]          += 1.0
        datos["PP"]            -= 1.0

    # Ruido estadístico calibrado a fiabilidad global
    ruido = (100 - fiabilidad) / 100
    for p in datos:
        datos[p] += random.uniform(-ruido * 2.5, ruido * 2.5)
        datos[p] = max(0.0, datos[p])

    return normalizar(datos)


def aplicar_umbral_and(votos, umbral_pct):
    """Filtra partidos bajo umbral y redistribuye proporcionalmente."""
    votos_filtrados = {p: v for p, v in votos.items() if v >= umbral_pct}
    return normalizar(votos_filtrados)


def calcular_and(f_desempleo, f_vivienda_and, f_agua, f_rural_urbano, umbral_and):
    """
    Cálculo completo del Parlamento de Andalucía.
    Retorna escaños totales y datos provinciales.
    """
    fecha = str(date.today())
    base_esc = ajustar_escenario_and(
        BASE_AND, f_desempleo, f_vivienda_and, f_agua, f_rural_urbano
    )
    escanos_totales = {p: 0 for p in PARTIDOS_AND}
    datos_prov = []

    for prov, num_esc in ESCANOS_AND.items():
        votos_raw = ajustar_provincial_and(base_esc.copy(), prov)
        votos     = aplicar_umbral_and(votos_raw, umbral_and)
        reparto   = dhondt(votos, num_esc)

        for p in PARTIDOS_AND:
            escanos_totales[p] = escanos_totales.get(p, 0) + reparto.get(p, 0)

        datos_prov.append({
            "Provincia":    prov,
            "Escaños_total": num_esc,
            "Reparto":      reparto,
            "Votos":        votos,
            "Votos_raw":    votos_raw
        })

    return escanos_totales, datos_prov


# ===============================
# TAB ANDALUCÍA — RENDERIZADO
# ===============================
# INSTRUCCIÓN: sustituir la línea de declaración de tabs por:
#

# ===============================
# GALICIA — DATOS ELECTORALES
# ===============================
# Composición actual Parlamento de Galicia (elecciones febrero 2024, 76 escaños)
GAL_COMPOSICION_ACTUAL = {
    "PP":                    40,   # mayoría absoluta Rueda
    "BNG":                   19,   # máximo histórico
    "PSOE":                   9,
    "Sumar":                  5,
    "VOX":                    2,
    "Democracia Ourensana":   1,   # partido local Ourense
    "OTROS":                  0
}

PARTIDOS_GAL = ["PP", "BNG", "PSOE", "Sumar", "VOX", "DO", "OTROS"]
COLORES_GAL = {
    "PP":    "#1f77b4",
    "BNG":   "#2ca02c",   # verde nacionalista
    "PSOE":  "#d62728",
    "Sumar": "#9467bd",
    "VOX":   "#17becf",
    "DO":    "#e67e22",   # Democracia Ourensana
    "OTROS": "#c7c7c7"
}

# Intención de voto base Galicia 2026 (estimación estructural)
# PP consolida; BNG en alza estructural; PSOE débil; Sumar estable
BASE_GAL = {
    "PP":    38.0,   # hegemonía histórica reforzada
    "BNG":   24.0,   # crecimiento estructural, Ana Pontón
    "PSOE":  13.0,   # mínimos históricos en Galicia
    "Sumar":  7.0,
    "VOX":    4.5,
    "DO":     2.0,   # solo relevante en Ourense
    "OTROS": 11.5
}

# Escaños por circunscripción — Parlamento de Galicia (76 diputados)
ESCANOS_GAL = {
    "A Coruña":   24,
    "Lugo":       15,
    "Ourense":    14,
    "Pontevedra": 23
}
TOTAL_GAL = sum(ESCANOS_GAL.values())  # 76

# ===============================
# EUSKADI — PARLAMENTO VASCO
# ===============================
PARTIDOS_EUS = ["PNV", "EH Bildu", "PSE-EE", "PP", "Sumar", "VOX", "OTROS"]
COLORES_EUS = {"PNV":"#cc0000","EH Bildu":"#4CAF50","PSE-EE":"#E53935","PP":"#1565C0","Sumar":"#9C27B0","VOX":"#00BCD4","OTROS":"#c7c7c7"}
REAL_EUS_2024 = {"PNV":27,"EH Bildu":27,"PSE-EE":12,"PP":7,"Sumar":1,"VOX":1,"OTROS":0}
BASE_EUS = {"PNV":34.5,"EH Bildu":32.0,"PSE-EE":14.0,"PP":9.5,"Sumar":3.0,"VOX":2.5,"OTROS":4.5}
ESCANOS_EUS = {"Álava":25,"Bizkaia":25,"Gipuzkoa":25}
TOTAL_EUS = sum(ESCANOS_EUS.values())  # 75

def ajustar_escenario_eus(base_eus, f_indep, f_izq, f_econ, f_conc):
    a = base_eus.copy()
    a["PNV"]      += (f_indep-50)*0.012; a["EH Bildu"] += (f_indep-50)*0.016
    a["PSE-EE"]   -= (f_indep-50)*0.010; a["PP"]       -= (f_indep-50)*0.008
    a["EH Bildu"] += (f_izq-50)*0.020;   a["PNV"]      -= (f_izq-50)*0.015
    a["PSE-EE"]   -= (f_izq-50)*0.005
    a["PNV"]      += (f_econ-50)*0.010;  a["PP"]       += (f_econ-50)*0.006
    a["EH Bildu"] -= (f_econ-50)*0.006
    a["PNV"]      += (f_conc-50)*0.010;  a["EH Bildu"] += (f_conc-50)*0.008
    a["PP"]       -= (f_conc-50)*0.008
    for p in a: a[p] = max(0.0, a[p])
    return normalizar(a)

def ajustar_territorial_eus(base, terr):
    d = base.copy()
    if terr == "Álava":
        d["EH Bildu"]+=2.5; d["PP"]+=3.5; d["PNV"]-=2.5; d["VOX"]+=1.5
    if terr == "Bizkaia":
        d["PNV"]+=4.0; d["EH Bildu"]-=1.5; d["PP"]-=1.0
    if terr == "Gipuzkoa":
        d["EH Bildu"]+=5.0; d["PNV"]-=1.5; d["PSE-EE"]-=1.0
    ruido = (100-fiabilidad)/100
    for p in d:
        d[p] += random.uniform(-ruido*2.5, ruido*2.5)
        d[p] = max(0.0, d[p])
    return normalizar(d)

def aplicar_umbral_eus(votos, umbral):
    return normalizar({p:v for p,v in votos.items() if v>=umbral})

def calcular_eus(f_indep, f_izq, f_econ, f_conc, umbral_eus):
    base = ajustar_escenario_eus(BASE_EUS, f_indep, f_izq, f_econ, f_conc)
    esc = {p:0 for p in PARTIDOS_EUS}
    terrs = []
    for terr, n in ESCANOS_EUS.items():
        vr = ajustar_territorial_eus(base.copy(), terr)
        v  = aplicar_umbral_eus(vr, umbral_eus)
        r  = dhondt(v, n)
        for p in PARTIDOS_EUS: esc[p] = esc.get(p,0) + r.get(p,0)
        terrs.append({"Territorio":terr,"Escaños_total":n,"Reparto":r,"Votos":v,"Votos_raw":vr})
    return esc, terrs

def render_tab_euskadi(esc, terrs, pol, nep, lsq, f_indep, f_izq, f_econ, f_conc):
    ma = (TOTAL_EUS//2)+1
    st.header("🏴󠁥󠁳󠁰󠁶󠁿 Euskadi — Laboratorio Electoral Autonómico")
    st.markdown(f"**3 territorios históricos** | **{TOTAL_EUS} diputados** | **Mayoría absoluta: {ma}** | D'Hondt | Barrera 3%")
    st.markdown("---")
    col1,col2,col3,col4 = st.columns(4)
    pf = max(esc, key=esc.get)
    col1.metric("Primera fuerza", f"{pf} ({esc[pf]})")
    col2.metric("Mayoría absoluta", ma)
    col3.metric("Polarización HHI", f"{pol:.3f}")
    col4.metric("Diputados totales", TOTAL_EUS)

    st.subheader("🏛️ Hemiciclo Parlamento Vasco")
    df_h = pd.DataFrame([{"Partido":p,"Escaños":v} for p,v in esc.items() if v>0]).sort_values("Escaños",ascending=False)
    fig_h = px.bar(df_h, x="Partido", y="Escaños", color="Partido",
                   color_discrete_map=COLORES_EUS, text="Escaños",
                   title=f"Parlamento Vasco — {TOTAL_EUS} diputados")
    fig_h.update_traces(textposition="outside")
    fig_h.update_layout(showlegend=False, height=400)
    st.plotly_chart(fig_h, use_container_width=True)

    st.subheader("⚖️ Análisis de bloques")
    b_nac = esc.get("PNV",0)+esc.get("EH Bildu",0)
    b_gov = esc.get("PNV",0)+esc.get("PSE-EE",0)
    b_der = esc.get("PP",0)+esc.get("VOX",0)
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Bloque nac. PNV+Bildu", b_nac, delta="✅ MA" if b_nac>=ma else f"{b_nac-ma}")
    c2.metric("Coalición PNV+PSE", b_gov, delta="✅ MA" if b_gov>=ma else f"{b_gov-ma}")
    c3.metric("Bloque PP+VOX", b_der)
    c4.metric("NEP / LSq", f"{nep:.2f} / {lsq:.2f}")

    st.subheader("🗺️ Resultados por territorio histórico")
    cols = st.columns(3)
    for i, d in enumerate(terrs):
        with cols[i]:
            st.markdown(f"**{d['Territorio']}** ({d['Escaños_total']} esc.)")
            df_t = pd.DataFrame([{"Partido":p,"Escaños":v} for p,v in d["Reparto"].items() if v>0]).sort_values("Escaños",ascending=False)
            fig_t = px.bar(df_t, x="Partido", y="Escaños", color="Partido",
                           color_discrete_map=COLORES_EUS, text="Escaños", height=280)
            fig_t.update_traces(textposition="outside")
            fig_t.update_layout(showlegend=False, margin=dict(t=20,b=20,l=10,r=10))
            st.plotly_chart(fig_t, use_container_width=True)

    st.subheader("🔍 Retrovalidación — Resultado real 21A 2024")
    cr, cs = st.columns(2)
    with cr:
        st.markdown("**Real 2024**")
        dr = pd.DataFrame([{"Partido":p,"Escaños":v} for p,v in REAL_EUS_2024.items() if v>0]).sort_values("Escaños",ascending=False)
        st.dataframe(dr, use_container_width=True, hide_index=True)
        st.plotly_chart(px.pie(dr, names="Partido", values="Escaños", color="Partido",
                               color_discrete_map=COLORES_EUS, title="Real 2024"), use_container_width=True)
    with cs:
        st.markdown("**Simulación 2026**")
        ds = pd.DataFrame([{"Partido":p,"Escaños":v} for p,v in esc.items() if v>0]).sort_values("Escaños",ascending=False)
        st.dataframe(ds, use_container_width=True, hide_index=True)
        st.plotly_chart(px.pie(ds, names="Partido", values="Escaños", color="Partido",
                               color_discrete_map=COLORES_EUS, title="Simulación 2026"), use_container_width=True)

    st.markdown("**Δ Simulación vs Real 2024**")
    df_e = pd.DataFrame([{"Partido":p,"Real 2024":REAL_EUS_2024.get(p,0),"Simulado":esc.get(p,0),"Delta":esc.get(p,0)-REAL_EUS_2024.get(p,0)} for p in PARTIDOS_EUS])
    st.dataframe(df_e, use_container_width=True, hide_index=True)
    st.caption("Fuentes: Sociómetro Vasco feb-2025, EITB, BOPV. D'Hondt, barrera 3% por territorio.")


# ===============================
# FUNCIONES GALICIA
# ===============================


def ajustar_escenario_gal(base_gal,
                           f_despoblacion_gal, f_bng_urbano,
                           f_pesca, f_autogobierno):
    """
    Ajuste estructural para Galicia.
    Variables: despoblación interior, ascenso urbano BNG,
               sector pesquero, reivindicación autogobierno.
    """
    ajuste = base_gal.copy()

    # Despoblación interior → PP se beneficia en rural profundo
    ajuste["PP"]  += (f_despoblacion_gal - 50) * 0.015
    ajuste["BNG"] -= (f_despoblacion_gal - 50) * 0.008

    # BNG urbano → Vigo/Coruña, jóvenes, feminismo, cultura galega
    ajuste["BNG"]   += (f_bng_urbano - 50) * 0.020
    ajuste["PSOE"]  -= (f_bng_urbano - 50) * 0.010
    ajuste["Sumar"] -= (f_bng_urbano - 50) * 0.005

    # Pesca → moviliza voto costero conservador (PP) y nacionalista (BNG)
    ajuste["PP"]  += (f_pesca - 50) * 0.008
    ajuste["BNG"] += (f_pesca - 50) * 0.006

    # Autogobierno → BNG se beneficia claramente
    ajuste["BNG"] += (f_autogobierno - 50) * 0.018
    ajuste["PP"]  -= (f_autogobierno - 50) * 0.010

    for p in ajuste:
        ajuste[p] = max(0.0, ajuste[p])
    return normalizar(ajuste)


def ajustar_provincial_gal(base, provincia_gal):
    """Ajustes por perfil histórico-electoral de cada provincia gallega."""
    datos = base.copy()

    # A Coruña: más urbana, BNG fuerte (Ferrol, Coruña ciudad), PSOE competitivo
    if provincia_gal == "A Coruña":
        datos["BNG"]  += 3.0
        datos["PSOE"] += 1.5
        datos["PP"]   -= 2.0

    # Pontevedra: Vigo — BNG máximo, industria, jóvenes; Pontevedra ciudad más equilibrada
    if provincia_gal == "Pontevedra":
        datos["BNG"]  += 4.0
        datos["PP"]   -= 2.5
        datos["PSOE"] += 1.0

    # Lugo: rural profundo, PP muy fuerte, envejecimiento extremo
    if provincia_gal == "Lugo":
        datos["PP"]   += 4.0
        datos["BNG"]  -= 2.0
        datos["PSOE"] -= 1.0

    # Ourense: PP+DO, caciquismo histórico, más conservador
    if provincia_gal == "Ourense":
        datos["PP"]  += 3.0
        datos["DO"]  += 4.5   # Democracia Ourensana — Gonzalo Pérez Jácome
        datos["BNG"] -= 1.5
        datos["VOX"] += 1.0

    ruido = (100 - fiabilidad) / 100
    for p in datos:
        datos[p] += random.uniform(-ruido * 2.5, ruido * 2.5)
        datos[p] = max(0.0, datos[p])
    return normalizar(datos)


def aplicar_umbral_gal(votos, umbral_pct):
    votos_filtrados = {p: v for p, v in votos.items() if v >= umbral_pct}
    return normalizar(votos_filtrados)


def calcular_gal(f_despoblacion_gal, f_bng_urbano,
                  f_pesca, f_autogobierno, umbral_gal):
    """Cálculo completo del Parlamento de Galicia."""
    base_esc  = ajustar_escenario_gal(
        BASE_GAL, f_despoblacion_gal, f_bng_urbano, f_pesca, f_autogobierno
    )
    escanos_totales = {p: 0 for p in PARTIDOS_GAL}
    datos_prov = []

    for prov, num_esc in ESCANOS_GAL.items():
        votos_raw = ajustar_provincial_gal(base_esc.copy(), prov)
        votos     = aplicar_umbral_gal(votos_raw, umbral_gal)
        reparto   = dhondt(votos, num_esc)

        for p in PARTIDOS_GAL:
            escanos_totales[p] = escanos_totales.get(p, 0) + reparto.get(p, 0)

        datos_prov.append({
            "Provincia":     prov,
            "Escaños_total": num_esc,
            "Reparto":       reparto,
            "Votos":         votos,
            "Votos_raw":     votos_raw
        })

    return escanos_totales, datos_prov


# ===============================
# RENDER TAB GALICIA
# ===============================

def render_tab_galicia(escanos_gal, datos_prov_gal,
                        polarizacion_gal, nep_gal, lsq_gal,
                        f_despoblacion_gal, f_bng_urbano,
                        f_pesca, f_autogobierno):

    st.header("🌿 Galicia — Laboratorio Electoral Autonómico")
    st.markdown("""
    > **Contexto:** Galicia es el feudo histórico del PP pero vive una transformación
    > estructural con el ascenso del BNG como alternativa nacional-progresista.
    > Las elecciones de febrero 2024 consolidaron este bipartidismo PP-BNG,
    > dejando al PSOE en mínimos históricos.
    """)

    ma_gal = (TOTAL_GAL // 2) + 1  # 39

    # ---- KPIs
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("NEP Galicia", nep_gal,
                help="Número Efectivo de Partidos")
    col2.metric("Polarización", f"{polarizacion_gal:.3f}")
    col3.metric("Gallagher (LSq)", f"{lsq_gal:.1f}")
    col4.metric("Diputados totales", TOTAL_GAL)

    st.markdown("---")

    # ---- COMPOSICIÓN ACTUAL vs PROYECCIÓN
    st.subheader("📊 Composición Real 2024 vs. Proyección Simulada")
    col_act, col_sim = st.columns(2)

    with col_act:
        st.markdown("**Parlamento de Galicia 2024 (Real)**")
        df_actual = pd.DataFrame({
            "Partido":    list(GAL_COMPOSICION_ACTUAL.keys()),
            "Diputados":  list(GAL_COMPOSICION_ACTUAL.values())
        })
        df_actual = df_actual[df_actual["Diputados"] > 0]
        fig_act = px.bar(df_actual, x="Partido", y="Diputados",
                         color="Partido", color_discrete_map=COLORES_GAL,
                         text="Diputados", title="Resultado Real 2024")
        fig_act.update_traces(textposition="outside")
        fig_act.add_hline(y=ma_gal, line_dash="dash", line_color="red",
                          annotation_text=f"Mayoría Absoluta ({ma_gal})")
        st.plotly_chart(fig_act, width='stretch')
        pp_r = GAL_COMPOSICION_ACTUAL["PP"]
        st.success(f"**Gobierno actual:** PP ({pp_r}) — mayoría absoluta  |  MA: {ma_gal}")

    with col_sim:
        st.markdown("**Proyección Simulada (Escenario Actual)**")
        df_sim = pd.DataFrame({
            "Partido":   list(escanos_gal.keys()),
            "Diputados": list(escanos_gal.values())
        })
        df_sim = df_sim[df_sim["Diputados"] > 0].sort_values("Diputados", ascending=False)
        fig_sim = px.bar(df_sim, x="Partido", y="Diputados",
                         color="Partido", color_discrete_map=COLORES_GAL,
                         text="Diputados", title="Simulación Actual")
        fig_sim.update_traces(textposition="outside")
        fig_sim.add_hline(y=ma_gal, line_dash="dash", line_color="red",
                          annotation_text=f"Mayoría Absoluta ({ma_gal})")
        st.plotly_chart(fig_sim, width='stretch')
        pp_sim_v = escanos_gal.get("PP", 0)
        bng_sim  = escanos_gal.get("BNG", 0)
        estado   = "✅ Mayoría absoluta" if pp_sim_v >= ma_gal else f"❌ PP necesita {ma_gal - pp_sim_v} más"
        st.info(f"**PP:** {pp_sim_v}  |  **BNG:** {bng_sim}  |  {estado}")

    # ---- DELTA
    st.subheader("🔄 Variación Estimada respecto a 2024")
    delta_data = []
    mapa_actual = {"PP":"PP","BNG":"BNG","PSOE":"PSOE",
                   "Sumar":"Sumar","VOX":"VOX",
                   "Democracia Ourensana":"DO","OTROS":"OTROS"}
    for p in PARTIDOS_GAL:
        clave_actual = {v: k for k, v in mapa_actual.items()}.get(p, p)
        actual_v   = GAL_COMPOSICION_ACTUAL.get(clave_actual,
                     GAL_COMPOSICION_ACTUAL.get(p, 0))
        simulado_v = escanos_gal.get(p, 0)
        delta_data.append({
            "Partido": p,
            "2024 (Real)": actual_v,
            "Simulado": simulado_v,
            "Δ Cambio": simulado_v - actual_v
        })
    df_delta = pd.DataFrame(delta_data)
    fig_delta = px.bar(df_delta, x="Partido", y="Δ Cambio",
                       color="Δ Cambio", color_continuous_scale="RdYlGn",
                       title="Variación respecto a 2024", text="Δ Cambio")
    fig_delta.add_hline(y=0, line_color="black", line_width=1)
    fig_delta.update_traces(textposition="outside")
    st.plotly_chart(fig_delta, width='stretch')

    # ---- DESGLOSE PROVINCIAL
    st.subheader("🗺️ Desglose Provincial Galicia")
    prov_sel = st.selectbox("Provincia gallega", list(ESCANOS_GAL.keys()),
                             key="selectbox_gal")
    dp_gal = next(d for d in datos_prov_gal if d["Provincia"] == prov_sel)

    col_pv, col_pe = st.columns(2)
    with col_pv:
        df_v = pd.DataFrame({
            "Partido":  list(dp_gal["Votos"].keys()),
            "Voto (%)": list(dp_gal["Votos"].values())
        })
        df_v = df_v[df_v["Voto (%)"] > 0.5].sort_values("Voto (%)", ascending=True)
        fig_v = go.Figure(go.Bar(
            x=df_v["Voto (%)"], y=df_v["Partido"], orientation="h",
            marker_color=[COLORES_GAL.get(p, "#999") for p in df_v["Partido"]],
            text=df_v["Voto (%)"].round(1), textposition="outside"
        ))
        fig_v.update_layout(height=300, xaxis_title="% Voto",
                            title=f"Intención de Voto — {prov_sel}")
        st.plotly_chart(fig_v, width='stretch')

    with col_pe:
        rep = {p: v for p, v in dp_gal["Reparto"].items() if v > 0}
        if rep:
            fig_e = px.pie(values=list(rep.values()), names=list(rep.keys()),
                           color=list(rep.keys()),
                           color_discrete_map=COLORES_GAL, hole=0.4,
                           title=f"D'Hondt — {prov_sel} ({ESCANOS_GAL[prov_sel]} diputados)")
            st.plotly_chart(fig_e, width='stretch')

    # ---- COALICIONES
    st.subheader("🤝 Análisis de Coaliciones — Parlamento de Galicia")
    pp_s    = escanos_gal.get("PP", 0)
    bng_s   = escanos_gal.get("BNG", 0)
    psoe_s  = escanos_gal.get("PSOE", 0)
    sumar_s = escanos_gal.get("Sumar", 0)
    vox_s   = escanos_gal.get("VOX", 0)
    do_s    = escanos_gal.get("DO", 0)

    coaliciones = {
        "PP solo":                pp_s,
        "PP + VOX":               pp_s + vox_s,
        "PP + DO":                pp_s + do_s,
        "BNG solo":               bng_s,
        "BNG + PSOE + Sumar":     bng_s + psoe_s + sumar_s,
        "BNG + PSOE + Sumar + DO":bng_s + psoe_s + sumar_s + do_s,
    }
    df_coal = pd.DataFrame({
        "Coalición": list(coaliciones.keys()),
        "Diputados": list(coaliciones.values())
    })
    df_coal["¿Mayoría?"] = df_coal["Diputados"].apply(
        lambda x: "✅ Mayoría" if x >= ma_gal else f"❌ Faltan {ma_gal - x}"
    )
    fig_coal = px.bar(df_coal, x="Coalición", y="Diputados",
                      text="Diputados", color="Diputados",
                      color_continuous_scale="Greens",
                      title=f"Escenarios de Coalición (MA: {ma_gal})")
    fig_coal.add_hline(y=ma_gal, line_dash="dash", line_color="red")
    fig_coal.update_traces(textposition="outside")
    st.plotly_chart(fig_coal, width='stretch')
    st.dataframe(df_coal, width='stretch')

    # ---- RADAR
    st.subheader("📡 Variables Estructurales Galicia")
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        cat_gal = ["Despoblación", "BNG Urbano", "Pesca", "Autogobierno", "Fiabilidad"]
        val_gal = [f_despoblacion_gal, f_bng_urbano, f_pesca, f_autogobierno, fiabilidad]
        fig_rad = go.Figure(go.Scatterpolar(
            r=val_gal, theta=cat_gal, fill="toself",
            line_color="#2ca02c", name="Galicia"
        ))
        fig_rad.update_layout(
            polar=dict(radialaxis=dict(range=[0, 100])),
            title="Perfil de Riesgo Electoral Galicia"
        )
        st.plotly_chart(fig_rad, width='stretch')

    with col_r2:
        votos_matrix = []
        for dp in datos_prov_gal:
            row = {"Provincia": dp["Provincia"]}
            for p in PARTIDOS_GAL:
                row[p] = round(dp["Votos"].get(p, 0), 1)
            votos_matrix.append(row)
        df_heat = pd.DataFrame(votos_matrix).set_index("Provincia")
        fig_heat = px.imshow(df_heat, color_continuous_scale="Greens",
                             title="% Intención de Voto por Provincia",
                             text_auto=True)
        st.plotly_chart(fig_heat, width='stretch')

    # ---- NOTA METODOLÓGICA
    with st.expander("📋 Nota Metodológica — Módulo Galicia"):
        st.markdown(f"""
**Circunscripciones:** 4 provincias | **Total diputados:** {TOTAL_GAL} | **Mayoría absoluta:** {ma_gal}  
**Umbral electoral:** 5% por circunscripción (Ley Electoral de Galicia)  
**Base:** Resultado real febrero 2024 con ajuste estructural 2026  

**Variables estructurales específicas:**
- **Despoblación:** Lugo y Ourense pierden población sistemáticamente. Refuerza voto conservador rural PP.
- **BNG Urbano:** Ascenso en Vigo, Coruña, Santiago. Jóvenes, feminismo, cultura galega. Variable clave de tendencia.
- **Pesca:** Sector estratégico en costa atlántica. Moviliza tanto PP (gestión) como BNG (soberanía).
- **Autogobierno:** Reivindicación de mayor autogobierno → beneficia BNG directamente.

**Perfiles provinciales:**
- **A Coruña:** BNG fuerte en ciudad y Ferrol. PP sólido en rural. PSOE residual.
- **Pontevedra:** Vigo es el bastión del BNG. Mayor dinamismo demográfico y económico.
- **Lugo:** PP hegemónico. Rural extremo. Envejecimiento más acusado de Galicia.
- **Ourense:** PP+DO (Jácome). Caciquismo histórico. BNG débil. VOX con presencia.

**Limitaciones:**
- DO (Democracia Ourensana) con alta volatilidad — dependiente de figura de Jácome
- BNG en crecimiento estructural difícil de modelar con datos históricos
- Umbral 5% elimina partidos pequeños con presencia real en alguna circunscripción
        """)


# ===============================
# MADRID — DATOS ELECTORALES
# ===============================
# Composición actual Asamblea de Madrid (elecciones mayo 2023, 135 escaños)
MAD_COMPOSICION_ACTUAL = {
    "PP":          71,   # mayoría absoluta Ayuso
    "Más Madrid":  30,
    "PSOE":        27,
    "VOX":         13,
    "Cs":           0,   # desaparecido
    "OTROS":        0
}

PARTIDOS_MAD = ["PP", "Más Madrid", "PSOE", "VOX", "Sumar", "OTROS"]
COLORES_MAD = {
    "PP":         "#1f77b4",
    "Más Madrid": "#00b050",   # verde Más Madrid
    "PSOE":       "#d62728",
    "VOX":        "#2ca02c",
    "Sumar":      "#9467bd",
    "OTROS":      "#c7c7c7"
}

# Intención de voto base Madrid 2026 (estimación estructural)
# PP muy fuerte; Más Madrid consolida espacio; PSOE recupera algo; VOX baja
BASE_MAD = {
    "PP":         40.0,   # efecto Ayuso consolidado
    "Más Madrid": 18.0,   # alternativa progresista urbana
    "PSOE":       17.0,   # recuperación lenta
    "VOX":         9.5,   # bajada tras máximos 2021
    "Sumar":       7.0,   # fragmentación izquierda
    "OTROS":       8.5
}

# Madrid: circunscripción ÚNICA — 135 escaños
ESCANOS_MAD = {"Madrid": 135}
TOTAL_MAD   = 135

# Zonas electorales para análisis interno (no circunscripciones legales)
ZONAS_MAD = {
    "Madrid Capital Norte":  {"PP": +5, "Más Madrid": +3, "VOX": +2, "PSOE": -3},
    "Madrid Capital Sur":    {"PSOE": +4, "Más Madrid": +2, "PP": -4, "Sumar": +2},
    "Madrid Capital Centro": {"Más Madrid": +5, "PP": +2, "PSOE": +1, "VOX": -2},
    "Corona Metropolitana":  {"PP": +6, "VOX": +3, "PSOE": -2, "Más Madrid": -3},
    "Sierra y Rural":        {"PP": +8, "VOX": +4, "PSOE": -4, "Más Madrid": -5},
}

# ===============================
# FUNCIONES MADRID
# ===============================


def ajustar_escenario_mad(base_mad,
                           f_vivienda_mad, f_ayuso,
                           f_fiscal, f_migracion):
    """
    Ajuste estructural para Madrid.
    Variables: crisis vivienda, efecto Ayuso, fiscalidad baja, migración.
    """
    ajuste = base_mad.copy()

    # Vivienda Madrid → penaliza PP, beneficia Más Madrid y PSOE
    ajuste["PP"]         -= (f_vivienda_mad - 50) * 0.020
    ajuste["Más Madrid"] += (f_vivienda_mad - 50) * 0.015
    ajuste["PSOE"]       += (f_vivienda_mad - 50) * 0.008

    # Efecto Ayuso → liderazgo PP, movilización conservadora
    ajuste["PP"]  += (f_ayuso - 50) * 0.025
    ajuste["VOX"] -= (f_ayuso - 50) * 0.010   # Ayuso absorbe voto VOX

    # Fiscalidad baja → diferencial competitivo PP, atrae voto liberal
    ajuste["PP"]         += (f_fiscal - 50) * 0.015
    ajuste["Más Madrid"] -= (f_fiscal - 50) * 0.008

    # Migración → activa voto VOX y PP en corona metropolitana
    ajuste["VOX"] += (f_migracion - 50) * 0.012
    ajuste["PP"]  += (f_migracion - 50) * 0.006
    ajuste["PSOE"]+= (f_migracion - 50) * 0.004  # también moviliza izquierda

    for p in ajuste:
        ajuste[p] = max(0.0, ajuste[p])
    return normalizar(ajuste)


def ajustar_zona_mad(base, zona):
    """Ajustes por zona electoral de Madrid."""
    datos = base.copy()
    for p, delta in ZONAS_MAD.get(zona, {}).items():
        if p in datos:
            datos[p] += delta
    ruido = (100 - fiabilidad) / 100
    for p in datos:
        datos[p] += random.uniform(-ruido * 2.0, ruido * 2.0)
        datos[p] = max(0.0, datos[p])
    return normalizar(datos)


def calcular_mad(f_vivienda_mad, f_ayuso, f_fiscal, f_migracion, umbral_mad):
    """
    Cálculo Asamblea de Madrid — circunscripción única.
    Incluye análisis por zonas electorales internas.
    """
    base_esc = ajustar_escenario_mad(
        BASE_MAD, f_vivienda_mad, f_ayuso, f_fiscal, f_migracion
    )
    # Aplicar umbral
    votos_filtrados = {p: v for p, v in base_esc.items() if v >= umbral_mad}
    votos = normalizar(votos_filtrados)
    reparto = dhondt(votos, TOTAL_MAD)

    # Análisis por zonas (informativo, no afecta al reparto legal)
    datos_zonas = []
    for zona in ZONAS_MAD:
        votos_zona = ajustar_zona_mad(base_esc.copy(), zona)
        datos_zonas.append({
            "Zona":   zona,
            "Votos":  votos_zona,
            "Reparto_estimado": dhondt(
                {p: v for p, v in votos_zona.items() if v >= umbral_mad},
                round(TOTAL_MAD * 0.2)  # ~27 escaños por zona estimado
            )
        })

    return reparto, votos, datos_zonas


# ===============================
# RENDER TAB MADRID
# ===============================

def render_tab_madrid(reparto_mad, votos_mad, datos_zonas_mad,
                       polarizacion_mad, nep_mad, lsq_mad,
                       f_vivienda_mad, f_ayuso, f_fiscal, f_migracion):

    st.header("🏙️ Madrid — Laboratorio Electoral Autonómico")
    st.markdown("""
    > **Contexto:** Madrid es la CCAA más atípica del sistema español — circunscripción
    > única de 135 escaños, alta fragmentación urbana, y el laboratorio del modelo
    > fiscal diferencial del PP (Ayuso). La izquierda está fragmentada entre
    > Más Madrid, PSOE y Sumar, dificultando una alternativa de gobierno cohesionada.
    """)

    ma_mad = (TOTAL_MAD // 2) + 1  # 68

    # ---- KPIs
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("NEP Madrid", nep_mad,
                help="Número Efectivo de Partidos")
    col2.metric("Polarización", f"{polarizacion_mad:.3f}")
    col3.metric("Gallagher (LSq)", f"{lsq_mad:.1f}")
    col4.metric("Diputados totales", TOTAL_MAD)

    st.markdown("---")

    # ---- COMPOSICIÓN ACTUAL vs PROYECCIÓN
    st.subheader("📊 Composición Real 2023 vs. Proyección Simulada")
    col_act, col_sim = st.columns(2)

    with col_act:
        st.markdown("**Asamblea de Madrid 2023 (Real)**")
        df_actual = pd.DataFrame({
            "Partido":    list(MAD_COMPOSICION_ACTUAL.keys()),
            "Diputados":  list(MAD_COMPOSICION_ACTUAL.values())
        })
        df_actual = df_actual[df_actual["Diputados"] > 0]
        fig_act = px.bar(df_actual, x="Partido", y="Diputados",
                         color="Partido", color_discrete_map=COLORES_MAD,
                         text="Diputados", title="Resultado Real 2023")
        fig_act.update_traces(textposition="outside")
        fig_act.add_hline(y=ma_mad, line_dash="dash", line_color="red",
                          annotation_text=f"Mayoría Absoluta ({ma_mad})")
        st.plotly_chart(fig_act, width='stretch')
        pp_r = MAD_COMPOSICION_ACTUAL["PP"]
        st.success(f"**Gobierno actual:** PP ({pp_r}) — mayoría absoluta  |  MA: {ma_mad}")

    with col_sim:
        st.markdown("**Proyección Simulada (Escenario Actual)**")
        df_sim = pd.DataFrame({
            "Partido":   list(reparto_mad.keys()),
            "Diputados": list(reparto_mad.values())
        })
        df_sim = df_sim[df_sim["Diputados"] > 0].sort_values("Diputados", ascending=False)
        fig_sim = px.bar(df_sim, x="Partido", y="Diputados",
                         color="Partido", color_discrete_map=COLORES_MAD,
                         text="Diputados", title="Simulación Actual")
        fig_sim.update_traces(textposition="outside")
        fig_sim.add_hline(y=ma_mad, line_dash="dash", line_color="red",
                          annotation_text=f"Mayoría Absoluta ({ma_mad})")
        st.plotly_chart(fig_sim, width='stretch')
        pp_sim_v = reparto_mad.get("PP", 0)
        mm_sim   = reparto_mad.get("Más Madrid", 0)
        estado   = "✅ Mayoría absoluta" if pp_sim_v >= ma_mad else f"❌ PP necesita {ma_mad - pp_sim_v} más"
        st.info(f"**PP:** {pp_sim_v}  |  **Más Madrid:** {mm_sim}  |  {estado}")

    # ---- DELTA
    st.subheader("🔄 Variación Estimada respecto a 2023")
    delta_data = []
    for p in PARTIDOS_MAD:
        actual_v   = MAD_COMPOSICION_ACTUAL.get(p, 0)
        simulado_v = reparto_mad.get(p, 0)
        delta_data.append({
            "Partido":     p,
            "2023 (Real)": actual_v,
            "Simulado":    simulado_v,
            "Δ Cambio":    simulado_v - actual_v
        })
    df_delta = pd.DataFrame(delta_data)
    fig_delta = px.bar(df_delta, x="Partido", y="Δ Cambio",
                       color="Δ Cambio", color_continuous_scale="RdYlGn",
                       title="Variación respecto a 2023", text="Δ Cambio")
    fig_delta.add_hline(y=0, line_color="black", line_width=1)
    fig_delta.update_traces(textposition="outside")
    st.plotly_chart(fig_delta, width='stretch')

    # ---- ANÁLISIS POR ZONAS
    st.subheader("🗺️ Análisis por Zonas Electorales")
    st.markdown("_Madrid tiene circunscripción única — el desglose zonal es analítico, no legal._")

    zona_sel = st.selectbox("Zona electoral", list(ZONAS_MAD.keys()),
                             key="selectbox_mad")
    dz = next(d for d in datos_zonas_mad if d["Zona"] == zona_sel)

    col_zv, col_ze = st.columns(2)
    with col_zv:
        df_vz = pd.DataFrame({
            "Partido":  list(dz["Votos"].keys()),
            "Voto (%)": list(dz["Votos"].values())
        })
        df_vz = df_vz[df_vz["Voto (%)"] > 0.5].sort_values("Voto (%)", ascending=True)
        fig_vz = go.Figure(go.Bar(
            x=df_vz["Voto (%)"], y=df_vz["Partido"], orientation="h",
            marker_color=[COLORES_MAD.get(p, "#999") for p in df_vz["Partido"]],
            text=df_vz["Voto (%)"].round(1), textposition="outside"
        ))
        fig_vz.update_layout(height=300, xaxis_title="% Voto",
                             title=f"Intención de Voto — {zona_sel}")
        st.plotly_chart(fig_vz, width='stretch')

    with col_ze:
        rep_z = {p: v for p, v in dz["Reparto_estimado"].items() if v > 0}
        if rep_z:
            fig_ez = px.pie(values=list(rep_z.values()), names=list(rep_z.keys()),
                            color=list(rep_z.keys()),
                            color_discrete_map=COLORES_MAD, hole=0.4,
                            title=f"Estimación escaños — {zona_sel}")
            st.plotly_chart(fig_ez, width='stretch')

    # ---- COALICIONES
    st.subheader("🤝 Análisis de Coaliciones — Asamblea de Madrid")
    pp_s  = reparto_mad.get("PP", 0)
    mm_s  = reparto_mad.get("Más Madrid", 0)
    ps_s  = reparto_mad.get("PSOE", 0)
    vox_s = reparto_mad.get("VOX", 0)
    su_s  = reparto_mad.get("Sumar", 0)

    coaliciones = {
        "PP solo":                   pp_s,
        "PP + VOX":                  pp_s + vox_s,
        "Más Madrid + PSOE":         mm_s + ps_s,
        "Más Madrid + PSOE + Sumar": mm_s + ps_s + su_s,
        "Bloque izquierda completo":  mm_s + ps_s + su_s,
    }
    df_coal = pd.DataFrame({
        "Coalición": list(coaliciones.keys()),
        "Diputados": list(coaliciones.values())
    })
    df_coal["¿Mayoría?"] = df_coal["Diputados"].apply(
        lambda x: "✅ Mayoría" if x >= ma_mad else f"❌ Faltan {ma_mad - x}"
    )
    fig_coal = px.bar(df_coal, x="Coalición", y="Diputados",
                      text="Diputados", color="Diputados",
                      color_continuous_scale="Blues",
                      title=f"Escenarios de Coalición (MA: {ma_mad})")
    fig_coal.add_hline(y=ma_mad, line_dash="dash", line_color="red")
    fig_coal.update_traces(textposition="outside")
    st.plotly_chart(fig_coal, width='stretch')
    st.dataframe(df_coal, width='stretch')

    # ---- RADAR
    st.subheader("📡 Variables Estructurales Madrid")
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        cat_mad = ["Vivienda", "Efecto Ayuso", "Fiscalidad", "Migración", "Fiabilidad"]
        val_mad = [f_vivienda_mad, f_ayuso, f_fiscal, f_migracion, fiabilidad]
        fig_rad = go.Figure(go.Scatterpolar(
            r=val_mad, theta=cat_mad, fill="toself",
            line_color="#1f77b4", name="Madrid"
        ))
        fig_rad.update_layout(
            polar=dict(radialaxis=dict(range=[0, 100])),
            title="Perfil de Riesgo Electoral Madrid"
        )
        st.plotly_chart(fig_rad, width='stretch')

    with col_r2:
        # Heatmap zonas
        votos_matrix = []
        for dz in datos_zonas_mad:
            row = {"Zona": dz["Zona"]}
            for p in PARTIDOS_MAD:
                row[p] = round(dz["Votos"].get(p, 0), 1)
            votos_matrix.append(row)
        df_heat = pd.DataFrame(votos_matrix).set_index("Zona")
        fig_heat = px.imshow(df_heat, color_continuous_scale="RdYlBu_r",
                             title="% Intención de Voto por Zona",
                             text_auto=True)
        st.plotly_chart(fig_heat, width='stretch')

    # ---- NOTA METODOLÓGICA
    with st.expander("📋 Nota Metodológica — Módulo Madrid"):
        st.markdown(f"""
**Circunscripción:** Única | **Total diputados:** {TOTAL_MAD} | **Mayoría absoluta:** {ma_mad}  
**Umbral electoral:** 5% sobre el total de votos válidos  
**Base:** Resultado real mayo 2023 con ajuste estructural 2026  

**Particularidad metodológica — Circunscripción única:**  
Madrid es la única CCAA grande con circunscripción única. Esto significa que el
D'Hondt opera sobre 135 escaños, siendo el sistema más proporcional de España.
El índice de Gallagher debería ser muy bajo (~2-3). El desglose zonal es **analítico**,
no legal — sirve para identificar tendencias territoriales dentro de la comunidad.

**Variables estructurales específicas:**
- **Efecto Ayuso:** Liderazgo carismático con alta capacidad de movilización conservadora.
  Absorbe voto VOX y genera lealtad en corona metropolitana y sierra.
- **Vivienda:** Crisis de alquiler especialmente aguda en Madrid capital.
  Principal vulnerabilidad electoral del PP entre jóvenes y clases medias urbanas.
- **Fiscalidad baja:** Diferencial competitivo respecto a otras CCAA.
  Atrae voto liberal y empresarial. Variable defensiva del PP.
- **Migración:** Variable de alta movilización en corona metropolitana sur.
  Activa simultáneamente voto VOX/PP y voto progresista.

**Perfiles zonales:**
- **Capital Norte:** Salamanca, Chamberí, Retiro — PP+VOX muy fuertes
- **Capital Sur:** Vallecas, Carabanchel, Villaverde — PSOE+Sumar
- **Capital Centro:** Malasaña, Lavapiés, Chueca — Más Madrid hegemónico
- **Corona Metropolitana:** Alcorcón, Leganés, Getafe vs Pozuelo, Majadahonda
- **Sierra y Rural:** PP+VOX dominantes, baja densidad

**Limitaciones:**
- Cs desaparecido → votos redistribuidos entre PP y PSOE principalmente
- Alta volatilidad urbana — Madrid capital muy sensible a eventos exógenos
- Más Madrid y Sumar compiten por mismo electorado → difícil modelar trasvases
        """)


# ===============================
# ENERGÍA — DATOS Y CONSTANTES
# ===============================

# Media UE Oil Bulletin (referencia semanal — se actualiza via ingest)
# Valores base marzo 2026 (€/litro con impuestos)
# ===============================
# FUNCIÓN INGESTA ENERGÍA
# ===============================


def obtener_precios_carburantes():
    """
    Descarga precios actuales de gasolineras desde API MINETUR.
    Calcula media nacional de Gasolina 95 y Gasóleo A.
    Retorna dict con precios medios o None si falla.
    """
    URL = ("https://sedeaplicaciones.minetur.gob.es/"
           "ServiciosRESTCarburantes/PreciosCarburantes/EstacionesTerrestres/")
    try:
        r = requests.get(URL, timeout=20,
                         headers={"User-Agent": "espana-vota/2.2",
                                  "Accept": "application/json"})
        if r.status_code != 200:
            return None
        data = r.json()
        eess = data.get("ListaEESSPrecio", [])
        fecha_api = data.get("Fecha", "")[:10].replace("/", "-")
        # Reordenar fecha DD-MM-YYYY → YYYY-MM-DD
        partes = fecha_api.split("-")
        if len(partes) == 3 and len(partes[2]) == 4:
            fecha_api = f"{partes[2]}-{partes[1]}-{partes[0]}"

        precios_95, precios_goa = [], []
        for e in eess:
            g95 = e.get("Precio Gasolina 95 E5", "").strip().replace(",", ".")
            goa = e.get("Precio Gasoleo A", "").strip().replace(",", ".")
            try:
                if g95:
                    precios_95.append(float(g95))
                if goa:
                    precios_goa.append(float(goa))
            except ValueError:
                pass

        if not precios_95 or not precios_goa:
            return None

        return {
            "fecha":        fecha_api,
            "gasolina_95":  round(sum(precios_95) / len(precios_95), 3),
            "gasoleo_a":    round(sum(precios_goa) / len(precios_goa), 3),
            "n_estaciones": len(eess),
            "fuente":       "MINETUR"
        }
    except Exception:
        return None


def obtener_brent_eur():
    """
    Obtiene precio Brent en EUR desde datahub.io (sin API key).
    Retorna float o None si falla.
    """
    # Tipo de cambio USD/EUR aproximado (se actualiza si hay endpoint)
    USD_EUR = 0.92
    try:
        r = requests.get(
            "https://pkgstore.datahub.io/core/oil-prices/brent-daily_json/data/brent-daily_json.json",
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            if data:
                ultimo = data[-1]
                precio_usd = float(ultimo.get("Price", 0))
                return round(precio_usd * USD_EUR, 2)
    except Exception:
        pass
    return None


# ===============================
# RENDER TAB ENERGÍA
# ===============================



# ===============================
# HEMICICLO — GRÁFICOS PARLAMENTO
# ===============================

def hacer_herradura(escanos_dict, colores, titulo, total=350):
    """
    Genera gráfico en forma de herradura (semicírculo) que representa
    la composición de un parlamento. Usa scatter polar con puntos
    distribuidos en arco de 180 grados de izquierda a derecha.
    """
    import numpy as np

    # Ordenar partidos por posición ideológica (izquierda → derecha)
    orden_ideologico = ["BILDU", "ERC", "JUNTS", "BNG", "SUMAR", "PSOE",
                        "CC", "PNV", "UPN", "OTROS", "PP", "VOX", "SALF"]
    partidos_ordenados = [p for p in orden_ideologico if p in escanos_dict and escanos_dict[p] > 0]
    # Añadir cualquier partido no contemplado en el orden
    for p in escanos_dict:
        if p not in partidos_ordenados and escanos_dict[p] > 0:
            partidos_ordenados.append(p)

    # Distribuir escaños en arco semicircular (180° = π radianes)
    # De izquierda (π) a derecha (0), de exterior a interior en filas
    FILAS = 8
    escanos_por_fila = [total // FILAS + (1 if i < total % FILAS else 0) for i in range(FILAS)]

    # Generar posiciones de todos los escaños
    todas_posiciones = []
    for fila in range(FILAS):
        n = escanos_por_fila[fila]
        radio = 1.0 + fila * 0.15
        angulos = np.linspace(np.pi, 0, n)
        for ang in angulos:
            todas_posiciones.append((radio * np.cos(ang), radio * np.sin(ang)))

    # Asignar partidos a posiciones
    asignaciones = []
    for p in partidos_ordenados:
        asignaciones.extend([p] * escanos_dict.get(p, 0))
    # Rellenar si faltan
    while len(asignaciones) < len(todas_posiciones):
        asignaciones.append("OTROS")
    asignaciones = asignaciones[:len(todas_posiciones)]

    # Crear figura
    fig = go.Figure()
    for p in partidos_ordenados:
        xs = [todas_posiciones[i][0] for i, a in enumerate(asignaciones) if a == p]
        ys = [todas_posiciones[i][1] for i, a in enumerate(asignaciones) if a == p]
        color = colores.get(p, "#aaaaaa")
        fig.add_trace(go.Scatter(
            x=xs, y=ys,
            mode="markers",
            marker=dict(size=7, color=color, line=dict(width=0.5, color="white")),
            name=f"{p} ({escanos_dict.get(p,0)})",
            hovertemplate=f"<b>{p}</b><br>Escaños: {escanos_dict.get(p,0)}<extra></extra>"
        ))

    # Línea de mayoría absoluta
    ma = total // 2 + 1
    fig.add_annotation(
        x=0, y=0.05,
        text=f"<b>MA: {ma}</b>",
        showarrow=False,
        font=dict(size=12, color="red")
    )
    fig.update_layout(
        title=dict(text=titulo, x=0.5, font=dict(size=14)),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5,
                    font=dict(size=10)),
        xaxis=dict(visible=False, range=[-1.4, 1.4]),
        yaxis=dict(visible=False, range=[-0.1, 1.5], scaleanchor="x"),
        height=420,
        margin=dict(l=10, r=10, t=40, b=80),
        plot_bgcolor="white",
        paper_bgcolor="white"
    )
    return fig


def hacer_donut(escanos_dict, colores, titulo):
    """Gráfico donut con escaños y porcentajes."""
    partidos = [p for p, v in escanos_dict.items() if v > 0]
    valores  = [escanos_dict[p] for p in partidos]
    colores_lista = [colores.get(p, "#aaaaaa") for p in partidos]
    total = sum(valores)
    labels = [f"{p}<br>{v} ({v/total*100:.1f}%)" for p, v in zip(partidos, valores)]

    fig = go.Figure(go.Pie(
        labels=partidos,
        values=valores,
        hole=0.45,
        marker=dict(colors=colores_lista,
                    line=dict(color="white", width=2)),
        textinfo="label+value",
        hovertemplate="<b>%{label}</b><br>Escaños: %{value}<br>%{percent}<extra></extra>",
        sort=False
    ))
    fig.add_annotation(
        text=f"<b>{total}</b><br>escaños",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=14)
    )
    fig.update_layout(
        title=dict(text=titulo, x=0.5, font=dict(size=14)),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.3,
                    xanchor="center", x=0.5, font=dict(size=10)),
        height=380,
        margin=dict(l=10, r=10, t=40, b=80)
    )
    return fig


# ============================================================
# AUDITORÍA & APRENDIZAJE — v2.0
# ============================================================
# Novedades v2:
#  - Galicia 2024: retrovalidación REAL (encuestas vs resultado real)
#  - Andalucía 2026: encuestas actuales (CENTRA, Sigma Dos, Social Data)
#  - Madrid 2023: retrovalidación REAL (encuestas vs resultado real)
#  - Lecciones Aprendidas: gráfico mejorado — gauge + tabla errores sistemáticos
#  - Histórico de precisión acumulado entre elecciones pasadas
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ------------------------------------------------------------------
# BASE DE DATOS UNIFICADA
# ------------------------------------------------------------------
# Cada ámbito puede ser:
#   tipo="proyeccion"   → elecciones futuras, sin resultado real todavía
#   tipo="retroval"     → elecciones pasadas, resultado real conocido
#
# En "retroval" se incluye "resultado_real" con los escaños reales.
# ------------------------------------------------------------------

AMBITOS = {

    # ---- CASTILLA Y LEÓN 2026 (futura, proyección) ---------------
    "🏰 CyL 2026 (próximas)": {
        "tipo": "proyeccion",
        "fecha_elecciones": "2026-03-15",
        "total_escanos": 86,
        "ma": 44,
        "partidos": ["PP", "PSOE", "VOX", "UPL", "SUMAR"],
        "colores": {
            "PP": "#1565C0", "PSOE": "#C62828",
            "VOX": "#2E7D32", "UPL": "#E65100", "SUMAR": "#6A1B9A"
        },
        "encuestas": {
            "PP":    {"Sigma Dos": 35.5, "NC Report": 35.6, "Sociométrica": 31.6, "CIS": 33.4},
            "PSOE":  {"Sigma Dos": 27.0, "NC Report": 27.6, "Sociométrica": 27.3, "CIS": 32.3},
            "VOX":   {"Sigma Dos": 19.7, "NC Report": 17.9, "Sociométrica": 20.0, "CIS": 18.5},
            "UPL":   {"Sigma Dos":  4.5, "NC Report":  4.9, "Sociométrica":  4.2, "CIS":  6.3},
            "SUMAR": {"Sigma Dos":  3.5, "NC Report":  3.8, "Sociométrica":  3.6, "CIS":  3.6},
        },
        "escanos_encuesta_media": {
            "PP": 33, "PSOE": 27, "VOX": 15, "UPL": 4, "SUMAR": 1
        },
        "encuestadoras": ["Sigma Dos", "NC Report", "Sociométrica", "CIS"],
    },

    # ---- GALICIA 2024 (pasada, retrovalidación REAL) --------------
    "🌿 Galicia 2024 (retroval.)": {
        "tipo": "retroval",
        "fecha_elecciones": "2024-02-18",
        "total_escanos": 75,
        "ma": 38,
        "partidos": ["PP", "BNG", "PSdeG", "DO"],
        "colores": {
            "PP": "#1565C0", "BNG": "#558B2F",
            "PSdeG": "#C62828", "DO": "#FF8F00"
        },
        # Encuestas preelectorales (medias de enero-febrero 2024)
        "encuestas": {
            "PP":    {"GAD3": 45.9, "Sigma Dos": 45.5, "CIS": 43.2, "NC Report": 47.0},
            "BNG":   {"GAD3": 33.0, "Sigma Dos": 29.0, "CIS": 33.4, "NC Report": 26.0},
            "PSdeG": {"GAD3": 12.5, "Sigma Dos": 15.0, "CIS": 18.1, "NC Report": 17.5},
            "DO":    {"GAD3":  0.7, "Sigma Dos":  0.5, "CIS":  0.6, "NC Report":  0.5},
        },
        "escanos_encuesta_media": {
            "PP": 39, "BNG": 23, "PSdeG": 12, "DO": 1
        },
        # RESULTADO REAL 18-F 2024 (100% escrutado)
        "resultado_real": {
            "PP": 40, "BNG": 25, "PSdeG": 9, "DO": 1
        },
        "encuestadoras": ["GAD3", "Sigma Dos", "CIS", "NC Report"],
    },

    # ---- ANDALUCÍA 2026 (futura, proyección) ---------------------
    "🌞 Andalucía 2026 (próximas)": {
        "tipo": "proyeccion",
        "fecha_elecciones": "2026-06-01",   # estimada primavera 2026
        "total_escanos": 109,
        "ma": 55,
        "partidos": ["PP", "PSOE", "VOX", "Por Andalucía", "Adelante And."],
        "colores": {
            "PP": "#1565C0", "PSOE": "#C62828", "VOX": "#2E7D32",
            "Por Andalucía": "#6A1B9A", "Adelante And.": "#F57F17"
        },
        # Fuentes: CENTRA dic-2025, Sigma Dos feb-2026, Social Data feb-2026
        "encuestas": {
            "PP":              {"CENTRA": 40.2, "Sigma Dos": 40.4, "Social Data": 42.7},
            "PSOE":            {"CENTRA": 21.4, "Sigma Dos": 20.8, "Social Data": 19.4},
            "VOX":             {"CENTRA": 17.5, "Sigma Dos": 18.0, "Social Data": 17.6},
            "Por Andalucía":   {"CENTRA":  7.5, "Sigma Dos":  7.5, "Social Data":  5.8},
            "Adelante And.":   {"CENTRA":  6.1, "Sigma Dos":  4.5, "Social Data":  7.6},
        },
        "escanos_encuesta_media": {
            "PP": 54, "PSOE": 26, "VOX": 20, "Por Andalucía": 5, "Adelante And.": 3
        },
        "encuestadoras": ["CENTRA", "Sigma Dos", "Social Data"],
    },

    # ---- MADRID 2023 (pasada, retrovalidación REAL) --------------
    "🏙️ Madrid 2023 (retroval.)": {
        "tipo": "retroval",
        "fecha_elecciones": "2023-05-28",
        "total_escanos": 135,
        "ma": 68,
        "partidos": ["PP", "Más Madrid", "PSOE", "VOX", "Sumar"],
        "colores": {
            "PP": "#1565C0", "Más Madrid": "#00897B",
            "PSOE": "#C62828", "VOX": "#2E7D32", "Sumar": "#6A1B9A"
        },
        # Encuestas previas (medias de mayo 2023)
        "encuestas": {
            "PP":          {"GAD3": 47.5, "Sigma Dos": 46.8, "CIS": 44.5, "40dB": 45.0},
            "Más Madrid":  {"GAD3": 19.0, "Sigma Dos": 18.5, "CIS": 20.0, "40dB": 19.5},
            "PSOE":        {"GAD3": 17.8, "Sigma Dos": 18.0, "CIS": 19.5, "40dB": 18.5},
            "VOX":         {"GAD3":  8.5, "Sigma Dos":  9.0, "CIS":  9.5, "40dB":  8.8},
            "Sumar":       {"GAD3":  4.5, "Sigma Dos":  4.8, "CIS":  5.0, "40dB":  4.5},
        },
        "escanos_encuesta_media": {
            "PP": 65, "Más Madrid": 26, "PSOE": 25, "VOX": 13, "Sumar": 6
        },
        # RESULTADO REAL 28-M 2023 (100% escrutado)
        "resultado_real": {
            "PP": 66, "Más Madrid": 26, "PSOE": 24, "VOX": 10, "Sumar": 9
        },
        "encuestadoras": ["GAD3", "Sigma Dos", "CIS", "40dB"],
    },

    # ---- NACIONAL 2026 (futura, proyección) ----------------------
    "🗺️ Nacional 2026 (próximas)": {
        "tipo": "proyeccion",
        "fecha_elecciones": "2027-12-01",
        "total_escanos": 350,
        "ma": 176,
        "partidos": ["PP", "PSOE", "VOX", "SUMAR", "JUNTS", "ERC", "BILDU", "PNV"],
        "colores": {
            "PP": "#1565C0", "PSOE": "#C62828", "VOX": "#2E7D32",
            "SUMAR": "#6A1B9A", "JUNTS": "#FF8F00", "ERC": "#FFD600",
            "BILDU": "#00695C", "PNV": "#1B5E20"
        },
        "encuestas": {
            "PP":    {"40dB": 33.2, "NC Report": 32.8, "Sigma Dos": 34.1, "CIS": 31.5},
            "PSOE":  {"40dB": 28.4, "NC Report": 27.9, "Sigma Dos": 28.8, "CIS": 31.2},
            "VOX":   {"40dB": 12.1, "NC Report": 11.8, "Sigma Dos": 12.5, "CIS": 10.8},
            "SUMAR": {"40dB":  6.8, "NC Report":  7.2, "Sigma Dos":  6.5, "CIS":  7.1},
            "JUNTS": {"40dB":  3.5, "NC Report":  3.2, "Sigma Dos":  3.8, "CIS":  3.0},
            "ERC":   {"40dB":  2.8, "NC Report":  2.5, "Sigma Dos":  2.9, "CIS":  2.4},
            "BILDU": {"40dB":  2.2, "NC Report":  2.4, "Sigma Dos":  2.1, "CIS":  2.0},
            "PNV":   {"40dB":  1.8, "NC Report":  1.7, "Sigma Dos":  1.9, "CIS":  1.8},
        },
        "escanos_encuesta_media": {
            "PP": 138, "PSOE": 118, "VOX": 35, "SUMAR": 28,
            "JUNTS": 8, "ERC": 6, "BILDU": 5, "PNV": 5
        },
        "encuestadoras": ["40dB", "NC Report", "Sigma Dos", "CIS"],
    },
}

# ------------------------------------------------------------------
# HISTÓRICO DE PRECISIÓN — elecciones pasadas verificables
# ------------------------------------------------------------------
HISTORICO_PRECISION = [
    {
        "eleccion": "Galicia 2024",
        "encuestadora": "GAD3",
        "mae_escanos": 4.0,
        "rmse_escanos": 5.3,
        "error_pp": -1,   # estimó 39, real 40  → -1
        "error_bng": 2,   # estimó 25-26, real 25 → aprox OK
        "sesgo": "Subestimó PSOE, sobreestimó PP",
        "nota": 73,
    },
    {
        "eleccion": "Galicia 2024",
        "encuestadora": "CIS",
        "mae_escanos": 6.5,
        "rmse_escanos": 8.1,
        "error_pp": 4,    # estimó 36-38, real 40 → -4
        "error_bng": -6,  # estimó 24-31, real 25
        "sesgo": "Infravaloró PP, sobrevaloró PSOE",
        "nota": 58,
    },
    {
        "eleccion": "Galicia 2024",
        "encuestadora": "Sigma Dos",
        "mae_escanos": 3.5,
        "rmse_escanos": 4.2,
        "error_pp": -1,
        "error_bng": 2,
        "sesgo": "Sobreestimó PSOE gallego",
        "nota": 79,
    },
    {
        "eleccion": "Madrid 2023",
        "encuestadora": "GAD3",
        "mae_escanos": 2.8,
        "rmse_escanos": 3.6,
        "error_pp": 1,
        "error_bng": None,
        "sesgo": "Infraestimó Sumar (+3), sobreestimó VOX (+3)",
        "nota": 82,
    },
    {
        "eleccion": "Madrid 2023",
        "encuestadora": "CIS",
        "mae_escanos": 3.5,
        "rmse_escanos": 4.4,
        "error_pp": 2,
        "error_bng": None,
        "sesgo": "Sobreestimó Más Madrid, infraestimó PP",
        "nota": 75,
    },
    {
        "eleccion": "Madrid 2023",
        "encuestadora": "Sigma Dos",
        "mae_escanos": 3.2,
        "rmse_escanos": 3.9,
        "error_pp": 1,
        "error_bng": None,
        "sesgo": "Sobreestimó VOX (+3), infraestimó Sumar",
        "nota": 78,
    },
    {
        "eleccion": "Generales 2023",
        "encuestadora": "40dB",
        "mae_escanos": 2.0,
        "rmse_escanos": 2.5,
        "error_pp": -1,
        "error_bng": None,
        "sesgo": "Más precisa en PP y PSOE",
        "nota": 90,
    },
    {
        "eleccion": "Generales 2023",
        "encuestadora": "GAD3",
        "mae_escanos": 5.8,
        "rmse_escanos": 7.3,
        "error_pp": -14,
        "error_bng": None,
        "sesgo": "Sobrestimó PP en 14 escaños (gran fallo 23J)",
        "nota": 42,
    },
    {
        "eleccion": "Generales 2023",
        "encuestadora": "Sigma Dos",
        "mae_escanos": 5.2,
        "rmse_escanos": 6.5,
        "error_pp": -10,
        "error_bng": None,
        "sesgo": "Sobrestimó PP, infraestimó VOX en escaños",
        "nota": 52,
    },
]

# ------------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------------

def _media_ponderada(encuestas_partido: dict, pesos: dict) -> float:
    """Media ponderada de encuestas según pesos dados."""
    vals, ws = [], []
    for fuente, pct in encuestas_partido.items():
        w = pesos.get(fuente, 1.0)
        vals.append(pct)
        ws.append(w)
    if not vals:
        return 0.0
    total_w = sum(ws)
    if total_w == 0:
        return float(np.mean(vals))
    return sum(v * w for v, w in zip(vals, ws)) / total_w


def _mae(pred: dict, real: dict) -> float:
    partidos = [p for p in pred if p in real]
    if not partidos:
        return 0.0
    return float(np.mean([abs(pred[p] - real[p]) for p in partidos]))


def _rmse(pred: dict, real: dict) -> float:
    partidos = [p for p in pred if p in real]
    if not partidos:
        return 0.0
    return float(np.sqrt(np.mean([(pred[p] - real[p])**2 for p in partidos])))


def _precision_index(rmse: float) -> float:
    return max(0.0, min(100.0, 100.0 - rmse * 5))


# ------------------------------------------------------------------
# GRÁFICOS
# ------------------------------------------------------------------

def _grafico_comparativa(partidos, escanos_modelo, escanos_enc_media, colores):
    """Barras agrupadas: Modelo vs Media Encuestas."""
    fig = go.Figure()
    x = list(partidos)
    fig.add_bar(
        x=x,
        y=[escanos_modelo.get(p, 0) for p in x],
        name="🤖 Modelo",
        marker_color=[colores.get(p, "#888") for p in x],
        opacity=0.9,
        text=[escanos_modelo.get(p, 0) for p in x],
        textposition="outside",
    )
    fig.add_bar(
        x=x,
        y=[escanos_enc_media.get(p, 0) for p in x],
        name="📊 Media Encuestas",
        marker_color=[colores.get(p, "#888") for p in x],
        opacity=0.45,
        marker_pattern_shape="/",
        text=[escanos_enc_media.get(p, 0) for p in x],
        textposition="outside",
    )
    fig.update_layout(
        barmode="group",
        title="Modelo vs Media de Encuestas (escaños)",
        height=380,
        margin=dict(t=50, b=30),
        legend=dict(orientation="h", y=-0.2),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.1)")
    return fig


def _grafico_delta(partidos, escanos_modelo, escanos_enc_media, colores):
    """Delta sistemático (Modelo − Encuesta) por partido."""
    x = list(partidos)
    deltas = [escanos_modelo.get(p, 0) - escanos_enc_media.get(p, 0) for p in x]
    bar_colors = []
    for d in deltas:
        if d > 0:
            bar_colors.append("#43A047")
        elif d < 0:
            bar_colors.append("#E53935")
        else:
            bar_colors.append("#757575")
    fig = go.Figure(go.Bar(
        x=x, y=deltas,
        marker_color=bar_colors,
        text=[f"{d:+d}" for d in deltas],
        textposition="outside",
    ))
    fig.add_hline(y=0, line_color="white", line_width=1)
    fig.update_layout(
        title="Δ Modelo − Encuesta (escaños) · verde=modelo mayor",
        height=320,
        margin=dict(t=50, b=30),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.1)", zeroline=True, zerolinecolor="white")
    return fig


def _grafico_encuestas_fuente(partidos, encuestas_dict, colores):
    """Barras por fuente encuestadora para cada partido."""
    fuentes = sorted({f for d in encuestas_dict.values() for f in d})
    fig = go.Figure()
    for fuente in fuentes:
        fig.add_bar(
            name=fuente,
            x=list(partidos),
            y=[encuestas_dict.get(p, {}).get(fuente, None) for p in partidos],
        )
    fig.update_layout(
        barmode="group",
        title="% Voto estimado por encuestadora",
        height=340,
        margin=dict(t=50, b=30),
        legend=dict(orientation="h", y=-0.25),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.1)")
    return fig


def _grafico_retroval(partidos, real, enc_media, colores):
    """Para retrovalidación: 3 barras por partido — Real / Encuesta / Modelo."""
    x = list(partidos)
    real_vals  = [real.get(p, 0) for p in x]
    enc_vals   = [enc_media.get(p, 0) for p in x]
    delta_enc  = [enc_media.get(p, 0) - real.get(p, 0) for p in x]

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Resultado Real vs Encuestas (escaños)", "Error de las Encuestas (Δ enc − real)")
    )

    fig.add_bar(
        x=x, y=real_vals,
        name="✅ Resultado Real",
        marker_color=[colores.get(p, "#888") for p in x],
        opacity=0.95,
        text=real_vals, textposition="outside",
        row=1, col=1,
    )
    fig.add_bar(
        x=x, y=enc_vals,
        name="📊 Media Encuestas",
        marker_color=[colores.get(p, "#888") for p in x],
        opacity=0.45,
        marker_pattern_shape="/",
        text=enc_vals, textposition="outside",
        row=1, col=1,
    )

    bar_colors_delta = ["#43A047" if d > 0 else "#E53935" if d < 0 else "#757575" for d in delta_enc]
    fig.add_bar(
        x=x, y=delta_enc,
        name="Δ (enc − real)",
        marker_color=bar_colors_delta,
        text=[f"{d:+d}" for d in delta_enc],
        textposition="outside",
        row=1, col=2,
    )
    fig.add_hline(y=0, line_color="white", line_width=1, row=1, col=2)

    fig.update_layout(
        height=380,
        margin=dict(t=60, b=30),
        legend=dict(orientation="h", y=-0.2),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        showlegend=True,
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.1)")
    return fig


def _gauge_precision(score: float, titulo: str = "Índice de Precisión"):
    """Gauge semicircular de 0-100."""
    color_needle = "#00E676" if score >= 75 else "#FFCA28" if score >= 50 else "#EF5350"
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        number={"suffix": " / 100", "font": {"size": 28, "color": "white"}},
        title={"text": titulo, "font": {"size": 14, "color": "white"}},
        delta={"reference": 75, "increasing": {"color": "#00E676"}, "decreasing": {"color": "#EF5350"}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "white", "tickfont": {"color": "white"}},
            "bar": {"color": color_needle, "thickness": 0.25},
            "bgcolor": "rgba(30,30,50,0.8)",
            "bordercolor": "rgba(255,255,255,0.2)",
            "steps": [
                {"range": [0,   50], "color": "rgba(239,83,80,0.25)"},
                {"range": [50,  75], "color": "rgba(255,202,40,0.25)"},
                {"range": [75, 100], "color": "rgba(0,230,118,0.25)"},
            ],
            "threshold": {
                "line": {"color": "white", "width": 2},
                "thickness": 0.75,
                "value": 75,
            },
        },
    ))
    fig.update_layout(
        height=240,
        margin=dict(t=40, b=10, l=20, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
    )
    return fig


def _grafico_historico_precision():
    """Ranking de precisión histórica por encuestadora."""
    df = pd.DataFrame(HISTORICO_PRECISION)
    medias = df.groupby("encuestadora")["nota"].mean().sort_values(ascending=True).reset_index()
    medias.columns = ["encuestadora", "nota_media"]

    bar_colors = []
    for n in medias["nota_media"]:
        if n >= 75:
            bar_colors.append("#00C853")
        elif n >= 55:
            bar_colors.append("#FFD600")
        else:
            bar_colors.append("#FF5252")

    fig = go.Figure(go.Bar(
        x=medias["nota_media"],
        y=medias["encuestadora"],
        orientation="h",
        marker_color=bar_colors,
        text=[f"{v:.0f}" for v in medias["nota_media"]],
        textposition="outside",
    ))
    fig.add_vline(x=75, line_dash="dash", line_color="white", annotation_text="Umbral bueno (75)",
                  annotation_font_color="white")
    fig.update_layout(
        title="🏆 Ranking histórico de precisión por encuestadora (media)",
        xaxis_title="Índice de Precisión (0–100)",
        height=340,
        margin=dict(t=50, b=30, l=120, r=60),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
    )
    fig.update_xaxes(range=[0, 110], showgrid=True, gridcolor="rgba(255,255,255,0.1)")
    fig.update_yaxes(showgrid=False)
    return fig


def _grafico_precision_por_eleccion():
    """Scatter: nota de precisión por elección y encuestadora."""
    df = pd.DataFrame(HISTORICO_PRECISION)
    fig = px.scatter(
        df,
        x="eleccion",
        y="nota",
        color="encuestadora",
        size="nota",
        hover_data=["sesgo", "mae_escanos"],
        title="Precisión por elección y encuestadora (tamaño = nota)",
    )
    fig.add_hline(y=75, line_dash="dash", line_color="white", annotation_text="Bueno",
                  annotation_font_color="white")
    fig.update_layout(
        height=360,
        margin=dict(t=50, b=30),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        legend=dict(orientation="h", y=-0.3),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(range=[0, 105], showgrid=True, gridcolor="rgba(255,255,255,0.1)")
    return fig


def _grafico_sesgo_sistematico():
    """Heatmap: sesgo sistemático de cada encuestadora en cada elección."""
    df = pd.DataFrame(HISTORICO_PRECISION)
    pivot = df.pivot_table(index="encuestadora", columns="eleccion", values="nota", aggfunc="mean")
    z = pivot.values.tolist()
    fig = go.Figure(go.Heatmap(
        z=z,
        x=list(pivot.columns),
        y=list(pivot.index),
        colorscale=[
            [0.0,  "#B71C1C"],
            [0.5,  "#F9A825"],
            [0.75, "#2E7D32"],
            [1.0,  "#00E676"],
        ],
        zmin=0, zmax=100,
        text=[[f"{v:.0f}" if not np.isnan(v) else "—" for v in row] for row in z],
        texttemplate="%{text}",
        colorbar=dict(title="Nota", tickfont=dict(color="white"), titlefont=dict(color="white")),
    ))
    fig.update_layout(
        title="🔥 Mapa de Calor — Precisión por encuestadora y elección",
        height=300,
        margin=dict(t=50, b=30, l=120),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
    )
    return fig


# ------------------------------------------------------------------
# RENDER PRINCIPAL
# ------------------------------------------------------------------

def render_tab_auditoria(escanos_nac: dict, escanos_cyl: dict):
    """
    Tab 🧠 Auditoría & Aprendizaje v2.

    Parámetros
    ----------
    escanos_nac : dict  → proyección nacional del modelo {partido: escaños}
    escanos_cyl : dict  → proyección CyL del modelo {partido: escaños}
    """

    st.markdown("## 🧠 Auditoría & Aprendizaje")
    st.markdown(
        "Compara el **modelo predictivo** contra encuestas reales · "
        "retrovalida con resultados conocidos · aprende de los errores pasados."
    )

    # ── Selector de ámbito ───────────────────────────────────────
    nombres = list(AMBITOS.keys())
    sel = st.selectbox("📍 Selecciona ámbito", nombres, key="aud_ambito_v2")
    datos = AMBITOS[sel]
    es_retroval = datos["tipo"] == "retroval"

    partidos    = datos["partidos"]
    colores     = datos["colores"]
    encuestas   = datos["encuestas"]
    enc_media_esc = datos["escanos_encuesta_media"]
    total_esc   = datos["total_escanos"]
    ma          = datos["ma"]
    encuestadoras = datos.get("encuestadoras", [])

    # Escaños del modelo según ámbito
    if "Nacional" in sel:
        modelo_esc = {p: escanos_nac.get(p, 0) for p in partidos}
    elif "CyL" in sel:
        modelo_esc = {p: escanos_cyl.get(p, 0) for p in partidos}
    else:
        # Para retroval o proyecciones sin modelo explícito:
        # usamos la media de encuestas como proxy del modelo base
        modelo_esc = dict(enc_media_esc)

    # ── Métricas de cabecera ────────────────────────────────────
    mae_val  = _mae(modelo_esc, enc_media_esc)
    rmse_val = _rmse(modelo_esc, enc_media_esc)
    prec_idx = _precision_index(rmse_val)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📅 Fecha elecciones", datos.get("fecha_elecciones", "N/D"))
    col2.metric("🏛️ Total escaños", total_esc)
    col3.metric("⚖️ Mayoría absoluta", ma)
    tipo_badge = "🔭 Proyección" if not es_retroval else "✅ Retrovalidación"
    col4.metric("Tipo", tipo_badge)

    st.divider()

    # ======================================================
    # SECCIÓN A — RETROVALIDACIÓN (Galicia 2024, Madrid 2023)
    # ======================================================
    if es_retroval:
        resultado_real = datos["resultado_real"]
        mae_enc  = _mae(enc_media_esc, resultado_real)
        rmse_enc = _rmse(enc_media_esc, resultado_real)
        prec_enc = _precision_index(rmse_enc)

        st.markdown("### 📐 Retrovalidación — Encuestas vs Resultado Real")

        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            st.plotly_chart(_gauge_precision(prec_enc, "Precisión media encuestas"), use_container_width=True, key=f"gauge_retro_{sel[:8]}")
        with c2:
            st.metric("MAE encuestas (escaños)", f"{mae_enc:.1f}")
            st.metric("RMSE encuestas (escaños)", f"{rmse_enc:.1f}")
            st.metric("Error medio estimado", f"±{mae_enc:.1f} esc.")
        with c3:
            # Tabla resultado real vs encuesta media
            filas = []
            for p in partidos:
                r = resultado_real.get(p, 0)
                e = enc_media_esc.get(p, 0)
                delta = e - r
                emoji = "✅" if abs(delta) <= 2 else ("⚠️" if abs(delta) <= 5 else "❌")
                filas.append({"Partido": p, "Real": r, "Enc.Media": e, "Δ": f"{delta:+d}", "": emoji})
            st.dataframe(pd.DataFrame(filas).set_index("Partido"), use_container_width=True)

        st.plotly_chart(
            _grafico_retroval(partidos, resultado_real, enc_media_esc, colores),
            use_container_width=True,
            key=f"retro_barras_{sel[:8]}"
        )

        # Encuestas por fuente
        st.markdown("### 🔍 Detalle por encuestadora")
        st.plotly_chart(
            _grafico_encuestas_fuente(partidos, encuestas, colores),
            use_container_width=True,
            key=f"retro_fuente_{sel[:8]}"
        )

        # Lecciones aprendidas de esta elección
        st.markdown("### 📖 Lecciones aprendidas de esta elección")
        hist_sel = [h for h in HISTORICO_PRECISION if sel.split("(")[0].strip().replace("🌿 ", "").replace("🏙️ ", "") in h["eleccion"]]
        if hist_sel:
            cols_lec = st.columns(len(hist_sel))
            for i, h in enumerate(hist_sel):
                with cols_lec[i]:
                    color = "🟢" if h["nota"] >= 75 else ("🟡" if h["nota"] >= 55 else "🔴")
                    st.markdown(f"**{h['encuestadora']}** {color}")
                    st.markdown(f"Nota: **{h['nota']}/100**")
                    st.markdown(f"MAE: {h['mae_escanos']} esc.")
                    st.caption(f"Sesgo: {h['sesgo']}")

    # ======================================================
    # SECCIÓN B — PROYECCIÓN FUTURA
    # ======================================================
    else:
        # Pesos encuestadoras
        st.markdown("### ⚖️ Pesos de encuestadoras")
        pesos = {}
        cols_pesos = st.columns(len(encuestadoras) if encuestadoras else 1)
        for i, fuente in enumerate(encuestadoras):
            with cols_pesos[i]:
                pesos[fuente] = st.slider(
                    fuente, 0.0, 1.0, 1.0, 0.05,
                    key=f"peso_{sel[:6]}_{fuente}"
                )

        # Recalcular media ponderada
        enc_media_pct = {}
        for p in partidos:
            enc_media_pct[p] = _media_ponderada(encuestas.get(p, {}), pesos)

        mae_val2  = _mae(modelo_esc, enc_media_esc)
        rmse_val2 = _rmse(modelo_esc, enc_media_esc)
        prec2     = _precision_index(rmse_val2)

        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            st.plotly_chart(_gauge_precision(prec2, "Precisión vs Encuestas"), use_container_width=True, key=f"gauge_proy_{sel[:8]}")
        with c2:
            st.metric("MAE modelo vs enc. (esc.)", f"{mae_val2:.1f}")
            st.metric("RMSE modelo vs enc. (esc.)", f"{rmse_val2:.1f}")

            # Alertas
            for p in partidos:
                delta_p = modelo_esc.get(p, 0) - enc_media_esc.get(p, 0)
                if abs(delta_p) >= 4:
                    st.warning(f"⚠️ {p}: Δ = {delta_p:+d} esc. — revisar proyección")
        with c3:
            filas = []
            for p in partidos:
                m = modelo_esc.get(p, 0)
                e = enc_media_esc.get(p, 0)
                delta = m - e
                emoji = "✅" if abs(delta) <= 2 else ("⚠️" if abs(delta) <= 5 else "❌")
                filas.append({"Partido": p, "Modelo": m, "Enc.Media": e, "Δ": f"{delta:+d}", "": emoji})
            st.dataframe(pd.DataFrame(filas).set_index("Partido"), use_container_width=True)

        st.markdown("### 📊 Comparativa escaños")
        st.plotly_chart(
            _grafico_comparativa(partidos, modelo_esc, enc_media_esc, colores),
            use_container_width=True,
            key=f"proy_comp_{sel[:8]}"
        )

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.plotly_chart(
                _grafico_delta(partidos, modelo_esc, enc_media_esc, colores),
                use_container_width=True,
                key=f"proy_delta_{sel[:8]}"
            )
        with col_d2:
            st.plotly_chart(
                _grafico_encuestas_fuente(partidos, encuestas, colores),
                use_container_width=True,
                key=f"proy_fuente_{sel[:8]}"
            )

    # ======================================================
    # SECCIÓN C — HISTÓRICO DE PRECISIÓN (siempre visible)
    # ======================================================
    st.divider()
    st.markdown("## 📈 Histórico de Precisión — Lecciones Aprendidas")
    st.caption("Precisión de encuestadoras en elecciones pasadas verificables · cuanto más alta la nota, mejor")

    tab_h1, tab_h2, tab_h3 = st.tabs(["🏆 Ranking global", "📉 Por elección", "🔥 Mapa de calor"])

    with tab_h1:
        col_r1, col_r2 = st.columns([2, 1])
        with col_r1:
            st.plotly_chart(_grafico_historico_precision(), use_container_width=True, key="hist_rank")
        with col_r2:
            df_h = pd.DataFrame(HISTORICO_PRECISION)
            medias = df_h.groupby("encuestadora")[["nota", "mae_escanos"]].mean().round(1).sort_values("nota", ascending=False)
            medias.columns = ["Nota media", "MAE medio"]
            st.markdown("**Resumen por encuestadora**")
            st.dataframe(medias, use_container_width=True)
            st.caption("Nota: máx 100. MAE = error medio en escaños.")

    with tab_h2:
        st.plotly_chart(_grafico_precision_por_eleccion(), use_container_width=True, key="hist_scatter")
        # Tabla detalle
        df_h2 = pd.DataFrame(HISTORICO_PRECISION)[["eleccion", "encuestadora", "nota", "mae_escanos", "sesgo"]]
        df_h2 = df_h2.sort_values(["eleccion", "nota"], ascending=[True, False])
        df_h2.columns = ["Elección", "Encuestadora", "Nota", "MAE (esc.)", "Sesgo detectado"]
        st.dataframe(df_h2.reset_index(drop=True), use_container_width=True)

    with tab_h3:
        st.plotly_chart(_grafico_sesgo_sistematico(), use_container_width=True, key="hist_heatmap")

        # Lecciones automáticas globales
        df_all = pd.DataFrame(HISTORICO_PRECISION)
        bajas  = df_all[df_all["nota"] < 55]
        st.markdown("### 🔴 Alertas de sesgo sistemático")
        if len(bajas) > 0:
            for _, row in bajas.iterrows():
                st.error(f"**{row['encuestadora']}** en {row['eleccion']}: nota {row['nota']}/100 — {row['sesgo']}")
        else:
            st.success("No se detectan sesgos sistemáticos graves en el histórico.")

        mejores = df_all.groupby("encuestadora")["nota"].mean().sort_values(ascending=False)
        st.markdown("### 🥇 Encuestadoras más fiables (media histórica)")
        for enc, nota in mejores.items():
            stars = "⭐" * max(1, min(5, int(nota / 20)))
            color = "🟢" if nota >= 75 else ("🟡" if nota >= 55 else "🔴")
            st.markdown(f"{color} **{enc}**: {nota:.0f}/100 {stars}")

def render_tab_andalucia(escanos_and, datos_prov_and,
                          polarizacion_and, nep_and, lsq_and,
                          factor_desempleo_and, factor_vivienda_and,
                          factor_agua, factor_rural_urbano):
    """Renderiza el tab completo de Andalucía."""

    st.header("🌞 Andalucía — Laboratorio Electoral Autonómico")
    st.markdown("""
    > **Contexto:** Andalucía es la CCAA más poblada (8.5M electores) y el principal
    > campo de batalla electoral de España. El PP ostenta mayoría absoluta desde 2022,
    > rompiendo 40 años de hegemonía socialista. Este módulo simula la evolución
    > de la intención de voto bajo distintos escenarios estructurales.
    """)

    ma_and = (TOTAL_AND // 2) + 1  # 55

    # ---- KPIs
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("NEP Andalucía", nep_and,
                help="Número Efectivo de Partidos")
    col2.metric("Polarización", f"{polarizacion_and:.3f}")
    col3.metric("Gallagher (LSq)", f"{lsq_and:.1f}",
                help="Desproporcionalidad votos→escaños")
    col4.metric("Diputados totales", TOTAL_AND)

    st.markdown("---")

    # ---- COMPOSICIÓN ACTUAL vs PROYECCIÓN
    st.subheader("📊 Composición Real 2022 vs. Proyección Simulada")
    col_act, col_sim = st.columns(2)

    with col_act:
        st.markdown("**Parlamento de Andalucía 2022 (Real)**")
        df_actual = pd.DataFrame({
            "Partido":     list(AND_COMPOSICION_ACTUAL.keys()),
            "Diputados":   list(AND_COMPOSICION_ACTUAL.values())
        })
        df_actual = df_actual[df_actual["Diputados"] > 0]
        fig_act = px.bar(df_actual, x="Partido", y="Diputados",
                         color="Partido", color_discrete_map=COLORES_AND,
                         text="Diputados", title="Resultado Real 2022")
        fig_act.update_traces(textposition="outside")
        fig_act.add_hline(y=ma_and, line_dash="dash", line_color="red",
                          annotation_text=f"Mayoría Absoluta ({ma_and})")
        st.plotly_chart(fig_act, width='stretch')
        pp_r = AND_COMPOSICION_ACTUAL["PP"]
        st.success(f"**Gobierno actual:** PP ({pp_r}) — mayoría absoluta  |  MA: {ma_and}")

    with col_sim:
        st.markdown("**Proyección Simulada (Escenario Actual)**")
        df_sim = pd.DataFrame({
            "Partido":   list(escanos_and.keys()),
            "Diputados": list(escanos_and.values())
        })
        df_sim = df_sim[df_sim["Diputados"] > 0].sort_values("Diputados", ascending=False)
        fig_sim = px.bar(df_sim, x="Partido", y="Diputados",
                         color="Partido", color_discrete_map=COLORES_AND,
                         text="Diputados", title="Simulación Actual")
        fig_sim.update_traces(textposition="outside")
        fig_sim.add_hline(y=ma_and, line_dash="dash", line_color="red",
                          annotation_text=f"Mayoría Absoluta ({ma_and})")
        st.plotly_chart(fig_sim, width='stretch')
        total_sim = sum(escanos_and.values())
        pp_sim_v = escanos_and.get("PP", 0)
        estado = "✅ Mayoría absoluta" if pp_sim_v >= ma_and else f"❌ PP necesita {ma_and - pp_sim_v} más"
        st.info(f"**PP simulado:** {pp_sim_v} escaños — {estado}")

    # ---- DELTA
    st.subheader("🔄 Variación Estimada respecto a 2022")
    # Mapeo de nombres entre composición actual y partidos simulados
    mapeo = {"PP":"PP","PSOE":"PSOE","VOX":"VOX",
             "Por Andalucía":"Por Andalucía","Cs":"OTROS","OTROS":"OTROS"}
    delta_data = []
    for p in PARTIDOS_AND:
        actual_v  = AND_COMPOSICION_ACTUAL.get(p, 0)
        simulado_v = escanos_and.get(p, 0)
        delta = simulado_v - actual_v
        delta_data.append({
            "Partido": p,
            "2022 (Real)": actual_v,
            "Simulado": simulado_v,
            "Δ Cambio": delta
        })
    df_delta = pd.DataFrame(delta_data)
    fig_delta = px.bar(df_delta, x="Partido", y="Δ Cambio",
                       color="Δ Cambio", color_continuous_scale="RdYlGn",
                       title="Variación de Escaños respecto a 2022",
                       text="Δ Cambio")
    fig_delta.add_hline(y=0, line_color="black", line_width=1)
    fig_delta.update_traces(textposition="outside")
    st.plotly_chart(fig_delta, width='stretch')

    # ---- DESGLOSE PROVINCIAL
    st.subheader("🗺️ Desglose Provincial Andalucía")
    prov_sel = st.selectbox("Provincia andaluza", list(ESCANOS_AND.keys()),
                             key="selectbox_and")
    dp_and = next(d for d in datos_prov_and if d["Provincia"] == prov_sel)

    col_pv, col_pe = st.columns(2)
    with col_pv:
        st.markdown(f"**Intención de Voto — {prov_sel}**")
        df_v = pd.DataFrame({
            "Partido":  list(dp_and["Votos"].keys()),
            "Voto (%)": list(dp_and["Votos"].values())
        })
        df_v = df_v[df_v["Voto (%)"] > 0.5].sort_values("Voto (%)", ascending=True)
        fig_v = go.Figure(go.Bar(
            x=df_v["Voto (%)"], y=df_v["Partido"], orientation="h",
            marker_color=[COLORES_AND.get(p, "#999") for p in df_v["Partido"]],
            text=df_v["Voto (%)"].round(1), textposition="outside"
        ))
        fig_v.update_layout(height=300, xaxis_title="% Voto")
        st.plotly_chart(fig_v, width='stretch')

    with col_pe:
        st.markdown(f"**Reparto D'Hondt — {prov_sel} ({ESCANOS_AND[prov_sel]} diputados)**")
        rep = {p: v for p, v in dp_and["Reparto"].items() if v > 0}
        if rep:
            fig_e = px.pie(values=list(rep.values()), names=list(rep.keys()),
                           color=list(rep.keys()),
                           color_discrete_map=COLORES_AND, hole=0.4)
            st.plotly_chart(fig_e, width='stretch')

    # ---- COALICIONES
    st.subheader("🤝 Análisis de Coaliciones — Parlamento de Andalucía")
    pp_s   = escanos_and.get("PP", 0)
    psoe_s = escanos_and.get("PSOE", 0)
    vox_s  = escanos_and.get("VOX", 0)
    pa_s   = escanos_and.get("Por Andalucía", 0)

    coaliciones = {
        "PP solo":              pp_s,
        "PP + VOX":             pp_s + vox_s,
        "PSOE + Por Andalucía": psoe_s + pa_s,
        "PSOE + VOX":           psoe_s + vox_s,   # escenario antinatural, referencia
        "Bloque progresista\n(PSOE+PA+otros)": psoe_s + pa_s + 2,
    }
    df_coal = pd.DataFrame({
        "Coalición":   list(coaliciones.keys()),
        "Diputados":   list(coaliciones.values())
    })
    df_coal["¿Mayoría?"] = df_coal["Diputados"].apply(
        lambda x: "✅ Mayoría" if x >= ma_and else f"❌ Faltan {ma_and - x}"
    )
    fig_coal = px.bar(df_coal, x="Coalición", y="Diputados",
                      text="Diputados", color="Diputados",
                      color_continuous_scale="Blues",
                      title=f"Escenarios de Coalición (MA: {ma_and})")
    fig_coal.add_hline(y=ma_and, line_dash="dash", line_color="red")
    fig_coal.update_traces(textposition="outside")
    st.plotly_chart(fig_coal, width='stretch')
    st.dataframe(df_coal, width='stretch')

    # ---- RADAR VARIABLES ESTRUCTURALES
    st.subheader("📡 Variables Estructurales Andalucía")
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        cat_and = ["Desempleo", "Vivienda/Turismo", "Agua/Sequía",
                   "Rural vs Urbano", "Fiabilidad"]
        val_and = [factor_desempleo_and, factor_vivienda_and,
                   factor_agua, factor_rural_urbano, fiabilidad]
        fig_rad = go.Figure(go.Scatterpolar(
            r=val_and, theta=cat_and, fill="toself",
            line_color="#d62728", name="Andalucía"
        ))
        fig_rad.update_layout(
            polar=dict(radialaxis=dict(range=[0, 100])),
            title="Perfil de Riesgo Electoral Andalucía"
        )
        st.plotly_chart(fig_rad, width='stretch')

    with col_r2:
        # Heatmap votos por provincia
        votos_matrix = []
        for dp in datos_prov_and:
            row = {"Provincia": dp["Provincia"]}
            for p in PARTIDOS_AND:
                row[p] = round(dp["Votos"].get(p, 0), 1)
            votos_matrix.append(row)
        df_heat = pd.DataFrame(votos_matrix).set_index("Provincia")
        fig_heat = px.imshow(df_heat, color_continuous_scale="RdYlBu_r",
                             title="% Intención de Voto por Provincia",
                             text_auto=True)
        st.plotly_chart(fig_heat, width='stretch')

    # ---- NOTA METODOLÓGICA
    with st.expander("📋 Nota Metodológica — Módulo Andalucía"):
        st.markdown(f"""
**Circunscripciones:** 8 provincias | **Total diputados:** {TOTAL_AND} | **Mayoría absoluta:** {ma_and}  
**Umbral electoral:** 3% por circunscripción (Ley Electoral de Andalucía)  
**Base de intención de voto:** Estimación estructural 2026 con ajuste provincial  

**Variables estructurales específicas:**
- **Desempleo:** Andalucía ~16% vs 11% nacional. Penaliza gobierno PP, moviliza voto de izquierda.
- **Vivienda/Turismo:** Tensión en costa (Málaga, Cádiz). Sube alquiler turístico → erosión voto urbano PP.
- **Agua/Sequía:** Variable crítica en Almería, Granada, Jaén. Moviliza voto rural conservador.
- **Rural vs Urbano:** Interior (Jaén, Huelva, Córdoba) muy distinto de costa (Málaga, Cádiz).

**Perfiles provinciales:**
- **Almería:** PP+VOX muy fuertes. Agricultura intensiva. Mayor efecto sequía.
- **Cádiz:** PSOE+Por Andalucía fuertes. Industrial-naval. Más polarizado.
- **Málaga:** PP hegemónico. Turismo. Clase media-alta costera.
- **Sevilla:** Capital política. PSOE competitivo. Más urbano y equilibrado.
- **Jaén/Huelva:** Interior rural. PSOE histórico pero erosionado. Alto desempleo.

**Limitaciones:**
- Sin encuestas autonómicas andaluzas recientes en el modelo
- Cs en liquidación → votos redistribuidos en OTROS
- Alta volatilidad en provincias pequeñas (Huelva, Jaén) por tamaño muestral
        """)
# ===============================
# EJECUCIÓN — CÁLCULO ANDALUCÍA
# ===============================
escanos_and, datos_prov_and = calcular_and(
    factor_desempleo_and, factor_vivienda_and,
    factor_agua, factor_rural_urbano, umbral_and
)
votos_and_avg = {p: sum(d["Votos"].get(p,0) for d in datos_prov_and)/len(datos_prov_and)
                 for p in PARTIDOS_AND}
polarizacion_and = calcular_indice_polarizacion(votos_and_avg)
nep_and          = calcular_indice_fragmentacion(escanos_and)
lsq_and          = calcular_sesgo_sistema(votos_and_avg, escanos_and)
ma_and           = (TOTAL_AND // 2) + 1



# ===============================
# EJECUCIÓN — CÁLCULO GALICIA
# ===============================
escanos_gal, datos_prov_gal = calcular_gal(
    factor_despoblacion_gal, factor_bng_urbano,
    factor_pesca, factor_autogobierno_gal, umbral_gal
)
votos_gal_avg = {p: sum(d["Votos"].get(p,0) for d in datos_prov_gal)/len(datos_prov_gal)
                 for p in PARTIDOS_GAL}
polarizacion_gal = calcular_indice_polarizacion(votos_gal_avg)
nep_gal          = calcular_indice_fragmentacion(escanos_gal)
lsq_gal          = calcular_sesgo_sistema(votos_gal_avg, escanos_gal)

# ===============================
# EJECUCIÓN — CÁLCULO EUSKADI
# ===============================
escanos_eus, datos_terr_eus = calcular_eus(
    factor_independentismo, factor_izq_abertzale,
    factor_economia_vasca, factor_concierto_eco, umbral_eus
)
votos_eus_avg = {p: sum(d["Votos"].get(p,0) for d in datos_terr_eus)/len(datos_terr_eus) for p in PARTIDOS_EUS}
polarizacion_eus = calcular_indice_polarizacion(votos_eus_avg)
nep_eus          = calcular_indice_fragmentacion(escanos_eus)
lsq_eus          = calcular_sesgo_sistema(votos_eus_avg, escanos_eus)

# ===============================
# EJECUCIÓN — CÁLCULO MADRID
# ===============================
reparto_mad, votos_mad, datos_zonas_mad = calcular_mad(
    factor_vivienda_mad, factor_ayuso, factor_fiscal, factor_migracion, umbral_mad
)
polarizacion_mad = calcular_indice_polarizacion(votos_mad)
nep_mad          = calcular_indice_fragmentacion(reparto_mad)
lsq_mad          = calcular_sesgo_sistema(votos_mad, reparto_mad)
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11 = st.tabs([
    "🏛️ Hemiciclo Nacional",
    "🗺️ Desglose Provincial",
    "📡 Radar Estratégico",
    "📋 Metodología y Fuentes",
    "📈 Histórico Semanal",
    "🏰 Castilla y León — Lab. Electoral",
    "🌞 Andalucía — Lab. Electoral",
    "🌿 Galicia — Lab. Electoral",
    "🏙️ Madrid — Lab. Electoral",
    "🧠 Auditoría & Aprendizaje",
    "🏴󠁥󠁳󠁰󠁶󠁿 Euskadi — Lab. Electoral",
])

# ========== TAB 1: HEMICICLO NACIONAL ==========
with tab1:
    st.subheader("Proyección de Escaños — Congreso de los Diputados")

    # Métricas KPI en columnas
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("NEP (Laakso-Taagepera)", nep_nac,
                help="Número Efectivo de Partidos. <2.5 dominante | 2.5-4 moderado | >4 fragmentado")
    col2.metric("Polarización (HHI)", f"{polarizacion_nac:.3f}",
                help="0=baja polarización, 1=máxima polarización")
    col3.metric("Índice Gallagher (LSq)", f"{lsq_nac:.1f}",
                help="Desproporcionalidad. 0=perfecto | >10=muy distorsionado")
    col4.metric("Mayoría Absoluta", "176 escaños")

    # Gráfico de barras
    df_hemi = pd.DataFrame({"Partido": list(escanos_totales.keys()),
                             "Escaños": list(escanos_totales.values())})
    df_hemi = df_hemi[df_hemi["Escaños"] > 0].sort_values("Escaños", ascending=False)
    fig = px.bar(df_hemi, x="Partido", y="Escaños", color="Partido",
                 color_discrete_map=PARTIDOS_COLORES, text="Escaños")
    fig.add_hline(y=176, line_dash="dash", line_color="red", annotation_text="Mayoría Absoluta (176)")
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, width='stretch')

    # Panel de gobernabilidad
    st.subheader("🤝 Análisis de Gobernabilidad y Coaliciones")
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.markdown("**Bloques Parlamentarios**")
        for k, v in gobernabilidad_nac.items():
            if "Distancia" in k or "posible" in k:
                continue
            icono = "🔵" if "Derecha" in k or "PP" in k else "🔴"
            st.write(f"{icono} **{k}**: {v} escaños")
    with col_g2:
        st.markdown("**Viabilidad de Gobierno**")
        for k, v in gobernabilidad_nac.items():
            if "Gobierno posible" in k:
                emoji = "✅" if v else "❌"
                st.write(f"{emoji} {k}")
            if "Distancia" in k:
                color = "🟢" if v <= 10 else ("🟡" if v <= 30 else "🔴")
                st.write(f"{color} {k}: {v} escaños restantes")

    st.write(f"**Total escaños:** {df_hemi['Escaños'].sum()} / 350")


    # ---- HEMICICLO VISUAL — Herradura + Donut
    st.markdown("---")
    st.subheader("🏛️ Hemiciclo Visual — Proyección vs. Resultado Real 2023")

    # Resultado real 2023 (composición actual del Congreso)
    REAL_2023 = {
        "PP":    137,
        "PSOE":  121,
        "VOX":    33,
        "SUMAR":  31,
        "ERC":     7,
        "JUNTS":   7,
        "BILDU":   6,
        "PNV":     5,
        "CC":      1,
        "BNG":     1,
        "UPN":     1,
        "OTROS":   0,
        "SALF":    0,
    }

    col_h1, col_h2 = st.columns(2)
    with col_h1:
        fig_herr_sim = hacer_herradura(
            escanos_totales, PARTIDOS_COLORES,
            "Proyección Simulada — Herradura"
        )
        st.plotly_chart(fig_herr_sim, width="stretch", key="herr_sim")

    with col_h2:
        fig_herr_real = hacer_herradura(
            REAL_2023, PARTIDOS_COLORES,
            "Resultado Real 2023 — Herradura"
        )
        st.plotly_chart(fig_herr_real, width="stretch", key="herr_real")

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        fig_donut_sim = hacer_donut(
            escanos_totales, PARTIDOS_COLORES,
            "Proyección Simulada — Composición"
        )
        st.plotly_chart(fig_donut_sim, width="stretch", key="donut_sim")

    with col_d2:
        fig_donut_real = hacer_donut(
            REAL_2023, PARTIDOS_COLORES,
            "Resultado Real 2023 — Composición"
        )
        st.plotly_chart(fig_donut_real, width="stretch", key="donut_real")

# ========== TAB 2: DESGLOSE PROVINCIAL ==========
with tab2:
    st.subheader("Desglose Provincial — Voto y Reparto D'Hondt")
    provincia_sel = st.selectbox("Selecciona provincia", PROVINCIAS)
    dp = next(d for d in datos_prov if d["Provincia"] == provincia_sel)

    col_v, col_e = st.columns(2)
    with col_v:
        st.markdown(f"**Intención de Voto — {provincia_sel}**")
        df_votos = pd.DataFrame({"Partido": list(dp["Votos"].keys()),
                                  "Voto (%)": list(dp["Votos"].values())})
        df_votos = df_votos[df_votos["Voto (%)"] > 0.5].sort_values("Voto (%)", ascending=True)
        fig_v = go.Figure(go.Bar(
            x=df_votos["Voto (%)"], y=df_votos["Partido"], orientation="h",
            marker_color=[PARTIDOS_COLORES.get(p, "#999") for p in df_votos["Partido"]],
            text=df_votos["Voto (%)"].round(1), textposition="outside"
        ))
        fig_v.update_layout(height=400, xaxis_title="% Voto")
        st.plotly_chart(fig_v, width='stretch')

    with col_e:
        st.markdown(f"**Escaños D'Hondt — {provincia_sel} ({ESCANOS[provincia_sel]} diputados)**")
        rep = {p: v for p, v in dp["Reparto"].items() if v > 0}
        fig_e = px.pie(values=list(rep.values()), names=list(rep.keys()),
                       color=list(rep.keys()),
                       color_discrete_map=PARTIDOS_COLORES, hole=0.4)
        st.plotly_chart(fig_e, width='stretch')

    st.markdown("**Tabla de Reparto:**")
    df_rep = pd.DataFrame([{"Partido": p, "Escaños": v, "% Voto": round(dp["Votos"].get(p, 0), 2)}
                            for p, v in dp["Reparto"].items() if v > 0])
    st.dataframe(df_rep.sort_values("Escaños", ascending=False), width='stretch')

# ========== TAB 3: RADAR ESTRATÉGICO ==========
with tab3:
    st.subheader("📡 Radar Estratégico Multidimensional")
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        categorias = ["Vivienda", "Energía", "Fiabilidad", "Despoblación CyL", "Cuestión Leonesa"]
        valores = [factor_vivienda, factor_energia, fiabilidad, factor_despoblacion, factor_cuestion_leonesa]
        fig_radar = go.Figure(go.Scatterpolar(r=valores, theta=categorias, fill="toself",
                                              line_color="#1f77b4", name="Escenario Actual"))
        fig_radar.update_layout(polar=dict(radialaxis=dict(range=[0, 100])),
                                title="Variables de Escenario")
        st.plotly_chart(fig_radar, width='stretch')
    with col_r2:
        # Radar de partidos por dimensión (perfil ideológico)
        partidos_radar = ["PP", "PSOE", "VOX", "SUMAR", "SALF"]
        dim_radar = ["Urbano", "Rural", "Jóvenes", "Mayores", "Clase Media"]
        # Scores simulados estructurales (no aleatorios, fijos)
        perfil = {
            "PP":    [55, 70, 30, 75, 65],
            "PSOE":  [70, 50, 55, 60, 60],
            "VOX":   [40, 65, 35, 55, 45],
            "SUMAR": [75, 25, 70, 35, 55],
            "SALF":  [60, 55, 45, 50, 55],
        }
        fig_per = go.Figure()
        for partido in partidos_radar:
            fig_per.add_trace(go.Scatterpolar(
                r=perfil[partido] + [perfil[partido][0]], theta=dim_radar + [dim_radar[0]],
                fill="toself", name=partido,
                line_color=PARTIDOS_COLORES[partido], opacity=0.6
            ))
        fig_per.update_layout(polar=dict(radialaxis=dict(range=[0, 100])),
                              title="Perfil Electoral por Segmento")
        st.plotly_chart(fig_per, width='stretch')

    # Heatmap de volatilidad
    st.subheader("🌡️ Mapa de Calor — Intención de Voto por Partido")
    votos_matrix = []
    for dp in datos_prov[:15]:  # muestra 15 provincias para legibilidad
        row = {"Provincia": dp["Provincia"]}
        for p in ["PP", "PSOE", "VOX", "SUMAR"]:
            row[p] = round(dp["Votos"].get(p, 0), 1)
        votos_matrix.append(row)
    df_heat = pd.DataFrame(votos_matrix).set_index("Provincia")
    fig_heat = px.imshow(df_heat, color_continuous_scale="RdYlBu_r",
                         title="% Intención de Voto por Provincia (muestra 15 prov.)",
                         text_auto=True)
    st.plotly_chart(fig_heat, width='stretch')

# ========== TAB 4: METODOLOGÍA ==========
with tab4:
    st.header("🏗️ Arquitectura del Modelo")
    st.markdown("""
**Pipeline de Cálculo:**

1. **Ajuste Nacional Base** — Ponderación de encuestas y resultados históricos  
2. **Ajuste de Escenario** — Impacto de variables estructurales (vivienda, energía)  
3. **Ajuste Territorial Provincial** — Correcciones por especificidad regional  
4. **Ruido Estadístico** — Función del coeficiente de incertidumbre configurable  
5. **Umbral Electoral** — Filtrado de partidos bajo mínimo legal  
6. **Método D'Hondt** — Distribución proporcional de escaños por circunscripción  
7. **Proyección Consolidada** — Agregación y ajuste a 350 escaños  
""")

    fig_flow = go.Figure(go.Sankey(
        node=dict(
            label=["Encuestas", "Histórico Electoral", "Ajuste Nacional",
                   "Ajuste Territorial", "Ruido Estadístico", "D'Hondt", "Proyección Final"],
            color=["#1f77b4", "#d62728", "#ff7f0e", "#2ca02c", "#9467bd", "#8c564b", "#17becf"]
        ),
        link=dict(
            source=[0, 1, 2, 3, 4, 5],
            target=[2, 2, 3, 4, 5, 6],
            value=[1, 1, 1, 1, 1, 1],
            color=["rgba(31,119,180,0.4)"] * 6
        )
    ))
    fig_flow.update_layout(title="Flujo de Datos del Modelo")
    st.plotly_chart(fig_flow, width='stretch')

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.header("📐 Métricas Implementadas")
        st.markdown("""
**Índice de Gallagher (LSq)**  
Mide desproporcionalidad entre votos y escaños.  
`LSq = √(0.5 × Σ(vi − si)²)`  
Rango: 0 (proporcional) → valores altos (distorsionado)

**NEP — Laakso-Taagepera**  
Número Efectivo de Partidos.  
`NEP = 1 / Σ(pi²)`  
<2.5: bipartidismo | 2.5-4: pluralismo | >4: fragmentado

**Polarización HHI**  
Concentración del voto.  
`HHI = Σ(pi²)` normalizado  
0=distribuido | 1=concentrado

**Volatilidad (σ semanal)**  
Desviación estándar del voto en ventana temporal.
""")

    with col_m2:
        st.header("🗂️ Gestión de Fuentes")
        st.markdown("""
**Fuentes utilizadas:**  
• Resultados electorales históricos (BOE, INE)  
• Encuestas CIS y privadas publicadas  
• Datos institucionales (ministerios, autonomías)  
• Ajustes estructurales internos del modelo  

**Auditoría y Control:**  
• Validación semanal del histórico  
• Monitorización de eventos de alto impacto  
• Revisión de coherencia territorial  
• Evaluación de desviaciones vs. resultados reales  

**Limitaciones:**  
• Modelo probabilístico, no determinista  
• Alta sensibilidad a eventos exógenos  
• No sustituye el escrutinio oficial  
• Ruido estadístico calibrable por el operador  
""")

# ========== TAB 5: HISTÓRICO SEMANAL ==========
with tab5:
    st.subheader("📈 Tendencias Temporales — Histórico Nacional")
    if not df_hist.empty:
        df_hist["Fecha"] = pd.to_datetime(df_hist["Fecha"])
        df_nacional = df_hist.groupby(["Fecha", "Partido"])["Votos"].mean().reset_index()
        fig_trend = go.Figure()
        for p in PARTIDOS:
            df_p = df_nacional[df_nacional["Partido"] == p]
            if not df_p.empty:
                vol = calcular_volatilidad(df_nacional[df_nacional["Partido"] == p].rename(
                    columns={"Votos": "Votos"}), p)
                fig_trend.add_trace(go.Scatter(
                    x=df_p["Fecha"], y=df_p["Votos"],
                    mode="lines+markers", name=f"{p} (σ={vol})",
                    line=dict(color=PARTIDOS_COLORES.get(p, "#999"), width=3)
                ))
        # Zoom en rango real de variación — evita línea plana
        all_vals = df_nacional["Votos"].dropna()
        y_min = max(0, all_vals.min() - 1.5)
        y_max = all_vals.max() + 1.5
        fig_trend.update_layout(height=500, hovermode="x unified",
                                title="Evolución semanal de intención de voto (%)",
                                yaxis_title="% Intención de Voto",
                                yaxis=dict(range=[y_min, y_max]))
        st.plotly_chart(fig_trend, width='stretch')

    # Métricas de volatilidad
    if not df_hist.empty:
        st.subheader("📊 Volatilidad por Partido")
        df_hist_vol = df_hist.copy()
        df_hist_vol["Fecha"] = pd.to_datetime(df_hist_vol["Fecha"])
        df_nac_vol = df_hist_vol.groupby(["Fecha", "Partido"])["Votos"].mean().reset_index()
        vol_data = []
        for p in PARTIDOS:
            df_p = df_nac_vol[df_nac_vol["Partido"] == p]
            vol = calcular_volatilidad(df_p, p)
            mean_v = df_p["Votos"].mean() if not df_p.empty else 0
            vol_data.append({"Partido": p, "Volatilidad (σ)": vol, "Media %": round(mean_v, 2)})
        df_vol = pd.DataFrame(vol_data).sort_values("Volatilidad (σ)", ascending=False)
        fig_vol = px.bar(df_vol, x="Partido", y="Volatilidad (σ)", color="Partido",
                         color_discrete_map=PARTIDOS_COLORES, title="Volatilidad Semanal por Partido")
        st.plotly_chart(fig_vol, width='stretch')

    st.dataframe(df_hist.sort_values("Fecha", ascending=False), width='stretch')

# ========== TAB 6: CASTILLA Y LEÓN ==========
with tab6:
    st.header("🏰 Castilla y León — Laboratorio Electoral Autonómico")
    st.markdown("""
    > **Contexto:** CyL presenta un sistema de partidos con hegemonía histórica del PP,  
    > tensión territorial leonesa, y alta dependencia del voto rural y envejecido.  
    > Este módulo simula intención de voto y composición parlamentaria bajo distintos escenarios.
    """)

    # KPIs CyL
    col_c1, col_c2, col_c3, col_c4 = st.columns(4)
    col_c1.metric("NEP CyL", nep_cyl,
                  help="Número Efectivo de Partidos en Cortes de CyL")
    col_c2.metric("Polarización CyL", f"{polarizacion_cyl:.3f}")
    col_c3.metric("Gallagher CyL", f"{lsq_cyl:.1f}",
                  help="Índice de desproporcionalidad del sistema electoral de CyL")
    col_c4.metric("Procuradores", TOTAL_CYL)

    st.markdown("---")

    # ---- COMPOSICIÓN ACTUAL vs PROYECCIÓN
    st.subheader("📊 Composición Actual (2022) vs. Proyección Simulada")
    col_act, col_sim = st.columns(2)
    with col_act:
        st.markdown("**Cortes de Castilla y León 2022 (Real)**")
        df_actual = pd.DataFrame({
            "Partido": list(CYL_COMPOSICION_ACTUAL.keys()),
            "Procuradores": list(CYL_COMPOSICION_ACTUAL.values())
        })
        fig_act = px.bar(df_actual, x="Partido", y="Procuradores",
                         color="Partido", color_discrete_map=COLORES_CYL,
                         text="Procuradores", title="Resultado Real 2022")
        fig_act.update_traces(textposition='outside')
        ma_cyl = (TOTAL_CYL // 2) + 1
        fig_act.add_hline(y=ma_cyl, line_dash="dash", line_color="red",
                          annotation_text=f"Mayoría Absoluta ({ma_cyl})")
        st.plotly_chart(fig_act, width='stretch')
        # Análisis de gobierno actual
        pp_actual = CYL_COMPOSICION_ACTUAL.get("PP", 0)
        vox_actual = CYL_COMPOSICION_ACTUAL.get("VOX", 0)
        st.info(f"**Gobierno actual:** PP ({pp_actual}) + VOX ({vox_actual}) = {pp_actual + vox_actual} procuradores  |  Mayoría Absoluta: {ma_cyl}")

    with col_sim:
        st.markdown("**Proyección Simulada (Escenario Actual)**")
        df_sim = pd.DataFrame({
            "Partido": list(escanos_cyl.keys()),
            "Procuradores": list(escanos_cyl.values())
        })
        df_sim = df_sim[df_sim["Procuradores"] > 0].sort_values("Procuradores", ascending=False)
        fig_sim = px.bar(df_sim, x="Partido", y="Procuradores",
                         color="Partido", color_discrete_map=COLORES_CYL,
                         text="Procuradores", title="Simulación Actual")
        fig_sim.update_traces(textposition='outside')
        fig_sim.add_hline(y=ma_cyl, line_dash="dash", line_color="red",
                          annotation_text=f"Mayoría Absoluta ({ma_cyl})")
        st.plotly_chart(fig_sim, width='stretch')
        total_sim = sum(escanos_cyl.values())
        st.write(f"**Total simulado:** {total_sim} procuradores")

    # ---- DELTA: CAMBIO NETO ESTIMADO
    st.subheader("🔄 Variación Estimada respecto a 2022")
    delta_data = []
    for p in PARTIDOS_CYL:
        actual = CYL_COMPOSICION_ACTUAL.get(p, 0)
        simulado = escanos_cyl.get(p, 0)
        delta = simulado - actual
        delta_data.append({"Partido": p, "2022 (Real)": actual,
                            "Simulado": simulado, "Δ Cambio": delta})
    df_delta = pd.DataFrame(delta_data)
    fig_delta = px.bar(df_delta, x="Partido", y="Δ Cambio", color="Δ Cambio",
                       color_continuous_scale="RdYlGn",
                       title="Variación de Escaños respecto a 2022",
                       text="Δ Cambio")
    fig_delta.add_hline(y=0, line_color="black", line_width=1)
    fig_delta.update_traces(textposition='outside')
    st.plotly_chart(fig_delta, width='stretch')

    # ---- DESGLOSE PROVINCIAL CYL
    st.subheader("🗺️ Desglose Provincial CyL")
    prov_sel_cyl = st.selectbox("Provincia CyL", list(ESCANOS_CYL.keys()))
    dp_cyl = next(d for d in datos_prov_cyl if d["Provincia"] == prov_sel_cyl)

    col_pv, col_pe = st.columns(2)
    with col_pv:
        st.markdown(f"**Intención de Voto — {prov_sel_cyl}**")
        df_v_cyl = pd.DataFrame({"Partido": list(dp_cyl["Votos"].keys()),
                                  "Voto (%)": list(dp_cyl["Votos"].values())})
        df_v_cyl = df_v_cyl[df_v_cyl["Voto (%)"] > 0.5].sort_values("Voto (%)", ascending=True)
        fig_vc = go.Figure(go.Bar(
            x=df_v_cyl["Voto (%)"], y=df_v_cyl["Partido"], orientation="h",
            marker_color=[COLORES_CYL.get(p, "#999") for p in df_v_cyl["Partido"]],
            text=df_v_cyl["Voto (%)"].round(1), textposition="outside"
        ))
        fig_vc.update_layout(height=300, xaxis_title="% Voto")
        st.plotly_chart(fig_vc, width='stretch')
    with col_pe:
        st.markdown(f"**Reparto D'Hondt — {prov_sel_cyl} ({ESCANOS_CYL[prov_sel_cyl]} proc.)**")
        rep_cyl = {p: v for p, v in dp_cyl["Reparto"].items() if v > 0}
        if rep_cyl:
            fig_ec = px.pie(values=list(rep_cyl.values()), names=list(rep_cyl.keys()),
                            color=list(rep_cyl.keys()), color_discrete_map=COLORES_CYL, hole=0.4)
            st.plotly_chart(fig_ec, width='stretch')

    # ---- ANÁLISIS DE COALICIONES CYL
    st.subheader("🤝 Análisis de Coaliciones — Cortes de CyL")
    pp_sim = escanos_cyl.get("PP", 0)
    psoe_sim = escanos_cyl.get("PSOE", 0)
    vox_sim = escanos_cyl.get("VOX", 0)
    sumar_sim = escanos_cyl.get("SUMAR", 0)
    upl_sim = escanos_cyl.get("UPL", 0)
    pav_sim = escanos_cyl.get("Por Ávila", 0)

    coaliciones = {
        "PP solo": pp_sim,
        "PP + VOX": pp_sim + vox_sim,
        "PP + Por Ávila": pp_sim + pav_sim,
        "PP + VOX + Por Ávila": pp_sim + vox_sim + pav_sim,
        "PSOE + SUMAR + UPL": psoe_sim + sumar_sim + upl_sim,
        "PSOE + SUMAR + UPL + otros": psoe_sim + sumar_sim + upl_sim + 2,
    }

    df_coal = pd.DataFrame({"Coalición": list(coaliciones.keys()),
                             "Procuradores": list(coaliciones.values())})
    df_coal["¿Mayoría?"] = df_coal["Procuradores"].apply(
        lambda x: "✅ Mayoría" if x >= ma_cyl else f"❌ Faltan {ma_cyl - x}")
    fig_coal = px.bar(df_coal, x="Coalición", y="Procuradores",
                      text="Procuradores", color="Procuradores",
                      color_continuous_scale="Blues",
                      title=f"Escenarios de Coalición (Mayoría Absoluta: {ma_cyl})")
    fig_coal.add_hline(y=ma_cyl, line_dash="dash", line_color="red")
    fig_coal.update_traces(textposition='outside')
    st.plotly_chart(fig_coal, width='stretch')
    st.dataframe(df_coal, width='stretch')

    # ---- RADAR DE VARIABLES ESTRUCTURALES CYL
    st.subheader("📡 Variables Estructurales CyL")
    cat_cyl = ["Despoblación", "Cuestión Leonesa", "Sanidad", "Vivienda", "Energía"]
    val_cyl = [factor_despoblacion, factor_cuestion_leonesa, factor_sanidad_cyl,
               factor_vivienda, factor_energia]
    fig_rad_cyl = go.Figure(go.Scatterpolar(r=val_cyl, theta=cat_cyl, fill="toself",
                                            line_color="#8c564b", name="CyL"))
    fig_rad_cyl.update_layout(polar=dict(radialaxis=dict(range=[0, 100])),
                               title="Perfil de Riesgo Electoral CyL")
    st.plotly_chart(fig_rad_cyl, width='stretch')

    # ---- HISTÓRICO CYL
    st.subheader("📈 Histórico de Intención de Voto CyL")
    if not df_hist_cyl.empty:
        df_hist_cyl["Fecha"] = pd.to_datetime(df_hist_cyl["Fecha"])
        df_cyl_nac = df_hist_cyl.groupby(["Fecha", "Partido"])["Votos"].mean().reset_index()
        fig_hcyl = go.Figure()
        for p in PARTIDOS_CYL:
            df_p = df_cyl_nac[df_cyl_nac["Partido"] == p]
            if not df_p.empty:
                fig_hcyl.add_trace(go.Scatter(
                    x=df_p["Fecha"], y=df_p["Votos"],
                    mode="lines+markers", name=p,
                    line=dict(color=COLORES_CYL.get(p, "#999"), width=3)
                ))
        fig_hcyl.update_layout(height=400, hovermode="x unified",
                                title="Evolución Semanal — Intención de Voto CyL")
        st.plotly_chart(fig_hcyl, width='stretch')
        st.dataframe(df_hist_cyl.sort_values("Fecha", ascending=False), width='stretch')

    # ---- NOTA METODOLÓGICA CYL
    with st.expander("📋 Nota Metodológica — Módulo CyL"):
        st.markdown(f"""
**Circunscripciones:** 9 provincias | **Total procuradores simulados:** {TOTAL_CYL}  
**Umbral electoral aplicado:** {umbral_cyl}% (configurable en sidebar)  
**Base de intención de voto:** Estimación estructural con ajuste provincial  

**Variables estructurales específicas CyL:**
- **Despoblación:** CyL pierde 30.000 hab/año. Moviliza voto conservador de mantenimiento.
- **Cuestión Leonesa:** Tensión histórica León vs. Castilla. Beneficia UPL en León, Zamora, Salamanca.
- **Sanidad:** Gestión autonómica del PP. Cierre de centros rurales genera erosión de voto.

**Limitaciones específicas:**
- Sin datos primarios de encuestas autonómicas recientes (modelo estructural)
- Partidos localistas sub-representados en bases nacionales
- Alta sensibilidad al coeficiente de incertidumbre en provincias pequeñas (Soria, Ávila, Segovia)
        """)


# ========== TAB 7: ANDALUCÍA ==========
with tab7:
    render_tab_andalucia(
        escanos_and, datos_prov_and,
        polarizacion_and, nep_and, lsq_and,
        factor_desempleo_and, factor_vivienda_and,
        factor_agua, factor_rural_urbano
    )


# ========== TAB 8: GALICIA ==========
with tab8:
    render_tab_galicia(
        escanos_gal, datos_prov_gal,
        polarizacion_gal, nep_gal, lsq_gal,
        factor_despoblacion_gal, factor_bng_urbano,
        factor_pesca, factor_autogobierno_gal
    )

# ========== TAB 9: MADRID ==========
with tab9:
    render_tab_madrid(
        reparto_mad, votos_mad, datos_zonas_mad,
        polarizacion_mad, nep_mad, lsq_mad,
        factor_vivienda_mad, factor_ayuso,
        factor_fiscal, factor_migracion
    )



# ========== TAB 10: AUDITORÍA ==========
# ========== TAB 11: EUSKADI ==========
with tab11:
    render_tab_euskadi(
        escanos_eus, datos_terr_eus,
        polarizacion_eus, nep_eus, lsq_eus,
        factor_independentismo, factor_izq_abertzale,
        factor_economia_vasca, factor_concierto_eco
    )

with tab10:
    render_tab_auditoria(escanos_totales, escanos_cyl)

import os as _os, datetime as _dt
_log = "last_ingest.txt"
_ts = _dt.datetime.fromtimestamp(_os.path.getmtime(_log)).strftime("%Y-%m-%d %H:%M") if _os.path.exists(_log) else "pendiente"
# ========== TAB 10: ENERGÍA ==========
st.markdown(f"© M.Castillo  |  mybloggingnotes@gmail.com  |  v2.2  |  🕐 Última ingesta: {_ts}")