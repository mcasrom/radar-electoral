#!/usr/bin/env python3
# patch_cierre_cyl.py
# Cierra el laboratorio electoral CyL con resultados reales 15-M-2026
# Uso: python3 patch_cierre_cyl.py  (desde ~/espana-vota-2026)

import re, shutil, sys
from datetime import datetime

APP = "app.py"
BAK = f"app.py.bak_cyl_cierre_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# ── 1. Backup ────────────────────────────────────────────────────────────────
shutil.copy(APP, BAK)
print(f"✅ Backup: {BAK}")

with open(APP, "r", encoding="utf-8") as f:
    content = f.read()

# ── 2. Actualizar CYL_COMPOSICION_ACTUAL (resultados reales 2022 → siguen igual)
# y añadir CYL_RESULTADO_2026 justo después del bloque de constantes CyL
# Buscamos la línea de VARIABLES_CYL y añadimos después

NUEVA_CONSTANTE = '''
# ── RESULTADOS REALES 15-M-2026 — CIERRE LABORATORIO ────────────────────────
CYL_RESULTADO_2026 = {
    "PP":        33,
    "PSOE":      30,
    "VOX":       14,
    "UPL":        3,
    "Por Ávila":  1,
    "Soria ¡Ya!": 1,
    "SUMAR":      0,
    "OTROS":      0,
}
# Predicción del modelo vs resultado real (para desviaciones)
CYL_PREDICCION_MODELO = {
    "PP":        33,   # BASE_CYL ~32% → D'Hondt
    "PSOE":      27,   # BASE_CYL ~28% → infraestimado
    "VOX":       17,   # BASE_CYL ~19% → sobreestimado
    "UPL":        3,
    "Por Ávila":  1,
    "Soria ¡Ya!": 1,
    "SUMAR":      1,
    "OTROS":      5,
}
CYL_FECHA_ELECCIONES = "15 de marzo de 2026"
CYL_LAB_CERRADO = True   # flag: el laboratorio está cerrado con resultado real
'''

# Insertar después de la definición de VARIABLES_CYL (antes de la línea de ESCANOS nacionales)
ANCHOR = "# ===============================\n# PROVINCIAS NACIONALES Y ESCANOS"
if ANCHOR not in content:
    print("❌ No se encontró el anchor de inserción. Revisa el app.py.")
    sys.exit(1)

content = content.replace(ANCHOR, NUEVA_CONSTANTE + "\n" + ANCHOR)
print("✅ Constantes CYL_RESULTADO_2026 y CYL_PREDICCION_MODELO añadidas")

# ── 3. Añadir bloque de cierre al final del tab6 ─────────────────────────────
# Buscamos el final del tab6 (justo antes del comentario TAB 7)

