#!/usr/bin/env python3
"""
patch_hemiciclo.py — Añade gráfico herradura + donut al tab Hemiciclo Nacional

Ejecutar desde ~/espana-vota-2026/:
    python3 patch_hemiciclo.py
"""

import ast
import shutil
from pathlib import Path
from datetime import datetime

APP    = Path("app.py")
BACKUP = Path(f"app.py.bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

shutil.copy2(APP, BACKUP)
print(f"✅ Backup: {BACKUP}")

content = APP.read_text(encoding="utf-8")

# ======================================================
# CÓDIGO DE LAS FUNCIONES DE HEMICICLO
# ======================================================

HEMICICLO_FUNCIONES = '''
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

'''

# ======================================================
# BLOQUE DE RENDER DEL HEMICICLO EN TAB1
# ======================================================

HEMICICLO_RENDER = '''
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
'''

# ======================================================
# INSERTAR FUNCIONES — antes de st.tabs
# ======================================================
anchor_tabs = "tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs"
idx = content.find(anchor_tabs)
if idx == -1:
    print("❌ No se encontró st.tabs"); exit(1)

content = content[:idx] + HEMICICLO_FUNCIONES + content[idx:]
print("✅ Funciones hacer_herradura y hacer_donut insertadas")

# ======================================================
# INSERTAR RENDER — al final del with tab1 block
# ======================================================
# Buscamos el anchor del final del tab1 (inicio de tab2)
anchor_tab2 = "# ========== TAB 2:"
idx2 = content.find(anchor_tab2)
if idx2 == -1:
    anchor_tab2 = "with tab2:"
    idx2 = content.find(anchor_tab2)

if idx2 == -1:
    print("❌ No se encontró el inicio de tab2"); exit(1)

content = content[:idx2] + HEMICICLO_RENDER + "\n" + content[idx2:]
print("✅ Render hemiciclo insertado en tab1")

# ======================================================
# VERIFICAR SINTAXIS
# ======================================================
print("\n── VERIFICACIÓN SINTAXIS ──")
try:
    ast.parse(content)
    print("✅ Sintaxis OK")
except SyntaxError as e:
    print(f"❌ SyntaxError línea {e.lineno}: {e.msg}")
    print(f"   Backup: {BACKUP}")
    exit(1)

APP.write_text(content, encoding="utf-8")
total = content.count("\n")
print(f"\n✅ app.py guardado — {total} líneas")
print(f"\n▶ Siguiente paso:")
print(f"   git add app.py && git commit -m 'feat: hemiciclo herradura + donut en tab1' && git push origin main")
