
# ===============================
# AUDITORÍA & APRENDIZAJE — DATOS
# ===============================

# Base de encuestas externas por ámbito
# Estructura: {ambito: {partido: {fuente: valor_pct}}}
ENCUESTAS_EXTERNAS = {
    "Castilla y León 2026": {
        "fecha_elecciones": "2026-03-15",
        "total_escanos": 86,
        "ma": 44,
        "partidos": ["PP", "PSOE", "VOX", "UPL", "SUMAR", "Por Ávila", "OTROS"],
        "encuestas": {
            "PP":    {"Sigma Dos": 35.5, "NC Report": 35.6, "Sociométrica": 31.6, "CIS": 33.4},
            "PSOE":  {"Sigma Dos": 27.0, "NC Report": 27.6, "Sociométrica": 27.3, "CIS": 32.3},
            "VOX":   {"Sigma Dos": 19.7, "NC Report": 17.9, "Sociométrica": 20.0, "CIS": 18.5},
            "UPL":   {"Sigma Dos":  4.5, "NC Report":  4.9, "Sociométrica":  4.2, "CIS":  6.3},
            "SUMAR": {"Sigma Dos":  3.5, "NC Report":  3.8, "Sociométrica":  3.6, "CIS":  3.6},
            "Por Ávila": {"Sigma Dos": 1.5, "NC Report": 1.8, "Sociométrica": 1.4, "CIS": 1.2},
            "OTROS": {"Sigma Dos":  8.3, "NC Report":  8.4, "Sociométrica": 11.9, "CIS":  4.7},
        },
        "escanos_encuesta_media": {
            "PP": 33, "PSOE": 27, "VOX": 15, "UPL": 4,
            "SUMAR": 1, "Por Ávila": 1, "OTROS": 5
        }
    },
    "Nacional 2026": {
        "fecha_elecciones": "2027-12-01",  # estimada
        "total_escanos": 350,
        "ma": 176,
        "partidos": ["PP", "PSOE", "VOX", "SUMAR", "JUNTS", "ERC", "BILDU", "PNV", "SALF", "OTROS"],
        "encuestas": {
            "PP":    {"40dB": 33.2, "NC Report": 32.8, "Sigma Dos": 34.1, "CIS": 31.5},
            "PSOE":  {"40dB": 28.4, "NC Report": 27.9, "Sigma Dos": 28.8, "CIS": 31.2},
            "VOX":   {"40dB": 12.1, "NC Report": 11.8, "Sigma Dos": 12.5, "CIS": 10.8},
            "SUMAR": {"40dB":  6.8, "NC Report":  7.2, "Sigma Dos":  6.5, "CIS":  7.1},
            "JUNTS": {"40dB":  3.5, "NC Report":  3.2, "Sigma Dos":  3.8, "CIS":  3.0},
            "ERC":   {"40dB":  2.8, "NC Report":  2.5, "Sigma Dos":  2.9, "CIS":  2.4},
            "BILDU": {"40dB":  2.2, "NC Report":  2.4, "Sigma Dos":  2.1, "CIS":  2.0},
            "PNV":   {"40dB":  1.8, "NC Report":  1.7, "Sigma Dos":  1.9, "CIS":  1.8},
            "SALF":  {"40dB":  2.5, "NC Report":  2.8, "Sigma Dos":  2.3, "CIS":  2.1},
            "OTROS": {"40dB":  6.7, "NC Report":  7.7, "Sigma Dos":  5.1, "CIS":  8.1},
        },
        "escanos_encuesta_media": {
            "PP": 138, "PSOE": 118, "VOX": 35, "SUMAR": 28,
            "JUNTS": 8, "ERC": 6, "BILDU": 5, "PNV": 5, "SALF": 4, "OTROS": 3
        }
    }
}

# Pesos iniciales por fuente (0-1) — ajustables por el usuario
PESOS_FUENTES_DEFAULT = {
    "CIS":          0.35,
    "Sigma Dos":    0.25,
    "NC Report":    0.20,
    "Sociométrica": 0.20,
    "40dB":         0.25,
}


# ===============================
# FUNCIONES AUDITORÍA
# ===============================

