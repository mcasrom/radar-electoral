#!/usr/bin/env python3
"""
patch_energia.py — Integra tab Energía & Combustibles en app.py
Versión robusta — misma estrategia que patch_gal_mad.py

Ejecutar desde ~/espana-vota-2026/:
    python3 patch_energia.py
"""

import ast
import re
import shutil
from pathlib import Path
from datetime import datetime

APP    = Path("app.py")
F_ENE  = Path("energia_tab.py")
BACKUP = Path(f"app.py.bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

for f in [APP, F_ENE]:
    if not f.exists():
        print(f"❌ No se encuentra {f}"); exit(1)

shutil.copy2(APP, BACKUP)
print(f"✅ Backup: {BACKUP}")

content = APP.read_text(encoding="utf-8")
lines   = content.splitlines()

def find_line(lines, pattern):
    for i, l in enumerate(lines):
        if pattern in l.strip():
            return i
    return -1

# ======================================================
# LEER energia_tab.py
# ======================================================
ene_code = F_ENE.read_text(encoding="utf-8")

# Separar constantes + funciones de ingesta + render
pat_const  = re.compile(r'(# ={5,}\n# ENERGÍA.*?)(?=def obtener_precios)', re.DOTALL)
pat_funcs  = re.compile(r'(def obtener_precios.*?)(?=def render_tab_energia)', re.DOTALL)
pat_render = re.compile(r'(def render_tab_energia.*)', re.DOTALL)

m_const  = pat_const.search(ene_code)
m_funcs  = pat_funcs.search(ene_code)
m_render = pat_render.search(ene_code)

if not all([m_const, m_funcs, m_render]):
    print("❌ No se encontraron todos los bloques en energia_tab.py"); exit(1)

ene_constantes = m_const.group(1)
ene_funciones  = m_funcs.group(1)
ene_render     = m_render.group(1)

# ======================================================
# INSERTAR CÓDIGO ANTES DE st.tabs
# ======================================================
idx_tabs = find_line(lines, "= st.tabs([")
if idx_tabs == -1:
    print("❌ No se encontró st.tabs"); exit(1)
print(f"  st.tabs en línea: {idx_tabs + 1}")

bloque_ene = f"\n{ene_constantes}\n{ene_funciones}\n{ene_render}\n"
ene_lines  = bloque_ene.splitlines()
lines      = lines[:idx_tabs] + ene_lines + lines[idx_tabs:]
print(f"✅ Energía: {len(ene_lines)} líneas insertadas")

# Actualizar idx_tabs
idx_tabs = find_line(lines, "= st.tabs([")

# ======================================================
# ACTUALIZAR DECLARACIÓN DE TABS (9 → 10)
# ======================================================
idx_close = idx_tabs
for i in range(idx_tabs, min(idx_tabs + 15, len(lines))):
    if "])" in lines[i]:
        idx_close = i
        break

new_tabs = [
    'tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([',
    '    "🏛️ Hemiciclo Nacional",',
    '    "🗺️ Desglose Provincial",',
    '    "📡 Radar Estratégico",',
    '    "📋 Metodología y Fuentes",',
    '    "📈 Histórico Semanal",',
    '    "🏰 Castilla y León",',
    '    "🌞 Andalucía",',
    '    "🌿 Galicia",',
    '    "🏙️ Madrid",',
    '    "🛢️ Energía"',
    '])',
]
lines = lines[:idx_tabs] + new_tabs + lines[idx_close + 1:]
print(f"✅ Declaración de tabs actualizada a 10")

# ======================================================
# WITH TAB10 — insertar antes del footer
# ======================================================
idx_footer = find_line(lines, "# ---- FOOTER")
if idx_footer == -1:
    idx_footer = find_line(lines, "st.markdown(\"---\")")

tab10_block = """
# ========== TAB 10: ENERGÍA ==========
with tab10:
    render_tab_energia()

""".splitlines()

if idx_footer != -1:
    lines = lines[:idx_footer] + tab10_block + lines[idx_footer:]
    print(f"✅ with tab10 (Energía) insertado")
else:
    lines += tab10_block
    print("✅ with tab10 añadido al final")

# ======================================================
# ACTUALIZAR VERSIÓN
# ======================================================
new_content = "\n".join(lines)
new_content = new_content.replace(
    "v2.2 — CyL + Andalucía + Galicia + Madrid",
    "v2.3 — CyL + Andalucía + Galicia + Madrid + Energía"
)
print("✅ Versión actualizada a v2.3")

# ======================================================
# VERIFICAR SINTAXIS
# ======================================================
print("\n── VERIFICACIÓN SINTAXIS ──")
try:
    ast.parse(new_content)
    print("✅ Sintaxis OK")
except SyntaxError as e:
    print(f"❌ SyntaxError línea {e.lineno}: {e.msg}")
    print(f"   Contexto: {e.text}")
    print(f"   Backup: {BACKUP}")
    exit(1)

# ======================================================
# GUARDAR
# ======================================================
APP.write_text(new_content, encoding="utf-8")
total = new_content.count("\n")
print(f"\n✅ app.py guardado — {total} líneas")
print(f"   Backup: {BACKUP}")
print(f"\n▶ Siguiente paso:")
print(f"   git add app.py energia_tab.py patch_energia.py")
print(f"   git commit -m 'v2.3: tab Energía & Combustibles — MINETUR + Brent + semáforo electoral'")
print(f"   git push origin main")
