#!/usr/bin/env python3
"""
patch_espana_vota_branding.py
España Vota 2026 – Branding OSINT verde + Ko-fi + links cruzados
"""
import os, shutil
from datetime import datetime

path = os.path.expanduser("~/espana-vota-2026/app.py")
shutil.copy2(path, path + f".bak_{datetime.now().strftime('%Y%m%d_%H%M')}")

with open(path, "r") as f:
    content = f.read()

# ── 1. Actualizar set_page_config ────────────────────────
OLD_CFG = 'st.set_page_config(layout="wide", page_title="España Vota 2026", page_icon="🗳️")'
NEW_CFG = 'st.set_page_config(layout="wide", page_title="España Vota 2026 · SIEG OSINT", page_icon="🗳️")'

if OLD_CFG in content:
    content = content.replace(OLD_CFG, NEW_CFG)
    print("set_page_config OK")

# ── 2. Sustituir st.title por logo OSINT ─────────────────
OLD_TITLE = 'st.title("🇪🇸 Sistema Multicapa de Inteligencia Electoral v2.0")'

LOGO_SVG = """st.markdown(\"\"\"
<svg width='100%' viewBox='0 0 680 130' xmlns='http://www.w3.org/2000/svg'>
<style>
@keyframes scan{0%{opacity:.1}50%{opacity:.35}100%{opacity:.1}}
@keyframes blink{0%,100%{opacity:1}49%{opacity:1}50%{opacity:0}99%{opacity:0}}
.sc{animation:scan 3s ease-in-out infinite}
.cu{animation:blink 1.1s step-end infinite}
</style>
<rect width='680' height='130' rx='4' fill='#0a0e0a' stroke='#1a2e1a'/>
<rect width='680' height='130' rx='4' fill='none' stroke='#00ff41' stroke-width='0.5' opacity='0.25'/>
<line x1='0' y1='26' x2='680' y2='26' stroke='#00ff41' stroke-width='0.3' opacity='0.15'/>
<circle cx='16' cy='13' r='4' fill='#ff5f57'/>
<circle cx='30' cy='13' r='4' fill='#febc2e'/>
<circle cx='44' cy='13' r='4' fill='#28c840'/>
<text x='340' y='18' text-anchor='middle' font-family='monospace' font-size='9' fill='#00ff41' opacity='0.35'>espana-vota-2026 — radar-electoral-osint</text>
<rect x='14' y='36' width='652' height='1' fill='#00ff41' opacity='0.06' class='sc'/>
<rect x='14' y='62' width='652' height='1' fill='#00ff41' opacity='0.06' class='sc' style='animation-delay:.8s'/>
<rect x='14' y='88' width='652' height='1' fill='#00ff41' opacity='0.06' class='sc' style='animation-delay:1.6s'/>
<text x='18' y='48' font-family='monospace' font-size='9' fill='#00ff41' opacity='0.45'>root@sieg:~$</text>
<text x='100' y='48' font-family='monospace' font-size='9' fill='#00ff41'>./radar --mode=electoral --target=espana-2026 --encuestas=ON</text>
<text x='18' y='64' font-family='monospace' font-size='8' fill='#4ade80' opacity='0.65'>[+] Partidos monitorizados: 13 | Circunscripciones: 52 | Modelo multicapa: ACTIVO</text>
<text x='18' y='95' font-family='monospace' font-size='20' font-weight='bold' fill='#00ff41' letter-spacing='3'>ESPANA VOTA 2026</text>
<text x='290' y='95' font-family='monospace' font-size='12' fill='#00cc33' letter-spacing='2'>Radar Electoral · OSINT</text>
<text x='290' y='110' font-family='monospace' font-size='9' fill='#009922' opacity='0.7'>Sistema Multicapa de Inteligencia Electoral v2.0</text>
<text x='18' y='120' font-family='monospace' font-size='7' fill='#00ff41' opacity='0.3'>© 2026 M.Castillo · mybloggingnotes@gmail.com</text>
<rect x='620' y='104' width='42' height='12' rx='2' fill='none' stroke='#00ff41' stroke-width='0.5' opacity='0.35'/>
<text x='641' y='113' font-family='monospace' font-size='7' fill='#00ff41' opacity='0.45' text-anchor='middle'>LIVE</text>
</svg>
\"\"\", unsafe_allow_html=True)"""

if OLD_TITLE in content:
    content = content.replace(OLD_TITLE, LOGO_SVG)
    print("Logo OSINT OK")
