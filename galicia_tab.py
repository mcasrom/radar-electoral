
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
        st.plotly_chart(fig_act, use_container_width=True)
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
        st.plotly_chart(fig_sim, use_container_width=True)
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
    st.plotly_chart(fig_delta, use_container_width=True)

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
        st.plotly_chart(fig_v, use_container_width=True)

    with col_pe:
        rep = {p: v for p, v in dp_gal["Reparto"].items() if v > 0}
        if rep:
            fig_e = px.pie(values=list(rep.values()), names=list(rep.keys()),
                           color=list(rep.keys()),
                           color_discrete_map=COLORES_GAL, hole=0.4,
                           title=f"D'Hondt — {prov_sel} ({ESCANOS_GAL[prov_sel]} diputados)")
            st.plotly_chart(fig_e, use_container_width=True)

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
    st.plotly_chart(fig_coal, use_container_width=True)
    st.dataframe(df_coal, use_container_width=True)

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
        st.plotly_chart(fig_rad, use_container_width=True)

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
        st.plotly_chart(fig_heat, use_container_width=True)

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
