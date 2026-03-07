#!/usr/bin/env python3
"""
patch_gal_mad.py — Integra tabs de Galicia y Madrid en app.py
Versión robusta — aprende de los errores del patch anterior.

Ejecutar desde ~/espana-vota-2026/:
    python3 patch_gal_mad.py

Estrategia:
  1. Backup automático con timestamp
  2. Busca anchors con strip() para tolerar espacios/tabs
  3. Inserta funciones ANTES de la línea de tabs (nunca después)
  4. Inserta llamadas DESPUÉS de la última función definida
  5. Añade with tabN ANTES del footer
  6. Verifica sintaxis antes de guardar
"""

import ast
import re
import shutil
from pathlib import Path
from datetime import datetime

APP     = Path("app.py")
F_GAL   = Path("galicia_tab.py")
F_MAD   = Path("madrid_tab.py")
BACKUP  = Path(f"app.py.bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

# ---- Verificaciones
for f in [APP, F_GAL, F_MAD]:
    if not f.exists():
        print(f"❌ No se encuentra {f}"); exit(1)

# ---- Backup
shutil.copy2(APP, BACKUP)
print(f"✅ Backup: {BACKUP}")

content = APP.read_text(encoding="utf-8")
lines   = content.splitlines()

# ---- Utilidades
def find_line(lines, pattern, strip=True):
    """Busca la primera línea que contiene pattern. Retorna índice 0-based."""
    for i, l in enumerate(lines):
        target = l.strip() if strip else l
        if pattern in target:
            return i
    return -1

def find_last_def(lines, keyword):
    """Retorna el índice de la última línea de la función que empieza con keyword."""
    start = find_line(lines, keyword)
    if start == -1:
        return -1
    # Avanzar hasta encontrar la siguiente def/class al mismo nivel o fin
    for i in range(start + 1, len(lines)):
        l = lines[i]
        if l and not l[0].isspace() and (l.startswith('def ') or
           l.startswith('class ') or l.startswith('#') or
           l.startswith('st.') or l.startswith('tab') or
           l.startswith('escanos') or l.startswith('with ')):
            return i - 1
    return len(lines) - 1

# ======================================================
# GALICIA
# ======================================================
print("\n── GALICIA ──")
gal_code = F_GAL.read_text(encoding="utf-8")

# Extraer bloques
pat_const = re.compile(r'(# ={5,}\n# GALICIA.*?)(?=def ajustar_escenario_gal)', re.DOTALL)
pat_funcs = re.compile(r'(def ajustar_escenario_gal.*?)(?=def render_tab_galicia)', re.DOTALL)
pat_render= re.compile(r'(def render_tab_galicia.*)', re.DOTALL)

m_const  = pat_const.search(gal_code)
m_funcs  = pat_funcs.search(gal_code)
m_render = pat_render.search(gal_code)

if not all([m_const, m_funcs, m_render]):
    print("❌ No se encontraron todos los bloques en galicia_tab.py"); exit(1)

gal_constantes = m_const.group(1)
gal_funciones  = m_funcs.group(1)
gal_render     = m_render.group(1)

# Insertar ANTES de la línea de tabs
idx_tabs = find_line(lines, "= st.tabs([")
if idx_tabs == -1:
    print("❌ No se encontró st.tabs"); exit(1)
print(f"  Línea st.tabs encontrada: {idx_tabs + 1}")

bloque_gal = f"\n{gal_constantes}\n{gal_funciones}\n{gal_render}\n"
gal_lines  = bloque_gal.splitlines()
lines      = lines[:idx_tabs] + gal_lines + lines[idx_tabs:]
print(f"✅ Galicia: constantes + funciones + render insertados ({len(gal_lines)} líneas)")

# Actualizar idx_tabs tras inserción
idx_tabs = find_line(lines, "= st.tabs([")

# ======================================================
# MADRID
# ======================================================
print("\n── MADRID ──")
mad_code = F_MAD.read_text(encoding="utf-8")

pat_const_m = re.compile(r'(# ={5,}\n# MADRID.*?)(?=def ajustar_escenario_mad)', re.DOTALL)
pat_funcs_m = re.compile(r'(def ajustar_escenario_mad.*?)(?=def render_tab_madrid)', re.DOTALL)
pat_render_m= re.compile(r'(def render_tab_madrid.*)', re.DOTALL)

m_const_m  = pat_const_m.search(mad_code)
m_funcs_m  = pat_funcs_m.search(mad_code)
m_render_m = pat_render_m.search(mad_code)

if not all([m_const_m, m_funcs_m, m_render_m]):
    print("❌ No se encontraron todos los bloques en madrid_tab.py"); exit(1)

mad_constantes = m_const_m.group(1)
mad_funciones  = m_funcs_m.group(1)
mad_render     = m_render_m.group(1)

bloque_mad = f"\n{mad_constantes}\n{mad_funciones}\n{mad_render}\n"
mad_lines  = bloque_mad.splitlines()
lines      = lines[:idx_tabs] + mad_lines + lines[idx_tabs:]
print(f"✅ Madrid: constantes + funciones + render insertados ({len(mad_lines)} líneas)")

# Actualizar idx_tabs
idx_tabs = find_line(lines, "= st.tabs([")

# ======================================================
# SIDEBAR — sliders Galicia y Madrid
# ======================================================
print("\n── SIDEBAR ──")
idx_sidebar = find_line(lines, 'subheader("🌞 Escenarios Andalucía")')
if idx_sidebar == -1:
    idx_sidebar = find_line(lines, 'subheader("🏛️ Escenarios CyL")')

sliders_gal = """
st.sidebar.markdown("---")
st.sidebar.subheader("🌿 Escenarios Galicia")
factor_despoblacion_gal = st.sidebar.slider("Despoblación Galicia",   0, 100, 60)
factor_bng_urbano       = st.sidebar.slider("BNG Urbano (Vigo/Coruña)",0,100, 55)
factor_pesca            = st.sidebar.slider("Sector Pesquero",         0, 100, 50)
factor_autogobierno_gal = st.sidebar.slider("Autogobierno Galicia",    0, 100, 45)
umbral_gal              = st.sidebar.slider("Umbral electoral Gal.(%)",3, 5,   5)
""".splitlines()

sliders_mad = """
st.sidebar.markdown("---")
st.sidebar.subheader("🏙️ Escenarios Madrid")
factor_vivienda_mad = st.sidebar.slider("Vivienda Madrid",      0, 100, 70)
factor_ayuso        = st.sidebar.slider("Efecto Ayuso",         0, 100, 65)
factor_fiscal       = st.sidebar.slider("Fiscalidad Baja",      0, 100, 60)
factor_migracion    = st.sidebar.slider("Migración Madrid",     0, 100, 55)
umbral_mad          = st.sidebar.slider("Umbral Madrid (%)",    3, 5,    5)
""".splitlines()

if idx_sidebar != -1:
    lines = lines[:idx_sidebar] + sliders_gal + sliders_mad + lines[idx_sidebar:]
    print(f"✅ Sliders Galicia y Madrid añadidos al sidebar")
else:
    print("⚠️  Sidebar anchor no encontrado — añadir sliders manualmente")

# Actualizar idx_tabs
idx_tabs = find_line(lines, "= st.tabs([")

# ======================================================
# DECLARACIÓN DE TABS — ampliar a 9
# ======================================================
print("\n── TABS ──")
idx_tabs = find_line(lines, "= st.tabs([")
print(f"  st.tabs en línea: {idx_tabs + 1}")

# Buscar la línea de declaración y reemplazar
tab_line = lines[idx_tabs]
# Contar cuántos tabs hay actualmente
idx_close = idx_tabs
for i in range(idx_tabs, min(idx_tabs + 15, len(lines))):
    if "])" in lines[i] or "]))" in lines[i]:
        idx_close = i
        break

new_tabs = [
    'tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([',
    '    "🏛️ Hemiciclo Nacional",',
    '    "🗺️ Desglose Provincial",',
    '    "📡 Radar Estratégico",',
    '    "📋 Metodología y Fuentes",',
    '    "📈 Histórico Semanal",',
    '    "🏰 Castilla y León",',
    '    "🌞 Andalucía",',
    '    "🌿 Galicia",',
    '    "🏙️ Madrid"',
    '])',
]
lines = lines[:idx_tabs] + new_tabs + lines[idx_close + 1:]
print(f"✅ Declaración de tabs actualizada a 9")

# ======================================================
# CÁLCULO — insertar DESPUÉS de la declaración de tabs
# y ANTES del TAB 1
# ======================================================
print("\n── CÁLCULO ──")
idx_tab1 = find_line(lines, "TAB 1: HEMICICLO NACIONAL")
if idx_tab1 == -1:
    idx_tab1 = find_line(lines, "with tab1:")

calc_gal = """
# ===============================
# EJECUCIÓN — CÁLCULO GALICIA
# ===============================
escanos_gal, datos_prov_gal = calcular_gal(
    factor_despoblacion_gal, factor_bng_urbano,
    factor_pesca, factor_autogobierno_gal, umbral_gal
)
votos_gal_avg = {p: sum(d["Votos"].get(p,0) for d in datos_prov_gal)/len(datos_prov_gal)
                 for p in PARTIDOS_GAL}
polarizacion_gal = calcular_indice_polarizacion(votos_gal_avg)
nep_gal          = calcular_indice_fragmentacion(escanos_gal)
lsq_gal          = calcular_sesgo_sistema(votos_gal_avg, escanos_gal)
""".splitlines()

calc_mad = """
# ===============================
# EJECUCIÓN — CÁLCULO MADRID
# ===============================
reparto_mad, votos_mad, datos_zonas_mad = calcular_mad(
    factor_vivienda_mad, factor_ayuso, factor_fiscal, factor_migracion, umbral_mad
)
polarizacion_mad = calcular_indice_polarizacion(votos_mad)
nep_mad          = calcular_indice_fragmentacion(reparto_mad)
lsq_mad          = calcular_sesgo_sistema(votos_mad, reparto_mad)
""".splitlines()

if idx_tab1 != -1:
    lines = lines[:idx_tab1] + calc_gal + calc_mad + lines[idx_tab1:]
    print(f"✅ Cálculos Galicia y Madrid insertados antes de TAB 1")
else:
    print("⚠️  TAB 1 no encontrado")

# ======================================================
# WITH TAB8 y TAB9 — insertar antes del footer
# ======================================================
print("\n── WITH TAB8 / TAB9 ──")
idx_footer = find_line(lines, "# ---- FOOTER")
if idx_footer == -1:
    idx_footer = find_line(lines, "st.markdown(\"---\")")

tab8_block = """
# ========== TAB 8: GALICIA ==========
with tab8:
    render_tab_galicia(
        escanos_gal, datos_prov_gal,
        polarizacion_gal, nep_gal, lsq_gal,
        factor_despoblacion_gal, factor_bng_urbano,
        factor_pesca, factor_autogobierno_gal
    )
""".splitlines()

tab9_block = """
# ========== TAB 9: MADRID ==========
with tab9:
    render_tab_madrid(
        reparto_mad, votos_mad, datos_zonas_mad,
        polarizacion_mad, nep_mad, lsq_mad,
        factor_vivienda_mad, factor_ayuso,
        factor_fiscal, factor_migracion
    )

""".splitlines()

if idx_footer != -1:
    lines = lines[:idx_footer] + tab8_block + tab9_block + lines[idx_footer:]
    print(f"✅ with tab8 (Galicia) y tab9 (Madrid) insertados")
else:
    lines += tab8_block + tab9_block
    print("✅ with tab8/tab9 añadidos al final")

# ======================================================
# ACTUALIZAR VERSIÓN
# ======================================================
new_content = "\n".join(lines)
new_content = new_content.replace(
    "v2.1 — Módulo CyL + Andalucía + Métricas Avanzadas",
    "v2.2 — CyL + Andalucía + Galicia + Madrid"
)
new_content = new_content.replace("v2.1  |  🕐", "v2.2  |  🕐")
print("✅ Versión actualizada a v2.2")

# ======================================================
# VERIFICAR SINTAXIS ANTES DE GUARDAR
# ======================================================
print("\n── VERIFICACIÓN SINTAXIS ──")
try:
    ast.parse(new_content)
    print("✅ Sintaxis OK")
except SyntaxError as e:
    print(f"❌ Error de sintaxis en línea {e.lineno}: {e.msg}")
    print(f"   Contexto: {e.text}")
    print(f"   Backup disponible en: {BACKUP}")
    print("   NO se guardará el fichero.")
    exit(1)

# ======================================================
# GUARDAR
# ======================================================
APP.write_text(new_content, encoding="utf-8")
total_lines = new_content.count("\n")
print(f"\n✅ app.py guardado — {total_lines} líneas")
print(f"   Backup en: {BACKUP}")
print(f"\n▶ Siguiente paso:")
print(f"   git add app.py galicia_tab.py madrid_tab.py patch_gal_mad.py")
print(f"   git commit -m 'v2.2: tabs Galicia + Madrid'")
print(f"   git push origin main")
