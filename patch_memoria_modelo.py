#!/usr/bin/env python3
# patch_memoria_modelo.py
# Aplica correcciones CyL→AND y añade tab Historial de Laboratorios
# Uso: python3 patch_memoria_modelo.py  (desde ~/espana-vota-2026)

import re, shutil, sys
from datetime import datetime

APP = "app.py"
BAK = f"app.py.bak_memoria_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

shutil.copy(APP, BAK)
print(f"✅ Backup: {BAK}")

with open(APP, "r", encoding="utf-8") as f:
    content = f.read()

# ══════════════════════════════════════════════════════════════════════════════
# FIX 1 — Corregir BASE_AND aplicando lecciones de CyL
# ══════════════════════════════════════════════════════════════════════════════
OLD_BASE_AND = '''BASE_AND = {
    "PP":            38.0,   # fortaleza del gobierno autonómico
    "PSOE":          26.0,   # recuperación lenta post-2022
    "VOX":           10.5,   # bajada tras máximos
    "Por Andalucía":  8.0,   # estabilización SUMAR/IU
    "OTROS":         17.5    # indecisos, abstención, nulos, Cs residual
}'''

NEW_BASE_AND = '''BASE_AND = {
    "PP":            38.0,   # fortaleza del gobierno autonómico
    "PSOE":          26.0,   # recuperación lenta post-2022
    # VOX: reducido de 10.5 → 9.0 aplicando corrección sesgo encuestador CyL-2026
    # En AND VOX tiene perfil más urbano-costero; aun así sesgo sistemático -1.5 pts
    "VOX":            9.0,
    "Por Andalucía":  8.5,   # estabilización — absorbe parte del voto SUMAR
    # OTROS: reducido de 17.5 → 13.0; Cs eliminado (0 escaños esperados post-CyL)
    "OTROS":         13.5    # indecisos + abstención + residual sin Cs
}
# NOTA: Correcciones aplicadas desde lecciones laboratorio CyL-2026
# model_memory.py::obtener_correcciones("cyl_2026") → VOX:-1.5, PSOE:+1.5, OTROS:-2.5'''

if OLD_BASE_AND not in content:
    print("❌ No se encontró BASE_AND original. Revisa el app.py.")
    sys.exit(1)

content = content.replace(OLD_BASE_AND, NEW_BASE_AND)
print("✅ BASE_AND corregida (sesgo VOX, OTROS desagregado)")

# ══════════════════════════════════════════════════════════════════════════════
# FIX 2 — Añadir factor voto útil PSOE en ajustar_escenario_and()
# ══════════════════════════════════════════════════════════════════════════════
OLD_AJUSTE_AND_RETURN = '''    # Rural vs urbano → mayor ruralidad → PP y VOX más fuertes
    ajuste["PP"]            += (f_rural_urbano - 50) * 0.012
    ajuste["VOX"]           += (f_rural_urbano - 50) * 0.006
    ajuste["Por Andalucía"] -= (f_rural_urbano - 50) * 0.010

    return normalizar(ajuste)'''

NEW_AJUSTE_AND_RETURN = '''    # Rural vs urbano → mayor ruralidad → PP y VOX más fuertes
    ajuste["PP"]            += (f_rural_urbano - 50) * 0.012
    ajuste["VOX"]           += (f_rural_urbano - 50) * 0.006
    ajuste["Por Andalucía"] -= (f_rural_urbano - 50) * 0.010

    # ── Corrección CyL-2026: factor voto útil PSOE ──────────────────────────
    # Lección aprendida: cuando VOX supera ~12-15%, votantes PSOE hesitantes
    # se movilizan → transferencia desde indecisos/OTROS hacia PSOE
    vox_estimado = ajuste.get("VOX", 0)
    if vox_estimado > 12.0:
        factor_voto_util = (vox_estimado - 12.0) * 0.08   # ~0.24 pts por cada pt sobre 12%
        ajuste["PSOE"]  += factor_voto_util
        ajuste["OTROS"] -= factor_voto_util * 0.8          # sale de indecisos/OTROS

    return normalizar(ajuste)'''

if OLD_AJUSTE_AND_RETURN not in content:
    print("❌ No se encontró el bloque rural_urbano en ajustar_escenario_and(). Revisa el app.py.")
    sys.exit(1)

content = content.replace(OLD_AJUSTE_AND_RETURN, NEW_AJUSTE_AND_RETURN)
print("✅ Factor voto útil PSOE añadido en ajustar_escenario_and()")

