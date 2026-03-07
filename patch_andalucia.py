#!/usr/bin/env python3
"""
patch_andalucia.py — Integra el tab de Andalucía en app.py de forma segura.
Ejecutar desde ~/espana-vota-2026/:
    python3 patch_andalucia.py

Hace backup automático antes de modificar.
"""

import re
import shutil
from pathlib import Path
from datetime import datetime

APP = Path("app.py")
PATCH = Path("andalucia_tab.py")
BACKUP = Path(f"app.py.bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

# ---- Verificaciones previas
if not APP.exists():
    print("❌ No se encuentra app.py"); exit(1)
if not PATCH.exists():
    print("❌ No se encuentra andalucia_tab.py"); exit(1)

# ---- Backup
shutil.copy2(APP, BACKUP)
print(f"✅ Backup creado: {BACKUP}")

content = APP.read_text(encoding="utf-8")
patch   = PATCH.read_text(encoding="utf-8")

# Extraer solo el código útil del patch (sin los comentarios de instrucción del render)
# El bloque de constantes y funciones va antes de los tabs
# El render_tab_andalucia() se llama dentro del tab

# ---- PASO 1: Añadir constantes y funciones ANTES de la línea de tabs
ANCHOR_TABS = 'tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(['
if ANCHOR_TABS not in content:
    print("❌ No se encuentra la declaración de tabs. Verifica app.py"); exit(1)

# Extraer el bloque de constantes+funciones del patch (hasta render_tab_andalucia)
patron_funciones = re.compile(
    r'(# ={5,}\n# ANDALUCÍA.*?)(?=def render_tab_andalucia)',
    re.DOTALL
)
m = patron_funciones.search(patch)
if not m:
    print("❌ No se encontró bloque de constantes en el patch"); exit(1)
bloque_constantes = m.group(1)

# Extraer la función render_tab_andalucia completa
patron_render = re.compile(r'(def render_tab_andalucia.*)', re.DOTALL)
m2 = patron_render.search(patch)
if not m2:
    print("❌ No se encontró render_tab_andalucia en el patch"); exit(1)
bloque_render = m2.group(1)

# Insertar constantes + función render antes de la declaración de tabs
insercion = f"\n{bloque_constantes}\n{bloque_render}\n\n"
content = content.replace(ANCHOR_TABS, insercion + ANCHOR_TABS)
print("✅ Constantes y funciones Andalucía insertadas")

# ---- PASO 2: Añadir sliders Andalucía al sidebar
ANCHOR_SIDEBAR = 'st.sidebar.markdown("---")\nst.sidebar.subheader("🏛️ Escenarios CyL")'
SIDEBAR_AND = """st.sidebar.markdown("---")
st.sidebar.subheader("🌞 Escenarios Andalucía")
factor_desempleo_and  = st.sidebar.slider("Desempleo Andalucía",     0, 100, 65)
factor_vivienda_and   = st.sidebar.slider("Vivienda/Turismo And.",    0, 100, 60)
factor_agua           = st.sidebar.slider("Crisis Agua/Sequía",       0, 100, 55)
factor_rural_urbano   = st.sidebar.slider("Peso Rural vs Urbano",     0, 100, 50)
umbral_and            = st.sidebar.slider("Umbral electoral And.(%)", 3, 5,    3)
"""
if ANCHOR_SIDEBAR in content:
    content = content.replace(ANCHOR_SIDEBAR, SIDEBAR_AND + "\n" + ANCHOR_SIDEBAR)
    print("✅ Sliders Andalucía añadidos al sidebar")
else:
    print("⚠️  Anchor sidebar no encontrado — añade los sliders manualmente")

# ---- PASO 3: Añadir cálculo de Andalucía antes de los tabs
ANCHOR_CALC = "escanos_totales,datos_prov = calcular()"
CALC_AND = """
# Cálculo Andalucía
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
"""
if ANCHOR_CALC in content:
    content = content.replace(ANCHOR_CALC, ANCHOR_CALC + CALC_AND)
    print("✅ Cálculo Andalucía añadido")
else:
    print("⚠️  Anchor cálculo no encontrado")

# ---- PASO 4: Actualizar declaración de tabs (6 → 7)
OLD_TABS = 'tab1,tab2,tab3,tab4,tab5,tab6 = st.tabs([\n    "🏛️ Hemiciclo Nacional",\n    "🗺️ Desglose Provincial",\n    "📡 Radar Estratégico",\n    "📋 Metodología y Fuentes",\n    "📈 Histórico Semanal",\n    "🏰 Castilla y León"\n])'
NEW_TABS = 'tab1,tab2,tab3,tab4,tab5,tab6,tab7 = st.tabs([\n    "🏛️ Hemiciclo Nacional",\n    "🗺️ Desglose Provincial",\n    "📡 Radar Estratégico",\n    "📋 Metodología y Fuentes",\n    "📈 Histórico Semanal",\n    "🏰 Castilla y León",\n    "🌞 Andalucía"\n])'
if OLD_TABS in content:
    content = content.replace(OLD_TABS, NEW_TABS)
    print("✅ Tab Andalucía añadido a la declaración de tabs")
else:
    print("⚠️  Declaración de tabs no encontrada exacta — editando con regex")
    content = re.sub(
        r'tab1,tab2,tab3,tab4,tab5,tab6 = st\.tabs\(\[',
        'tab1,tab2,tab3,tab4,tab5,tab6,tab7 = st.tabs([',
        content
    )
    # Añadir tab7 al final de la lista
    content = re.sub(
        r'("🏰 Castilla y León"\n\])',
        '"🏰 Castilla y León",\n    "🌞 Andalucía"\n])',
        content
    )
    print("✅ Tab Andalucía añadido via regex")

# ---- PASO 5: Añadir with tab7 al final, antes del footer
ANCHOR_FOOTER = "# ---- FOOTER\nst.markdown"
TAB7_BLOCK = """
# ========== TAB 7: ANDALUCÍA ==========
with tab7:
    render_tab_andalucia(
        escanos_and, datos_prov_and,
        polarizacion_and, nep_and, lsq_and,
        factor_desempleo_and, factor_vivienda_and,
        factor_agua, factor_rural_urbano
    )

"""
if ANCHOR_FOOTER in content:
    content = content.replace(ANCHOR_FOOTER, TAB7_BLOCK + ANCHOR_FOOTER)
    print("✅ with tab7 añadido antes del footer")
else:
    content += TAB7_BLOCK
    print("✅ with tab7 añadido al final")

# ---- PASO 6: Actualizar footer versión
content = content.replace(
    "v2.0 — Módulo CyL + Métricas Avanzadas",
    "v2.1 — Módulo CyL + Andalucía + Métricas Avanzadas"
)
content = content.replace(
    "v2.0  |  🕐",
    "v2.1  |  🕐"
)
print("✅ Versión actualizada a v2.1")

# ---- Guardar
APP.write_text(content, encoding="utf-8")
lineas = content.count("\n")
print(f"\n✅ app.py actualizado — {lineas} líneas")
print(f"   Backup en: {BACKUP}")
print("\n▶ Siguiente paso:")
print("   python3 -c \"import ast; ast.parse(open('app.py').read()); print('✅ Sintaxis OK')\"")