def calcular_media_ponderada(partido_encuestas, pesos):
    """Calcula media ponderada de encuestas según pesos de fuentes."""
    total_peso = 0
    suma = 0
    for fuente, valor in partido_encuestas.items():
        peso = pesos.get(fuente, 0.2)
        suma += valor * peso
        total_peso += peso
    return round(suma / total_peso, 2) if total_peso > 0 else 0.0


def calcular_escanos_desde_votos(votos_dict, total_escanos, umbral=3.0):
    """D'Hondt simplificado para calcular escaños desde % de voto."""
    votos_filtrados = {p: v for p, v in votos_dict.items() if v >= umbral}
    if not votos_filtrados:
        return {p: 0 for p in votos_dict}
    total_v = sum(votos_filtrados.values())
    votos_norm = {p: v / total_v for p, v in votos_filtrados.items()}

    # D'Hondt
    escanos = {p: 0 for p in votos_dict}
    cocientes = []
    for p, v in votos_norm.items():
        cocientes.append((v, p, 1))

    import heapq
    heap = [(-v, p, 1) for p, v in votos_norm.items()]
    heapq.heapify(heap)
    for _ in range(total_escanos):
        neg_v, p, div = heapq.heappop(heap)
        escanos[p] += 1
        heapq.heappush(heap, (neg_v * div / (div + 1), p, div + 1))

    return escanos


def calcular_delta_modelo_encuesta(escanos_modelo, escanos_encuesta, partidos):
    """Calcula desviación entre modelo y encuestas por partido."""
    deltas = {}
    for p in partidos:
        mod = escanos_modelo.get(p, 0)
        enc = escanos_encuesta.get(p, 0)
        deltas[p] = {"modelo": mod, "encuesta": enc, "delta": mod - enc}
    return deltas


def sugerir_ajustes_sliders(deltas, ambito):
    """
    Sugiere ajustes a los parámetros del modelo basándose en
    la desviación modelo vs encuestas.
    Retorna dict con sugerencias textuales por variable.
    """
    sugerencias = []
    for p, d in deltas.items():
        delta = d["delta"]
        if abs(delta) >= 3:
            if delta > 0:  # Modelo sobreestima este partido
                sugerencias.append({
                    "partido": p,
                    "delta": delta,
                    "tipo": "reducir",
                    "mensaje": f"⬇️ **{p}**: modelo sobreestima en {delta} escaños — considera reducir variables que favorecen a {p}"
                })
            else:  # Modelo subestima
                sugerencias.append({
                    "partido": p,
                    "delta": delta,
                    "tipo": "aumentar",
                    "mensaje": f"⬆️ **{p}**: modelo subestima en {abs(delta)} escaños — considera aumentar variables que favorecen a {p}"
                })
    return sugerencias


# ===============================
# RENDER TAB AUDITORÍA
# ===============================

