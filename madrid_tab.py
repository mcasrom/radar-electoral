
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
        st.plotly_chart(fig_act, use_container_width=True)
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
        st.plotly_chart(fig_sim, use_container_width=True)
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
    st.plotly_chart(fig_delta, use_container_width=True)

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
        st.plotly_chart(fig_vz, use_container_width=True)

    with col_ze:
        rep_z = {p: v for p, v in dz["Reparto_estimado"].items() if v > 0}
        if rep_z:
            fig_ez = px.pie(values=list(rep_z.values()), names=list(rep_z.keys()),
                            color=list(rep_z.keys()),
                            color_discrete_map=COLORES_MAD, hole=0.4,
                            title=f"Estimación escaños — {zona_sel}")
            st.plotly_chart(fig_ez, use_container_width=True)

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
    st.plotly_chart(fig_coal, use_container_width=True)
    st.dataframe(df_coal, use_container_width=True)

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
        st.plotly_chart(fig_rad, use_container_width=True)

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
        st.plotly_chart(fig_heat, use_container_width=True)

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
