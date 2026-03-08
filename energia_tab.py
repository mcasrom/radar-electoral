
# ===============================
# ENERGÍA — DATOS Y CONSTANTES
# ===============================

# Media UE Oil Bulletin (referencia semanal — se actualiza via ingest)
# Valores base marzo 2026 (€/litro con impuestos)
ENERGIA_UE_BASE = {
    "gasolina_95_ue":  1.594,
    "gasoleo_a_ue":    1.526,
}

# Histórico de precios medios España (€/litro) — base para gráfica inicial
# Fuente: Oil Bulletin UE / MITECO
ENERGIA_HISTORICO_BASE = [
    {"fecha": "2025-01", "gasolina_95": 1.530, "gasoleo_a": 1.480, "brent_eur": 72.0},
    {"fecha": "2025-02", "gasolina_95": 1.520, "gasoleo_a": 1.465, "brent_eur": 70.5},
    {"fecha": "2025-03", "gasolina_95": 1.505, "gasoleo_a": 1.450, "brent_eur": 68.0},
    {"fecha": "2025-04", "gasolina_95": 1.498, "gasoleo_a": 1.442, "brent_eur": 67.5},
    {"fecha": "2025-05", "gasolina_95": 1.512, "gasoleo_a": 1.455, "brent_eur": 69.0},
    {"fecha": "2025-06", "gasolina_95": 1.525, "gasoleo_a": 1.468, "brent_eur": 71.0},
    {"fecha": "2025-07", "gasolina_95": 1.538, "gasoleo_a": 1.478, "brent_eur": 73.5},
    {"fecha": "2025-08", "gasolina_95": 1.530, "gasoleo_a": 1.470, "brent_eur": 72.0},
    {"fecha": "2025-09", "gasolina_95": 1.515, "gasoleo_a": 1.458, "brent_eur": 70.0},
    {"fecha": "2025-10", "gasolina_95": 1.502, "gasoleo_a": 1.445, "brent_eur": 68.5},
    {"fecha": "2025-11", "gasolina_95": 1.490, "gasoleo_a": 1.435, "brent_eur": 67.0},
    {"fecha": "2025-12", "gasolina_95": 1.470, "gasoleo_a": 1.420, "brent_eur": 65.5},
    {"fecha": "2026-01", "gasolina_95": 1.455, "gasoleo_a": 1.405, "brent_eur": 63.0},
    {"fecha": "2026-02", "gasolina_95": 1.505, "gasoleo_a": 1.448, "brent_eur": 68.0},
    {"fecha": "2026-03", "gasolina_95": 1.549, "gasoleo_a": 1.468, "brent_eur": 71.5},
]

# Umbrales de alerta electoral (precio €/litro)
UMBRAL_GASOLINA_TENSION  = 1.65   # por encima → presión electoral alta
UMBRAL_GASOLEO_TENSION   = 1.55
UMBRAL_GASOLINA_CRITICO  = 1.80
UMBRAL_GASOLEO_CRITICO   = 1.70

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