def render_tab_auditoria(escanos_nac, escanos_cyl):
    """Renderiza el tab completo de Auditoría & Aprendizaje."""
    st.header("🧠 Auditoría & Aprendizaje — Modelo vs. Encuestas Externas")
    st.markdown("""
    > **Sistema de calibración:** Compara la proyección del modelo propio con las
    > encuestas publicadas por demoscópicas externas. Ajusta los pesos de cada fuente
    > y observa cómo el modelo aprende a corregir sus desviaciones sistemáticas.
    """)

    # ---- SELECTOR DE ÁMBITO
    ambito_sel = st.selectbox(
        "📍 Selecciona ámbito electoral",
        list(ENCUESTAS_EXTERNAS.keys()),
        key="sel_ambito_auditoria"
    )
    datos_ambito = ENCUESTAS_EXTERNAS[ambito_sel]
    partidos     = datos_ambito["partidos"]
    encuestas    = datos_ambito["encuestas"]
    total_esc    = datos_ambito["total_escanos"]
    ma           = datos_ambito["ma"]
    fecha_el     = datos_ambito.get("fecha_elecciones", "N/D")

    st.info(f"📅 Fecha electoral: **{fecha_el}**  |  Total escaños: **{total_esc}**  |  MA: **{ma}**")
    st.markdown("---")

    # ---- PESOS DE FUENTES
    st.subheader("⚖️ Calibración de Pesos por Fuente Demoscópica")
    st.markdown("_Ajusta la confianza en cada encuestadora. Los pesos se normalizan automáticamente._")

    fuentes = list({f for p in encuestas.values() for f in p.keys()})
    col_pesos = st.columns(min(len(fuentes), 5))
    pesos_usuario = {}
    for i, fuente in enumerate(fuentes):
        with col_pesos[i % len(col_pesos)]:
            pesos_usuario[fuente] = st.slider(
                f"{fuente}", 0.0, 1.0,
                PESOS_FUENTES_DEFAULT.get(fuente, 0.2),
                step=0.05, key=f"peso_{fuente}_{ambito_sel}"
            )

    # ---- CALCULAR MEDIAS PONDERADAS
    votos_enc_pond = {}
    for p in partidos:
        if p in encuestas:
            votos_enc_pond[p] = calcular_media_ponderada(encuestas[p], pesos_usuario)
        else:
            votos_enc_pond[p] = 0.0

    escanos_enc_calc = calcular_escanos_desde_votos(votos_enc_pond, total_esc)

    # Escaños del modelo propio según ámbito
    if "León" in ambito_sel or "CyL" in ambito_sel or "Castilla" in ambito_sel:
        escanos_modelo = escanos_cyl
    else:
        escanos_modelo = escanos_nac

    st.markdown("---")

    # ---- GRÁFICO PRINCIPAL: MODELO vs ENCUESTAS
    st.subheader("📊 Proyección Modelo vs. Media Ponderada Encuestas")

    df_comp = pd.DataFrame([
        {
            "Partido": p,
            "Modelo (app)": escanos_modelo.get(p, 0),
            "Media Encuestas": escanos_enc_calc.get(p, 0),
        }
        for p in partidos if escanos_modelo.get(p, 0) > 0 or escanos_enc_calc.get(p, 0) > 0
    ]).sort_values("Modelo (app)", ascending=False)

    df_melt = df_comp.melt(id_vars="Partido", var_name="Fuente", value_name="Escaños")
    colores_barras = {"Modelo (app)": "#2ecc71", "Media Encuestas": "#3498db"}

    fig_comp = px.bar(
        df_melt, x="Partido", y="Escaños", color="Fuente",
        barmode="group", text="Escaños",
        color_discrete_map=colores_barras,
        title=f"Escaños: Modelo Propio vs. Encuestas — {ambito_sel}",
        height=420
    )
    fig_comp.update_traces(textposition="outside")
    fig_comp.add_hline(y=ma, line_dash="dash", line_color="red",
                       annotation_text=f"MA ({ma})")
    st.plotly_chart(fig_comp, width="stretch", key=f"audit_comp_{ambito_sel}")

    # ---- DELTA MODELO vs ENCUESTAS
    st.subheader("🔍 Desviación Sistemática — Δ Modelo vs. Encuestas")

    deltas = calcular_delta_modelo_encuesta(escanos_modelo, escanos_enc_calc, partidos)
    df_delta = pd.DataFrame([
        {"Partido": p, "Δ Escaños": d["delta"],
         "Modelo": d["modelo"], "Encuesta": d["encuesta"]}
        for p, d in deltas.items()
        if d["modelo"] > 0 or d["encuesta"] > 0
    ]).sort_values("Δ Escaños", ascending=False)

    fig_delta = px.bar(
        df_delta, x="Partido", y="Δ Escaños",
        color="Δ Escaños", color_continuous_scale="RdYlGn",
        text="Δ Escaños", title="Δ = Modelo − Encuesta (positivo = modelo sobreestima)",
        height=350
    )
    fig_delta.add_hline(y=0, line_color="black", line_width=1)
    fig_delta.update_traces(textposition="outside")
    st.plotly_chart(fig_delta, width="stretch", key=f"audit_delta_{ambito_sel}")

    # ---- ENCUESTAS INDIVIDUALES
    st.subheader("📋 Encuestas Individuales por Partido")
    df_enc_ind = []
    for p in partidos:
        if p in encuestas:
            for fuente, valor in encuestas[p].items():
                df_enc_ind.append({
                    "Partido": p, "Fuente": fuente, "% Voto": valor,
                    "Peso": pesos_usuario.get(fuente, 0.2)
                })
    df_enc = pd.DataFrame(df_enc_ind)
    if not df_enc.empty:
        fig_enc = px.bar(
            df_enc, x="Partido", y="% Voto", color="Fuente",
            barmode="group", text="% Voto",
            title="Intención de voto por encuestadora (%)",
            height=380
        )
        fig_enc.update_traces(texttemplate="%{text:.1f}", textposition="outside")
        st.plotly_chart(fig_enc, width="stretch", key=f"audit_enc_{ambito_sel}")

    # ---- SISTEMA DE APRENDIZAJE — SUGERENCIAS
    st.markdown("---")
    st.subheader("🧠 Sistema de Aprendizaje — Sugerencias de Calibración")

    sugerencias = sugerir_ajustes_sliders(deltas, ambito_sel)
    if sugerencias:
        col_sug1, col_sug2 = st.columns(2)
        for i, s in enumerate(sugerencias):
            with col_sug1 if i % 2 == 0 else col_sug2:
                if s["tipo"] == "reducir":
                    st.warning(s["mensaje"])
                else:
                    st.info(s["mensaje"])

        # Índice de precisión del modelo
        mae = sum(abs(d["delta"]) for d in deltas.values()) / len(deltas)
        rmse = (sum(d["delta"]**2 for d in deltas.values()) / len(deltas)) ** 0.5
        precision = max(0, round(100 - rmse * 5, 1))

        st.markdown("---")
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("MAE (Error Medio Absoluto)", f"{mae:.2f} escaños")
        col_m2.metric("RMSE", f"{rmse:.2f} escaños")
        col_m3.metric("Índice de Precisión", f"{precision}/100",
                      "✅ Bueno" if precision > 75 else "⚠️ Mejorable")

        # Radar de precisión por partido
        partidos_radar = [p for p in partidos if abs(deltas.get(p, {}).get("delta", 0)) > 0]
        if partidos_radar:
            fig_radar_prec = go.Figure(go.Scatterpolar(
                r=[max(0, 10 - abs(deltas[p]["delta"])) for p in partidos_radar],
                theta=partidos_radar,
                fill="toself",
                line_color="#2ecc71",
                name="Precisión por partido (10=perfecto)"
            ))
            fig_radar_prec.update_layout(
                polar=dict(radialaxis=dict(range=[0, 10])),
                title="Radar de Precisión del Modelo por Partido",
                height=380
            )
            st.plotly_chart(fig_radar_prec, width="stretch", key=f"audit_radar_{ambito_sel}")
    else:
        st.success("✅ El modelo está bien calibrado — desviación < 3 escaños en todos los partidos.")

    # ---- TABLA RESUMEN
    st.subheader("📊 Tabla Resumen Comparativa")
    df_resumen = pd.DataFrame([
        {
            "Partido": p,
            "Modelo": escanos_modelo.get(p, 0),
            "Enc. Media Pond.": escanos_enc_calc.get(p, 0),
            "Δ": deltas.get(p, {}).get("delta", 0),
            **{f: encuestas.get(p, {}).get(f, "-") for f in fuentes}
        }
        for p in partidos
        if escanos_modelo.get(p, 0) > 0 or escanos_enc_calc.get(p, 0) > 0
    ])
    st.dataframe(df_resumen, use_container_width=True)

    # ---- NOTA METODOLÓGICA
    with st.expander("📋 Metodología del Sistema de Auditoría"):
        st.markdown(f"""
**Media ponderada de encuestas:**
Cada encuestadora tiene un peso ajustable (0-1). La media ponderada se normaliza
automáticamente para que los pesos sumen 1.

**D'Hondt desde % encuesta:**
Los % de voto de la media ponderada se convierten en escaños aplicando la ley D'Hondt
al total de {total_esc} escaños con umbral del 3%.

**Índice de Precisión:**
`Precisión = max(0, 100 - RMSE × 5)`
Donde RMSE es la raíz del error cuadrático medio entre modelo y encuestas.
- >85: Modelo muy preciso
- 70-85: Modelo aceptable
- <70: Modelo necesita recalibración

**Sugerencias de calibración:**
Se generan automáticamente cuando |Δ| ≥ 3 escaños en cualquier partido.
Las sugerencias orientan qué variables estructurales del sidebar ajustar.

**Fuentes de encuestas CyL 2026:**
Sigma Dos (El Mundo), NC Report (El Confidencial), Sociométrica, CIS (Barómetro autonómico)
        """)