# ══════════════════════════════════════════════════════════════════════════════
# FIX 3 — Añadir import de model_memory y tab Historial en la cabecera
# ══════════════════════════════════════════════════════════════════════════════
# Buscamos el primer import del archivo para añadir el nuestro
OLD_IMPORT_ANCHOR = "import streamlit as st"
NEW_IMPORT_ANCHOR = """import streamlit as st
try:
    from model_memory import (
        inicializar_cyl_2026, resumen_labs,
        obtener_correcciones, obtener_todos_labs
    )
    inicializar_cyl_2026()   # registra CyL-2026 si no existe
    _MEMORIA_OK = True
except ImportError:
    _MEMORIA_OK = False"""

# Solo reemplazar la primera ocurrencia
content = content.replace(OLD_IMPORT_ANCHOR, NEW_IMPORT_ANCHOR, 1)
print("✅ Import de model_memory añadido")

# ══════════════════════════════════════════════════════════════════════════════
# FIX 4 — Añadir "Historial" a la lista de tabs
# ══════════════════════════════════════════════════════════════════════════════
# Buscamos la declaración de tabs (línea con st.tabs)
# Necesitamos ver cómo está declarada — buscamos el patrón
OLD_TABS = '"🏰 Castilla y León — Lab. Electoral",\n    "🌞 Andalucía — Lab. Electoral",\n    "🌿 Galicia — Lab. Electoral",\n    "🏙️ Madrid — Lab. Electoral",'
NEW_TABS = '"🏰 Castilla y León — Lab. Electoral",\n    "🌞 Andalucía — Lab. Electoral",\n    "🌿 Galicia — Lab. Electoral",\n    "🏙️ Madrid — Lab. Electoral",\n    "📊 Historial de Laboratorios",'

if OLD_TABS in content:
    content = content.replace(OLD_TABS, NEW_TABS)
    print("✅ Tab 'Historial de Laboratorios' añadido a la lista de tabs")
else:
    print("⚠️  No se encontró la lista de tabs exacta — añade manualmente '📊 Historial de Laboratorios' a st.tabs()")