else:
    print("Logo NOT FOUND")

# ── 3. Añadir Ko-fi + links al sidebar ───────────────────
OLD_SIDEBAR = 'st.sidebar.header("🎛️ Control de Escenarios")'

NEW_SIDEBAR = """# Branding sidebar
st.sidebar.markdown(\"\"\"
<div style='padding:0.4rem 0 0.8rem 0; border-bottom:1px solid rgba(0,255,65,0.15); margin-bottom:0.8rem'>
    <div style='font-size:0.65rem; font-weight:600; letter-spacing:0.12em;
                text-transform:uppercase; color:#00cc33; margin-bottom:2px'>SIEG OSINT</div>
    <div style='font-size:0.95rem; font-weight:600; color:#00ff41; line-height:1.2'>
        España Vota 2026
    </div>
    <div style='font-size:0.65rem; color:#4a7a4a; margin-top:3px'>
        Radar Electoral · Análisis Multicapa
    </div>
</div>
\"\"\", unsafe_allow_html=True)

st.sidebar.markdown(\"\"\"
<div style='font-size:0.75rem; line-height:1.9; opacity:0.75; margin-bottom:8px'>
    <div style='font-weight:600; margin-bottom:6px; font-size:0.8rem; color:#00ff41'>🛰️ Red SIEG OSINT</div>
    <a href='https://mcasrom.github.io/sieg-osint' target='_blank'
       style='display:block; color:#4ade80; text-decoration:none; margin-bottom:4px'>🌐 Portal SIEG OSINT</a>
    <a href='https://politica-nacional-osint.streamlit.app' target='_blank'
       style='display:block; color:#4ade80; text-decoration:none; margin-bottom:4px'>📊 SIEG Política Nacional</a>
    <a href='https://fake-news-narrative.streamlit.app' target='_blank'
       style='display:block; color:#4ade80; text-decoration:none; margin-bottom:4px'>📡 Narrative Radar</a>
    <a href='https://t.me/sieg_politica' target='_blank'
       style='display:block; color:#4ade80; text-decoration:none; margin-bottom:4px'>📢 Canal @sieg_politica</a>
</div>
\"\"\", unsafe_allow_html=True)

st.sidebar.markdown(\"\"\"
<div style='text-align:center; padding:6px 0; margin-bottom:8px'>
    <a href='https://ko-fi.com/m_castillo' target='_blank'
       style='display:inline-block; background:#FF5E5B; color:white;
              font-weight:600; font-size:0.75rem; padding:6px 14px;
              border-radius:16px; text-decoration:none'>
        ☕ Buy me a coffee
    </a>
    <div style='font-size:0.65rem; opacity:0.4; margin-top:3px'>Apoya SIEG OSINT</div>
</div>
\"\"\", unsafe_allow_html=True)

st.sidebar.markdown("---")

st.sidebar.header("🎛️ Control de Escenarios")"""

if OLD_SIDEBAR in content:
    content = content.replace(OLD_SIDEBAR, NEW_SIDEBAR)
    print("Sidebar OK")
else:
    print("Sidebar NOT FOUND")

# ── 4. Tema oscuro OSINT ─────────────────────────────────
streamlit_dir = os.path.expanduser("~/espana-vota-2026/.streamlit")
os.makedirs(streamlit_dir, exist_ok=True)
config_path = os.path.join(streamlit_dir, "config.toml")
with open(config_path, "w") as f:
    f.write("""[browser]
gatherUsageStats = false

[theme]
base = 'dark'
backgroundColor = '#0a0e0a'
secondaryBackgroundColor = '#0f1a0f'
primaryColor = '#00ff41'
textColor = '#c8ffc8'
font = 'monospace'
""")
print("config.toml OK")

# ── 5. Copyright en footer ───────────────────────────────
if '© 2026 M. Castillo' not in content:
    content = content.rstrip() + """

st.markdown("---")
st.markdown(\"\"\"
<div style='text-align:center; font-size:0.72rem; opacity:0.35; font-family:monospace; padding:8px 0'>
    © 2026 M. Castillo ·
    <a href='mailto:mybloggingnotes@gmail.com' style='color:inherit'>mybloggingnotes@gmail.com</a> ·
    <a href='https://mcasrom.github.io/sieg-osint' target='_blank' style='color:inherit'>SIEG OSINT España</a>
</div>
\"\"\", unsafe_allow_html=True)
"""
    print("Footer copyright OK")

with open(path, "w") as f:
    f.write(content)

print("Patch completado OK")
