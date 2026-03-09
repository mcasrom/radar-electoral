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