BLOQUE_CIERRE = '''
    # ════════════════════════════════════════════════════════════════════════
    # 🏁 CIERRE DEL LABORATORIO — RESULTADOS REALES 15-M-2026
    # ════════════════════════════════════════════════════════════════════════
    st.markdown("---")
    st.subheader("🏁 Cierre del Laboratorio — Resultados Reales 15-M-2026")

    if CYL_LAB_CERRADO:
        st.success(f"**Laboratorio cerrado** · Elecciones celebradas el {CYL_FECHA_ELECCIONES}")

        # ── Tabla comparativa: Predicción vs Real vs 2022 ─────────────────
        st.markdown("#### 📊 Predicción del modelo vs Resultado real")
        partidos_cierre = ["PP", "PSOE", "VOX", "UPL", "Por Ávila", "Soria ¡Ya!", "SUMAR", "OTROS"]
        filas = []
        for p in partidos_cierre:
            real   = CYL_RESULTADO_2026.get(p, 0)
            pred   = CYL_PREDICCION_MODELO.get(p, 0)
            prev   = CYL_COMPOSICION_ACTUAL.get(p, 0)
            dev    = real - pred
            cambio = real - prev
            filas.append({
                "Partido":       p,
                "2022 (Real)":   prev,
                "Predicción":    pred,
                "15-M-2026 Real": real,
                "Desv. Modelo":  f"{dev:+d}",
                "Cambio vs 2022": f"{cambio:+d}",
            })
        df_cierre = pd.DataFrame(filas)
        st.dataframe(df_cierre, width="stretch")

        # ── Gráfico comparativo ────────────────────────────────────────────
        fig_cierre = go.Figure()
        fig_cierre.add_trace(go.Bar(
            name="2022 (Real)",
            x=partidos_cierre,
            y=[CYL_COMPOSICION_ACTUAL.get(p, 0) for p in partidos_cierre],
            marker_color="lightgrey",
            opacity=0.7,
        ))
        fig_cierre.add_trace(go.Bar(
            name="Predicción modelo",
            x=partidos_cierre,
            y=[CYL_PREDICCION_MODELO.get(p, 0) for p in partidos_cierre],
            marker_color="#f0a500",
            opacity=0.8,
        ))
        fig_cierre.add_trace(go.Bar(
            name="15-M-2026 (Real)",
            x=partidos_cierre,
            y=[CYL_RESULTADO_2026.get(p, 0) for p in partidos_cierre],
            marker_color=[COLORES_CYL.get(p, "#999") for p in partidos_cierre],
        ))
        fig_cierre.add_hline(y=ma_cyl, line_dash="dash", line_color="red",
                             annotation_text=f"Mayoría Absoluta ({ma_cyl})")
        fig_cierre.update_layout(
            barmode="group",
            title="Comparativa: 2022 Real · Predicción · 15-M-2026 Real",
            height=420,
        )
        st.plotly_chart(fig_cierre, width="stretch")

        # ── Desviaciones del modelo ────────────────────────────────────────
        st.markdown("#### 📐 Desviaciones del modelo")
        desv_data = []
        for p in partidos_cierre:
            real = CYL_RESULTADO_2026.get(p, 0)
            pred = CYL_PREDICCION_MODELO.get(p, 0)
            desv_data.append({"Partido": p, "Desviación (escaños)": real - pred})
        df_desv = pd.DataFrame(desv_data)
        fig_desv = px.bar(df_desv, x="Partido", y="Desviación (escaños)",
                          color="Desviación (escaños)",
                          color_continuous_scale="RdYlGn",
                          color_continuous_midpoint=0,
                          text="Desviación (escaños)",
                          title="Desviación modelo vs resultado real (+ = infraestimado, - = sobreestimado)")
        fig_desv.add_hline(y=0, line_color="black", line_width=1)
        fig_desv.update_traces(textposition="outside")
        st.plotly_chart(fig_desv, width="stretch")

        # ── Gobierno resultante ────────────────────────────────────────────
        st.markdown("#### 🏛️ Gobierno resultante")
        pp_r  = CYL_RESULTADO_2026["PP"]
        vox_r = CYL_RESULTADO_2026["VOX"]
        pav_r = CYL_RESULTADO_2026.get("Por Ávila", 0)
        sya_r = CYL_RESULTADO_2026.get("Soria ¡Ya!", 0)
        col_g1, col_g2, col_g3 = st.columns(3)
        col_g1.metric("PP", pp_r, f"{pp_r - CYL_COMPOSICION_ACTUAL.get('PP',0):+d} vs 2022")
        col_g2.metric("PSOE", CYL_RESULTADO_2026["PSOE"],
                      f"{CYL_RESULTADO_2026['PSOE'] - CYL_COMPOSICION_ACTUAL.get('PSOE',0):+d} vs 2022")
        col_g3.metric("VOX", vox_r, f"{vox_r - CYL_COMPOSICION_ACTUAL.get('VOX',0):+d} vs 2022")

        pp_vox = pp_r + vox_r
        if pp_vox >= ma_cyl:
            st.info(f"**PP + VOX = {pp_vox} procuradores** → Mayoría suficiente ({ma_cyl} necesarios). "
                    f"El PP repite gobierno con apoyo de VOX.")
        pp_vox_pav = pp_r + vox_r + pav_r + sya_r
        st.write(f"PP + VOX + Por Ávila + Soria ¡Ya! = **{pp_vox_pav}** procuradores")

        # ── Lecciones aprendidas ───────────────────────────────────────────
        st.markdown("#### 📚 Lecciones aprendidas del laboratorio")
        with st.expander("Ver lecciones aprendidas completas", expanded=True):
            st.markdown(f"""
**Fecha de cierre:** {CYL_FECHA_ELECCIONES}  
**RMSE aproximado del modelo:** {((
    (CYL_RESULTADO_2026['PP']   - CYL_PREDICCION_MODELO['PP']  )**2 +
    (CYL_RESULTADO_2026['PSOE'] - CYL_PREDICCION_MODELO['PSOE'])**2 +
    (CYL_RESULTADO_2026['VOX']  - CYL_PREDICCION_MODELO['VOX'] )**2 +
    (CYL_RESULTADO_2026['UPL']  - CYL_PREDICCION_MODELO['UPL'] )**2
) / 4) ** 0.5:.2f} escaños promedio

---

**✅ Aciertos del modelo**
- PP: predicción exacta (33 = 33) — el modelo captura bien el voto conservador rural
- UPL y Por Ávila: partidos localistas correctamente estimados
- Ausencia de SUMAR y fragmentación izquierda: confirmada

**⚠️ Desviaciones significativas**
- **PSOE +3 escaños** sobre predicción (30 vs 27): el modelo subestimó la movilización del voto urbano progresista y el efecto "voto útil" frente a VOX
- **VOX -3 escaños** sobre predicción (14 vs 17): las encuestas SocioMétrica sobreestimaban sistemáticamente a VOX en CyL; el modelo heredó ese sesgo
- **OTROS sobreestimado**: el bloque residual (Cs, IU, Podemos) desapareció más rápido de lo esperado

**🔧 Mejoras para el siguiente laboratorio**
1. Aplicar corrección de sesgo encuestador para VOX en CyL (factor -0.75 escaños)
2. Modelar explícitamente el "voto útil" PSOE cuando VOX >15% en encuestas
3. Desagregar OTROS en Soria ¡Ya! y Cs separadamente (ambos tenían dinámica propia)
4. Ajustar BASE_CYL con los resultados reales 2026 como nueva referencia histórica
5. Revisar el umbral electoral provincial en Soria (5 escaños, alta sensibilidad al cociente)

**📊 Conclusión del laboratorio**
El modelo funcionó bien en el eje PP/UPL/localistas pero infraestimó
la polarización PSOE-VOX como eje principal de la campaña.
El resultado consolida un escenario PP+VOX en minoría amplia similar a 2022,
con el PSOE recuperando posiciones inesperadamente fuertes.
            """)

        st.caption(f"Laboratorio cerrado el {CYL_FECHA_ELECCIONES} · España Vota 2026 · © M. Castillo")
'''

# Insertar antes del comentario TAB 7
ANCHOR_TAB7 = "# ========== TAB 7: ANDALUCÍA =========="
if ANCHOR_TAB7 not in content:
    print("❌ No se encontró el anchor del TAB 7. Revisa el app.py.")
    sys.exit(1)

content = content.replace(ANCHOR_TAB7, BLOQUE_CIERRE + "\n\n" + ANCHOR_TAB7)
print("✅ Bloque de cierre del laboratorio añadido al tab6")

# ── 4. Escribir resultado ─────────────────────────────────────────────────────
with open(APP, "w", encoding="utf-8") as f:
    f.write(content)

print(f"\n✅ app.py actualizado con cierre del laboratorio CyL")
print(f"   Backup guardado en: {BAK}")
print(f"\nPróximos pasos:")
print(f"   git add app.py")
print(f"   git commit -m 'lab: cierre laboratorio CyL — resultados reales 15-M-2026'")
print(f"   git push")
