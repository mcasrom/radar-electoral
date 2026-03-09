#!/usr/bin/env python3
"""
patch_auditoria_v2.py
=====================
Reemplaza render_tab_auditoria (y sus datos) en app.py
por la versión v2 completa.

Uso:
    cd /home/dietpi/espana-vota-2026
    python3 patch_auditoria_v2.py
"""

import re, shutil, ast
from pathlib import Path
from datetime import datetime

APP = Path("app.py")
NUEVO_TAB = Path("auditoria_tab_v2.py")

if not APP.exists():
    raise FileNotFoundError(f"No se encontró {APP}")
if not NUEVO_TAB.exists():
    raise FileNotFoundError(f"No se encontró {NUEVO_TAB}")

src = APP.read_text(encoding="utf-8")

# ---------- 1. Backup ----------------------------------------
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
bak = APP.with_suffix(f".py.bak_{ts}")
shutil.copy(APP, bak)
print(f"📦 Backup → {bak}")

# ---------- 2. Localizar bloque antiguo ----------------------
# Buscamos desde el comentario de datos hasta el final de render_tab_auditoria
MARKER_START = re.compile(
    r"(# ={3,}\n# AUDITORÍA.*?# ={3,}\n|"
    r"ENCUESTAS_EXTERNAS\s*=\s*\{|"
    r"AMBITOS\s*=\s*\{)",
    re.DOTALL
)

m = MARKER_START.search(src)
if not m:
    # Buscar directamente la función
    m = re.search(r"\ndef render_tab_auditoria\b", src)
    if not m:
        raise RuntimeError("No se encontró render_tab_auditoria en app.py")
    blk_start = m.start() + 1  # saltar el \n inicial
else:
    blk_start = m.start()

# Encontrar el final de render_tab_auditoria
func_m = re.search(r"^def render_tab_auditoria\b", src[blk_start:], re.MULTILINE)
if not func_m:
    raise RuntimeError("No se encontró def render_tab_auditoria tras el marcador")

abs_func_start = blk_start + func_m.start()

# Leer hasta el siguiente def/class al mismo nivel (col 0)
rest = src[abs_func_start:]
next_def = re.search(r"^\n(def |class )", rest, re.MULTILINE)
if next_def:
    blk_end = abs_func_start + next_def.start() + 1
else:
    blk_end = len(src)

old_block = src[blk_start:blk_end]
print(f"🔍 Bloque a reemplazar: líneas {src[:blk_start].count(chr(10))+1}–{src[:blk_end].count(chr(10))}")

# ---------- 3. Nuevo bloque ----------------------------------
nuevo_bloque = NUEVO_TAB.read_text(encoding="utf-8").rstrip() + "\n\n"

# ---------- 4. Reemplazar ------------------------------------
new_src = src[:blk_start] + nuevo_bloque + src[blk_end:]

# ---------- 5. Verificar sintaxis ----------------------------
try:
    ast.parse(new_src)
except SyntaxError as e:
    print(f"❌ Error de sintaxis tras el patch: {e}")
    raise

# ---------- 6. Escribir --------------------------------------
APP.write_text(new_src, encoding="utf-8")
print(f"✅ app.py actualizado — {len(new_src.splitlines())} líneas")
print("→ Reinicia Streamlit: pkill -f streamlit && streamlit run app.py &")