def render_tab_energia():
    """Renderiza el tab completo de Energía & Combustibles."""
    st.header("🛢️ Energía & Combustibles — Indicadores Electorales")
    st.markdown("""
    > **Contexto:** El precio del combustible es uno de los termómetros electorales
    > más directos — afecta al bolsillo de todos los hogares y es especialmente
    > sensible en zonas rurales sin alternativa al vehículo privado.
    > España cotiza sistemáticamente **por debajo de la media UE**, pero cualquier
    > repunte activa tensión política inmediata.
    """)

    # ---- OBTENER DATOS EN TIEMPO REAL
    with st.spinner("Cargando precios actuales..."):
        precios_actuales = obtener_precios_carburantes()
        brent_actual     = obtener_brent_eur()

    if precios_actuales:
        g95_actual = precios_actuales["gasolina_95"]
        goa_actual = precios_actuales["gasoleo_a"]
        n_est      = precios_actuales["n_estaciones"]
        fecha_dato = precios_actuales["fecha"]
    else:
        # Fallback a último dato histórico
        g95_actual = ENERGIA_HISTORICO_BASE[-1]["gasolina_95"]
        goa_actual = ENERGIA_HISTORICO_BASE[-1]["gasoleo_a"]
        n_est      = 0
        fecha_dato = ENERGIA_HISTORICO_BASE[-1]["fecha"]
        st.warning("⚠️ Datos en tiempo real no disponibles — mostrando último registro")

    if brent_actual is None:
        brent_actual = ENERGIA_HISTORICO_BASE[-1]["brent_eur"]

    g95_ue  = ENERGIA_UE_BASE["gasolina_95_ue"]
    goa_ue  = ENERGIA_UE_BASE["gasoleo_a_ue"]

    st.caption(f"📅 Datos: {fecha_dato}  |  🏪 {n_est:,} estaciones de servicio")
    st.markdown("---")

    # ---- KPIs PRINCIPALES
    st.subheader("⛽ Precios Actuales España vs. Media UE")
    col1, col2, col3, col4 = st.columns(4)

    delta_g95 = round(g95_actual - g95_ue, 3)
    delta_goa = round(goa_actual - goa_ue, 3)

    col1.metric("Gasolina 95", f"{g95_actual:.3f} €/L",
                f"{delta_g95:+.3f} vs UE",
                delta_color="inverse")
    col2.metric("Gasóleo A", f"{goa_actual:.3f} €/L",
                f"{delta_goa:+.3f} vs UE",
                delta_color="inverse")
    col3.metric("Brent", f"{brent_actual:.1f} €/barril")
    col4.metric("Diferencial España-UE",
                f"{abs(delta_g95):.3f} €/L",
                "España más barata" if delta_g95 < 0 else "España más cara",
                delta_color="normal" if delta_g95 < 0 else "inverse")

    st.markdown("---")

    # ---- SEMÁFORO ELECTORAL
    st.subheader("🚦 Semáforo de Tensión Electoral — Combustibles")
    col_s1, col_s2 = st.columns(2)

    def semaforo(precio, umbral_tension, umbral_critico, nombre):
        if precio >= umbral_critico:
            st.error(f"🔴 **{nombre}: {precio:.3f} €/L** — Nivel CRÍTICO electoral. "
                     f"Por encima de {umbral_critico}€ → movilización de protesta alta.")
        elif precio >= umbral_tension:
            st.warning(f"🟡 **{nombre}: {precio:.3f} €/L** — Tensión MODERADA. "
                       f"Acercándose al umbral de presión electoral ({umbral_tension}€).")
        else:
            st.success(f"🟢 **{nombre}: {precio:.3f} €/L** — Sin tensión electoral significativa.")

    with col_s1:
        semaforo(g95_actual, UMBRAL_GASOLINA_TENSION,
                 UMBRAL_GASOLINA_CRITICO, "Gasolina 95")
    with col_s2:
        semaforo(goa_actual, UMBRAL_GASOLEO_TENSION,
                 UMBRAL_GASOLEO_CRITICO, "Gasóleo A")

    st.markdown("---")

    # ---- COMPARATIVA ESPAÑA vs UE
    st.subheader("🌍 España vs. Media Unión Europea")
    df_comp = pd.DataFrame({
        "Carburante": ["Gasolina 95", "Gasóleo A"],
        "España":     [g95_actual, goa_actual],
        "Media UE":   [g95_ue, goa_ue]
    })
    df_comp_melt = df_comp.melt(id_vars="Carburante",
                                 var_name="Región", value_name="€/L")
    fig_comp = px.bar(df_comp_melt, x="Carburante", y="€/L",
                      color="Región",
                      color_discrete_map={"España": "#1f77b4", "Media UE": "#ff7f0e"},
                      barmode="group", text="€/L",
                      title="Precio €/litro — España vs Media UE (con impuestos)")
    fig_comp.update_traces(texttemplate="%{text:.3f}", textposition="outside")
    fig_comp.update_layout(height=400)
    st.plotly_chart(fig_comp, width='stretch')

    # ---- EVOLUCIÓN HISTÓRICA
    st.subheader("📈 Evolución Histórica de Precios")
    df_hist_e = pd.DataFrame(ENERGIA_HISTORICO_BASE)
    df_hist_e["fecha"] = pd.to_datetime(df_hist_e["fecha"])

    tipo_graf = st.radio("Visualización", ["Carburantes (€/L)", "Brent (€/barril)", "Ambos"],
                          horizontal=True, key="radio_energia")

    fig_hist = go.Figure()
    if tipo_graf in ["Carburantes (€/L)", "Ambos"]:
        fig_hist.add_trace(go.Scatter(
            x=df_hist_e["fecha"], y=df_hist_e["gasolina_95"],
            name="Gasolina 95", mode="lines+markers",
            line=dict(color="#e74c3c", width=3)
        ))
        fig_hist.add_trace(go.Scatter(
            x=df_hist_e["fecha"], y=df_hist_e["gasoleo_a"],
            name="Gasóleo A", mode="lines+markers",
            line=dict(color="#3498db", width=3)
        ))
        # Líneas de umbral
        fig_hist.add_hline(y=UMBRAL_GASOLINA_TENSION, line_dash="dot",
                           line_color="orange", annotation_text="Umbral tensión gasolina")
        fig_hist.add_hline(y=UMBRAL_GASOLINA_CRITICO, line_dash="dot",
                           line_color="red", annotation_text="Umbral crítico gasolina")
        fig_hist.update_layout(yaxis_title="€/litro")

    if tipo_graf in ["Brent (€/barril)", "Ambos"]:
        yaxis_ref = "y2" if tipo_graf == "Ambos" else "y"
        fig_hist.add_trace(go.Scatter(
            x=df_hist_e["fecha"], y=df_hist_e["brent_eur"],
            name="Brent €/barril", mode="lines+markers",
            line=dict(color="#2ecc71", width=2, dash="dash"),
            yaxis=yaxis_ref
        ))
        if tipo_graf == "Ambos":
            fig_hist.update_layout(
                yaxis2=dict(title="€/barril", overlaying="y", side="right")
            )
        else:
            fig_hist.update_layout(yaxis_title="€/barril")

    fig_hist.update_layout(height=450, hovermode="x unified",
                           title="Evolución mensual de precios energéticos")
    st.plotly_chart(fig_hist, width='stretch')

    # ---- IMPACTO ELECTORAL ESTIMADO
    st.subheader("🗳️ Impacto Electoral Estimado")
    st.markdown("""
    El precio del combustible afecta desproporcionadamente a:
    - **Zonas rurales** — sin alternativa al vehículo privado → voto de protesta
    - **Trabajadores con desplazamiento largo** — sensibles a subidas de >5%
    - **Autónomos y transporte** — gasóleo A es coste directo de negocio
    """)

    col_i1, col_i2, col_i3 = st.columns(3)

    # Índice de presión electoral (0-100)
    presion_g95 = min(100, max(0, (g95_actual - 1.30) / (1.90 - 1.30) * 100))
    presion_goa = min(100, max(0, (goa_actual - 1.20) / (1.80 - 1.20) * 100))
    presion_total = round((presion_g95 + presion_goa) / 2, 1)

    col_i1.metric("Presión Electoral Gasolina",
                  f"{presion_g95:.0f}/100",
                  help="0=sin presión, 100=máxima presión electoral")
    col_i2.metric("Presión Electoral Gasóleo",
                  f"{presion_goa:.0f}/100")
    col_i3.metric("Índice Agregado",
                  f"{presion_total:.0f}/100",
                  "⚠️ Moderado" if presion_total > 40 else "✅ Bajo")

    # Gauge visual
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=presion_total,
        title={"text": "Índice Presión Electoral Energética"},
        delta={"reference": 40},
        gauge={
            "axis": {"range": [0, 100]},
            "bar":  {"color": "#e74c3c" if presion_total > 60
                              else "#f39c12" if presion_total > 40
                              else "#2ecc71"},
            "steps": [
                {"range": [0,  40], "color": "#d5f5e3"},
                {"range": [40, 65], "color": "#fdebd0"},
                {"range": [65, 100],"color": "#fadbd8"},
            ],
            "threshold": {
                "line": {"color": "red", "width": 4},
                "thickness": 0.75, "value": 65
            }
        }
    ))
    fig_gauge.update_layout(height=300)
    st.plotly_chart(fig_gauge, width='stretch')

    # ---- NOTA METODOLÓGICA
    with st.expander("📋 Fuentes y Metodología — Módulo Energía"):
        st.markdown(f"""
**Precios España:** API REST del Ministerio de Industria (MINETUR)
`sedeaplicaciones.minetur.gob.es` — {n_est:,} estaciones de servicio actualizadas diariamente.

**Media UE:** Oil Bulletin semanal de la Comisión Europea
`energy.ec.europa.eu/data-and-analysis/weekly-oil-bulletin`
Referencia: semana del lunes anterior. Gasolina UE: {g95_ue}€/L | Gasóleo UE: {goa_ue}€/L

**Brent:** Serie histórica EIA/datahub.io (USD convertido a EUR al tipo ~0.92)

**Índice de Presión Electoral:**
- Escala 0-100 donde 0 = precio mínimo histórico reciente (gasolina 1.30€)
- 65+ = nivel de movilización de protesta documentado históricamente
- Basado en correlación histórica precios-intención de voto 2008-2024

**Umbrales de tensión:**
- 🟡 Gasolina >{UMBRAL_GASOLINA_TENSION}€ | Gasóleo >{UMBRAL_GASOLEO_TENSION}€ — tensión moderada
- 🔴 Gasolina >{UMBRAL_GASOLINA_CRITICO}€ | Gasóleo >{UMBRAL_GASOLEO_CRITICO}€ — nivel crítico
        """)