# ══════════════════════════════════════════════════════════════════════════════
# FIX 5 — Añadir bloque del tab Historial justo antes del footer
# ══════════════════════════════════════════════════════════════════════════════
BLOQUE_HISTORIAL = '''
# ========== TAB HISTORIAL DE LABORATORIOS ==========
# Nota: asignar esta variable al tab correspondiente en la declaración de tabs
# Ejemplo: tab_hist = tabs[-1]  o añadir tab_hist en el unpack de st.tabs()

def render_tab_historial():
    """Tab de historial comparado de todos los laboratorios cerrados."""
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go

    st.header("📊 Historial de Laboratorios Electorales")
    st.markdown("""
    Registro de todos los laboratorios cerrados con resultados reales,
    métricas de precisión del modelo y lecciones aprendidas aplicadas.
    """)

    if not _MEMORIA_OK:
        st.warning("⚠️ model_memory.py no encontrado. Copia el archivo al directorio del proyecto.")
        return

    labs_raw = obtener_todos_labs()
    if not labs_raw:
        st.info("Sin laboratorios cerrados aún.")
        return

    # ── KPIs globales ──────────────────────────────────────────────────────
    labs_cerrados = [l for l in labs_raw.values() if l.get("cerrado")]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Labs cerrados", len(labs_cerrados))
    if labs_cerrados:
        rmse_medio = sum(l["metricas"].get("rmse", 0) for l in labs_cerrados) / len(labs_cerrados)
        mae_medio  = sum(l["metricas"].get("mae",  0) for l in labs_cerrados) / len(labs_cerrados)
        col2.metric("RMSE medio", f"{rmse_medio:.2f} esc.")
        col3.metric("MAE medio",  f"{mae_medio:.2f} esc.")
        # Partido con mayor sesgo acumulado
        sesgos = {}
        for lab in labs_cerrados:
            for p, d in lab["metricas"].get("detalle", {}).items():
                sesgos[p] = sesgos.get(p, 0) + d.get("error", 0)
        if sesgos:
            p_sesgo = max(sesgos, key=lambda x: abs(sesgos[x]))
            col4.metric("Mayor sesgo acumulado", f"{p_sesgo} ({sesgos[p_sesgo]:+d})")

    st.markdown("---")

    # ── Tabla resumen ──────────────────────────────────────────────────────
    st.subheader("📋 Resumen de laboratorios")
    filas = resumen_labs()
    if filas:
        df_hist = pd.DataFrame(filas)
        st.dataframe(df_hist, width="stretch")

    # ── Gráfico RMSE por laboratorio ───────────────────────────────────────
    labs_con_rmse = [l for l in filas if l["RMSE"] != "-"]
    if labs_con_rmse:
        st.subheader("📐 Evolución del error del modelo (RMSE)")
        df_rmse = pd.DataFrame([
            {"Laboratorio": l["Comunidad"], "Fecha": l["Fecha"],
             "RMSE": float(l["RMSE"]), "MAE": float(l["MAE"])}
            for l in labs_con_rmse
        ])
        fig_rmse = px.bar(df_rmse, x="Laboratorio", y=["RMSE", "MAE"],
                          barmode="group",
                          title="Error del modelo por laboratorio",
                          labels={"value": "Escaños", "variable": "Métrica"},
                          color_discrete_map={"RMSE": "#e74c3c", "MAE": "#f39c12"})
        st.plotly_chart(fig_rmse, width="stretch")

    # ── Detalle por partido: sesgos acumulados ─────────────────────────────
    st.subheader("🎯 Sesgos acumulados por partido")
    all_sesgos = {}
    for lab in labs_cerrados:
        for p, d in lab["metricas"].get("detalle", {}).items():
            if p not in all_sesgos:
                all_sesgos[p] = []
            all_sesgos[p].append(d.get("error", 0))
    if all_sesgos:
        df_sesgos = pd.DataFrame([
            {"Partido": p,
             "Error medio": round(sum(v)/len(v), 2),
             "Error total": sum(v),
             "N labs": len(v)}
            for p, v in all_sesgos.items()
        ]).sort_values("Error medio")
        fig_sesgo = px.bar(df_sesgos, x="Partido", y="Error medio",
                           color="Error medio",
                           color_continuous_scale="RdYlGn",
                           color_continuous_midpoint=0,
                           text="Error medio",
                           title="Sesgo medio por partido (+ = infraestimado, - = sobreestimado)")
        fig_sesgo.add_hline(y=0, line_color="black", line_width=1)
        fig_sesgo.update_traces(textposition="outside")
        st.plotly_chart(fig_sesgo, width="stretch")
        st.dataframe(df_sesgos, width="stretch")

    # ── Detalle expandible por laboratorio ────────────────────────────────
    st.subheader("🔍 Detalle por laboratorio")
    for clave, lab in labs_raw.items():
        if not lab.get("cerrado"):
            continue
        with st.expander(f"{'✅' if lab['cerrado'] else '🔄'} {lab['comunidad']} — {lab['fecha_eleccion']}"):
            m = lab.get("metricas", {})
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("RMSE", m.get("rmse", "-"))
            col_b.metric("MAE",  m.get("mae",  "-"))
            col_c.metric("Bias", m.get("bias", "-"))

            # Tabla predicción vs real
            detalle = m.get("detalle", {})
            if detalle:
                df_det = pd.DataFrame([
                    {"Partido": p, "Predicción": d["pred"],
                     "Real": d["real"], "Error": f"{d['error']:+d}"}
                    for p, d in detalle.items()
                ])
                st.dataframe(df_det, width="stretch")

            # Correcciones derivadas
            corr = lab.get("correcciones", {})
            if corr:
                st.markdown("**Correcciones aplicadas al siguiente lab:**")
                for p, c in corr.items():
                    st.markdown(f"- {p}: `{c:+.1f}` escaños")

            # Lecciones
            lecciones = lab.get("lecciones", [])
            if lecciones:
                st.markdown("**Lecciones aprendidas:**")
                for l in lecciones:
                    st.markdown(f"- {l}")

    st.caption("España Vota 2026 · model_memory.py · © M. Castillo")

'''

# Insertar antes del footer final
ANCHOR_FOOTER = 'import os as _os, datetime as _dt'
if ANCHOR_FOOTER in content:
    content = content.replace(ANCHOR_FOOTER, BLOQUE_HISTORIAL + "\n" + ANCHOR_FOOTER)
    print("✅ Función render_tab_historial() añadida")
else:
    print("⚠️  No se encontró el anchor del footer — añade render_tab_historial() manualmente al final")

# ══════════════════════════════════════════════════════════════════════════════
# Guardar
# ══════════════════════════════════════════════════════════════════════════════
with open(APP, "w", encoding="utf-8") as f:
    f.write(content)

print(f"""
✅ patch_memoria_modelo.py completado

Cambios aplicados:
  1. BASE_AND["VOX"]   10.5 → 9.0  (corrección sesgo CyL)
  2. BASE_AND["OTROS"] 17.5 → 13.5 (Cs eliminado)
  3. Factor voto útil PSOE añadido en ajustar_escenario_and()
  4. Import model_memory.py en cabecera
  5. Tab 'Historial de Laboratorios' añadido
  6. render_tab_historial() implementada

Pasos siguientes:
  1. Añadir tab_hist al unpack de st.tabs() y llamar a render_tab_historial()
  2. Copiar model_memory.py a ~/espana-vota-2026/
  3. Copiar lessons_learned.md a ~/espana-vota-2026/docs/
  4. python3 -c "from model_memory import inicializar_cyl_2026; inicializar_cyl_2026()"
  5. git add app.py model_memory.py docs/lessons_learned.md
  6. git commit -m "feat: memoria del modelo + correcciones AND + historial labs"
  7. git push
""")
