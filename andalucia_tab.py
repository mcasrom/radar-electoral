
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
# tab1,tab2,tab3,tab4,tab5,tab6,tab7 = st.tabs([
#     "🏛️ Hemiciclo Nacional",
#     "🗺️ Desglose Provincial",
#     "📡 Radar Estratégico",
#     "📋 Metodología y Fuentes",
#     "📈 Histórico Semanal",
#     "🏰 Castilla y León",
#     "🌞 Andalucía"
# ])
#
# Y añadir en sidebar (junto a los sliders de CyL):
# st.sidebar.markdown("---")
# st.sidebar.subheader("🌞 Escenarios Andalucía")
# factor_desempleo_and   = st.sidebar.slider("Desempleo Andalucía",    0,100,65)
# factor_vivienda_and    = st.sidebar.slider("Vivienda/Turismo And.",   0,100,60)
# factor_agua            = st.sidebar.slider("Crisis Agua/Sequía",      0,100,55)
# factor_rural_urbano    = st.sidebar.slider("Peso Rural vs Urbano",    0,100,50)
# umbral_and             = st.sidebar.slider("Umbral electoral And.(%)",3,5,3)
#
# Añadir antes de los tabs:
# escanos_and, datos_prov_and = calcular_and(
#     factor_desempleo_and, factor_vivienda_and,
#     factor_agua, factor_rural_urbano, umbral_and
# )
# votos_and_avg = {p: sum(d["Votos"].get(p,0) for d in datos_prov_and)/len(datos_prov_and)
#                  for p in PARTIDOS_AND}
# polarizacion_and = calcular_indice_polarizacion(votos_and_avg)
# nep_and          = calcular_indice_fragmentacion(escanos_and)
# lsq_and          = calcular_sesgo_sistema(votos_and_avg, escanos_and)
# ma_and           = (TOTAL_AND // 2) + 1  # 55

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
        st.plotly_chart(fig_act, use_container_width=True)
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
        st.plotly_chart(fig_sim, use_container_width=True)
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
    st.plotly_chart(fig_delta, use_container_width=True)

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
        st.plotly_chart(fig_v, use_container_width=True)

    with col_pe:
        st.markdown(f"**Reparto D'Hondt — {prov_sel} ({ESCANOS_AND[prov_sel]} diputados)**")
        rep = {p: v for p, v in dp_and["Reparto"].items() if v > 0}
        if rep:
            fig_e = px.pie(values=list(rep.values()), names=list(rep.keys()),
                           color=list(rep.keys()),
                           color_discrete_map=COLORES_AND, hole=0.4)
            st.plotly_chart(fig_e, use_container_width=True)

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
    st.plotly_chart(fig_coal, use_container_width=True)
    st.dataframe(df_coal, use_container_width=True)

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
        st.plotly_chart(fig_rad, use_container_width=True)

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
        st.plotly_chart(fig_heat, use_container_width=True)

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
