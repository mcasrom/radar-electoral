#!/usr/bin/env python3
"""
ingest_daily.py — Ingesta diaria ligera
Optimizado para Odroid C2 / DietPi / 2GB RAM

Ejecuta: cron 06:00 cada día
Escribe: espana_vota.db (SQLite)
NO lanza Streamlit, NO carga plotly, NO carga numpy

Fuentes:
  - CIS barómetro mensual (RSS/web scraping ligero)
  - SEPE paro registrado provincial (datos.gob.es API)
  - INE indicadores socioeconómicos (API REST)
  - Recálculo de proyección con semilla diaria
"""

import sqlite3
import csv
import json
import os
import sys
import time
import random
import logging
import requests
from datetime import date, datetime
from pathlib import Path

# ===============================
# CONFIGURACIÓN DE PATHS
# ===============================
BASE_DIR = Path(__file__).parent
DB_PATH  = BASE_DIR / "espana_vota.db"
LOG_DIR  = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# ===============================
# LOGGING — archivo + stdout
# ===============================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "daily.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("ingest_daily")

# ===============================
# SEMILLA DIARIA FIJA
# Mismo resultado todo el día → cache de Streamlit efectiva
# ===============================
SEED_HOY = int(date.today().strftime("%Y%m%d"))
random.seed(SEED_HOY)
log.info(f"Semilla diaria: {SEED_HOY}")

# ===============================
# CONSTANTES ELECTORALES
# ===============================
PARTIDOS = ["PP","PSOE","VOX","SUMAR","SALF","ERC","JUNTS","PNV","BILDU","CC","UPN","BNG","OTROS"]
PARTIDOS_CYL = ["PP","PSOE","VOX","SUMAR","Por Ávila","UPL","OTROS"]

BASE_NACIONAL = {
    "PP":30.0,"PSOE":27.0,"VOX":16.0,"SUMAR":8.0,"SALF":4.0,
    "ERC":2.0,"JUNTS":2.0,"PNV":1.5,"BILDU":1.2,"CC":0.8,
    "UPN":0.5,"BNG":0.7,"OTROS":6.3
}
BASE_CYL = {
    "PP":36.0,"PSOE":24.0,"VOX":11.0,"SUMAR":6.5,
    "Por Ávila":1.5,"UPL":2.0,"OTROS":19.0
}

ESCANOS_NAC = {
    "Álava":4,"Albacete":4,"Alicante":12,"Almería":6,"Asturias":7,"Ávila":3,
    "Badajoz":6,"Baleares":8,"Barcelona":32,"Burgos":4,"Cáceres":4,"Cádiz":9,
    "Cantabria":5,"Castellón":5,"Ciudad Real":5,"Córdoba":6,"Cuenca":3,
    "Girona":6,"Granada":7,"Guadalajara":3,"Guipúzcoa":6,"Huelva":5,
    "Huesca":3,"Jaén":5,"La Coruña":8,"La Rioja":4,"Las Palmas":8,
    "León":4,"Lleida":4,"Lugo":4,"Madrid":37,"Málaga":11,"Murcia":10,
    "Navarra":5,"Ourense":4,"Palencia":3,"Pontevedra":7,"Salamanca":4,
    "Santa Cruz de Tenerife":7,"Segovia":3,"Sevilla":12,"Soria":2,
    "Tarragona":6,"Teruel":3,"Toledo":6,"Valencia":16,"Valladolid":5,
    "Vizcaya":8,"Zamora":3,"Zaragoza":7,"Ceuta":1,"Melilla":1
}
ESCANOS_CYL = {
    "Ávila":9,"Burgos":12,"León":14,"Palencia":7,
    "Salamanca":11,"Segovia":7,"Soria":5,"Valladolid":14,"Zamora":7
}

# ===============================
# BASE DE DATOS SQLite
# ===============================
def init_db(conn):
    """Crea tablas si no existen. Idempotente."""
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS historico_nacional (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha     TEXT NOT NULL,
            provincia TEXT NOT NULL,
            partido   TEXT NOT NULL,
            votos_pct REAL,
            escanos   INTEGER,
            fuente    TEXT DEFAULT 'modelo',
            UNIQUE(fecha, provincia, partido)
        );

        CREATE TABLE IF NOT EXISTS historico_cyl (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha     TEXT NOT NULL,
            provincia TEXT NOT NULL,
            partido   TEXT NOT NULL,
            votos_pct REAL,
            escanos   INTEGER,
            escenario TEXT,
            fuente    TEXT DEFAULT 'modelo',
            UNIQUE(fecha, provincia, partido, escenario)
        );

        CREATE TABLE IF NOT EXISTS encuestas (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha      TEXT NOT NULL,
            fuente     TEXT NOT NULL,
            partido    TEXT NOT NULL,
            valor_pct  REAL,
            tipo       TEXT,
            UNIQUE(fecha, fuente, partido)
        );

        CREATE TABLE IF NOT EXISTS socioeconomico (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha     TEXT NOT NULL,
            provincia TEXT NOT NULL,
            indicador TEXT NOT NULL,
            valor     REAL,
            UNIQUE(fecha, provincia, indicador)
        );

        CREATE TABLE IF NOT EXISTS log_ingesta (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha     TEXT NOT NULL,
            tipo      TEXT NOT NULL,
            fuente    TEXT NOT NULL,
            registros INTEGER,
            estado    TEXT,
            mensaje   TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_hist_fecha   ON historico_nacional(fecha);
        CREATE INDEX IF NOT EXISTS idx_hist_partido ON historico_nacional(partido);
        CREATE INDEX IF NOT EXISTS idx_cyl_fecha    ON historico_cyl(fecha);
        CREATE INDEX IF NOT EXISTS idx_enc_fecha    ON encuestas(fecha);
    """)
    conn.commit()
    log.info("Base de datos inicializada / verificada")

def log_ingesta(conn, tipo, fuente, registros, estado, mensaje=""):
    conn.execute(
        "INSERT INTO log_ingesta(fecha,tipo,fuente,registros,estado,mensaje) VALUES(?,?,?,?,?,?)",
        (str(date.today()), tipo, fuente, registros, estado, mensaje)
    )
    conn.commit()

# ===============================
# FUNCIONES ELECTORALES LIGERAS
# (sin numpy, sin pandas en runtime)
# ===============================
def normalizar(dic):
    total = sum(dic.values())
    if total == 0:
        return dic
    return {k: v * 100 / total for k, v in dic.items()}

def dhondt(votos, num_escanos):
    factor = 10000
    vi = {p: int(v * factor) for p, v in votos.items()}
    tabla = [(p, vi[p] / i) for p in vi for i in range(1, num_escanos + 1)]
    tabla.sort(key=lambda x: x[1], reverse=True)
    resultado = {p: 0 for p in vi}
    for i in range(num_escanos):
        resultado[tabla[i][0]] += 1
    return resultado

def ajustar_territorial_nac(base, provincia):
    datos = base.copy()
    if provincia == "Madrid":
        datos["PP"] += 3.0; datos["VOX"] += 1.5
    if provincia in ["Barcelona","Girona","Lleida","Tarragona"]:
        datos["ERC"] += 5.0; datos["JUNTS"] += 4.0; datos["PP"] -= 2.0
    if provincia in ["Vizcaya","Guipúzcoa","Álava"]:
        datos["PNV"] += 6.0; datos["BILDU"] += 5.0
    # Ruido reproducible (semilla diaria fija → mismo resultado todo el día)
    for p in datos:
        datos[p] += random.Random(int(SEED_HOY) + date.today().timetuple().tm_yday + abs(hash(p)) % 9999).uniform(-1.5, 1.5)
        datos[p] = max(0.0, datos[p])
    return normalizar(datos)

def ajustar_territorial_cyl(base, provincia):
    datos = base.copy()
    ajustes = {
        "León":       {"UPL": +4.5, "PP": -1.5},
        "Salamanca":  {"PP": +2.5, "PSOE": -1.0},
        "Valladolid": {"PSOE": +1.5, "SUMAR": +1.0, "PP": -1.0},
        "Ávila":      {"Por Ávila": +2.5},
        "Soria":      {"PP": +3.0},
        "Burgos":     {"PP": +1.0, "PSOE": +0.5},
        "Palencia":   {"PP": +1.5, "VOX": +0.5},
        "Segovia":    {"PP": +1.5, "VOX": +0.5},
        "Zamora":     {"PP": +1.5, "VOX": +0.5},
    }
    for p, delta in ajustes.get(provincia, {}).items():
        if p in datos:
            datos[p] += delta
    for p in datos:
        datos[p] += random.Random(int(SEED_HOY) + date.today().timetuple().tm_yday * 7 + abs(hash(p)) % 9999).uniform(-1.8, 1.8)
        datos[p] = max(0.0, datos[p])
    return normalizar(datos)

# ===============================
# CÁLCULO Y PERSISTENCIA
# ===============================
def calcular_y_guardar_nacional(conn):
    """Proyección nacional completa → SQLite. Solo escribe si no existe el registro del día."""
    fecha = str(date.today())
    insertados = 0
    for prov, num_esc in ESCANOS_NAC.items():
        votos = ajustar_territorial_nac(BASE_NACIONAL.copy(), prov)
        reparto = dhondt(votos, num_esc)
        for p in PARTIDOS:
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO historico_nacional
                    (fecha, provincia, partido, votos_pct, escanos, fuente)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (fecha, prov, p,
                      round(votos.get(p, 0), 4),
                      reparto.get(p, 0),
                      "modelo_diario"))
                insertados += conn.execute("SELECT changes()").fetchone()[0]
            except sqlite3.Error as e:
                log.warning(f"  Nacional {prov}/{p}: {e}")
    conn.commit()
    log.info(f"  Nacional: {insertados} registros nuevos insertados")
    log_ingesta(conn, "diario", "modelo_nacional", insertados, "ok")

def calcular_y_guardar_cyl(conn):
    """Proyección CyL → SQLite."""
    fecha = str(date.today())
    insertados = 0
    escenario = f"seed:{SEED_HOY}"
    for prov, num_esc in ESCANOS_CYL.items():
        votos = ajustar_territorial_cyl(BASE_CYL.copy(), prov)
        reparto = dhondt(votos, num_esc)
        for p in PARTIDOS_CYL:
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO historico_cyl
                    (fecha, provincia, partido, votos_pct, escanos, escenario, fuente)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (fecha, prov, p,
                      round(votos.get(p, 0), 4),
                      reparto.get(p, 0),
                      escenario, "modelo_diario"))
                insertados += conn.execute("SELECT changes()").fetchone()[0]
            except sqlite3.Error as e:
                log.warning(f"  CyL {prov}/{p}: {e}")
    conn.commit()
    log.info(f"  CyL: {insertados} registros nuevos insertados")
    log_ingesta(conn, "diario", "modelo_cyl", insertados, "ok")

# ===============================
# INGESTA SEPE — PARO PROVINCIAL
# API datos.gob.es — ligera, JSON paginado
# ===============================
def ingestar_paro_sepe(conn):
    """
    Descarga paro registrado por provincia desde datos.gob.es
    Dataset: EA0022 — Paro registrado por provincias
    Timeout agresivo para no bloquear el cron en el Odroid
    """
    URL = "https://datos.gob.es/apidata/catalog/dataset/EA0022/distribution/EA0022-OBS.json"
    log.info("  SEPE: descargando paro provincial...")
    try:
        r = requests.get(URL, timeout=15, headers={"User-Agent": "espana-vota/2.0"})
        if r.status_code != 200:
            log.warning(f"  SEPE: HTTP {r.status_code} — omitiendo")
            log_ingesta(conn, "diario", "sepe", 0, "warn", f"HTTP {r.status_code}")
            return
        data = r.json()
        registros = 0
        fecha = str(date.today())
        items = data.get("result", {}).get("items", [])[:60]  # max 60 items → ligero
        for item in items:
            provincia = item.get("Provincia", {}).get("label", "")
            valor = item.get("value", None)
            periodo = item.get("Periodo", {}).get("label", fecha)
            if provincia and valor is not None:
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO socioeconomico
                        (fecha, provincia, indicador, valor)
                        VALUES (?, ?, ?, ?)
                    """, (periodo[:10], provincia, "paro_registrado", float(valor)))
                    registros += conn.execute("SELECT changes()").fetchone()[0]
                except (sqlite3.Error, ValueError):
                    pass
        conn.commit()
        log.info(f"  SEPE: {registros} registros nuevos")
        log_ingesta(conn, "diario", "sepe", registros, "ok")
    except requests.exceptions.Timeout:
        log.warning("  SEPE: timeout — omitiendo (no crítico)")
        log_ingesta(conn, "diario", "sepe", 0, "timeout")
    except Exception as e:
        log.error(f"  SEPE error: {e}")
        log_ingesta(conn, "diario", "sepe", 0, "error", str(e))

# ===============================
# INGESTA CIS — BARÓMETRO MENSUAL
# Scraping ligero del RSS público del CIS
# ===============================
def ingestar_cis_rss(conn):
    """
    Monitoriza el RSS del CIS para detectar nuevos barómetros.
    Solo descarga metadatos, no el .sav completo.
    """
    RSS_URL = "https://www.cis.es/rss/estudios.xml"
    log.info("  CIS RSS: comprobando nuevos estudios...")
    try:
        r = requests.get(RSS_URL, timeout=10, headers={"User-Agent": "espana-vota/2.0"})
        if r.status_code != 200:
            log.warning(f"  CIS RSS: HTTP {r.status_code}")
            log_ingesta(conn, "diario", "cis_rss", 0, "warn", f"HTTP {r.status_code}")
            return
        # Parseo manual ligero — sin lxml ni BeautifulSoup
        content = r.text
        nuevos = 0
        # Buscar títulos de barómetros en el XML
        import re
        titulos = re.findall(r"<title><!\[CDATA\[(.*?)\]\]></title>", content)
        links   = re.findall(r"<link>(https://www\.cis\.es/.*?)</link>", content)
        fecha   = str(date.today())
        for i, titulo in enumerate(titulos[:10]):
            if "barómetro" in titulo.lower() or "barometro" in titulo.lower():
                link = links[i] if i < len(links) else ""
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO encuestas
                        (fecha, fuente, partido, valor_pct, tipo)
                        VALUES (?, ?, ?, ?, ?)
                    """, (fecha, "CIS_RSS", titulo[:120], 0.0, "metadata"))
                    nuevos += conn.execute("SELECT changes()").fetchone()[0]
                    if nuevos > 0:
                        log.info(f"  CIS: nuevo barómetro detectado → {titulo[:80]}")
                except sqlite3.Error:
                    pass
        conn.commit()
        log.info(f"  CIS RSS: {nuevos} entradas nuevas registradas")
        log_ingesta(conn, "diario", "cis_rss", nuevos, "ok")
    except requests.exceptions.Timeout:
        log.warning("  CIS RSS: timeout")
        log_ingesta(conn, "diario", "cis_rss", 0, "timeout")
    except Exception as e:
        log.error(f"  CIS RSS error: {e}")
        log_ingesta(conn, "diario", "cis_rss", 0, "error", str(e)[:200])

# ===============================
# SALUD DEL SISTEMA
# ===============================
def log_salud_sistema(conn):
    """Registra métricas del sistema en el log de ingesta."""
    try:
        # Memoria disponible
        with open("/proc/meminfo") as f:
            lines = f.readlines()
        mem_total = int([l for l in lines if "MemTotal" in l][0].split()[1])
        mem_free  = int([l for l in lines if "MemAvailable" in l][0].split()[1])
        mem_uso_pct = round((1 - mem_free / mem_total) * 100, 1)

        # Espacio en disco
        st = os.statvfs("/")
        disco_libre_mb = (st.f_bavail * st.f_frsize) // (1024 * 1024)

        # Tamaño de la DB
        db_size_kb = os.path.getsize(DB_PATH) // 1024 if DB_PATH.exists() else 0

        msg = f"RAM uso:{mem_uso_pct}% | Disco libre:{disco_libre_mb}MB | DB:{db_size_kb}KB"
        log.info(f"  Sistema: {msg}")
        log_ingesta(conn, "salud", "sistema", 0, "ok", msg)

        # Alerta si RAM > 80% o disco < 200MB
        if mem_uso_pct > 80:
            log.warning(f"  ⚠️  RAM alta: {mem_uso_pct}%")
        if disco_libre_mb < 200:
            log.warning(f"  ⚠️  Disco bajo: {disco_libre_mb}MB libres")

    except Exception as e:
        log.warning(f"  Salud sistema: {e}")

# ===============================
# MAIN
# ===============================
def main():
    t_inicio = time.time()
    log.info("=" * 50)
    log.info(f"INGEST DAILY — {date.today()} — seed:{SEED_HOY}")
    log.info("=" * 50)

    # Conexión SQLite — WAL mode para no bloquear Streamlit
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-8000")   # 8MB cache máx
    conn.execute("PRAGMA temp_store=MEMORY")

    try:
        init_db(conn)

        log.info("▶ Salud del sistema")
        log_salud_sistema(conn)

        log.info("▶ Calculando proyección nacional")
        calcular_y_guardar_nacional(conn)

        log.info("▶ Calculando proyección CyL")
        calcular_y_guardar_cyl(conn)

        log.info("▶ Ingesta SEPE paro provincial")
        ingestar_paro_sepe(conn)

        log.info("▶ Monitorización CIS RSS")
        ingestar_cis_rss(conn)

        # VACUUM mensual — solo el día 1 de cada mes
        if date.today().day == 1:
            log.info("▶ VACUUM mensual de SQLite")
            conn.execute("VACUUM")
            log.info("  VACUUM completado")

    except Exception as e:
        log.error(f"ERROR CRÍTICO en ingest_daily: {e}")
        sys.exit(1)
    finally:
        conn.close()

    elapsed = round(time.time() - t_inicio, 2)
    log.info(f"✓ Completado en {elapsed}s")
    log.info("=" * 50)

if __name__ == "__main__":
    main()

# Exportar CSV diario para Streamlit Cloud
import sqlite3 as _sq
_conn = _sq.connect("espana_vota.db")
_rows = _conn.execute("SELECT fecha, provincia, partido, votos_pct, escanos FROM historico_nacional ORDER BY fecha DESC, provincia, partido").fetchall()
with open("historico_semanal.csv", "w") as _f:
    _f.write("Fecha,Provincia,Partido,Votos,Escaños\n")
    for _r in _rows:
        _f.write(f"{_r[0]},{_r[1]},{_r[2]},{_r[3]:.4f},{_r[4]}\n")
_conn.close()

# Timestamp para Streamlit Cloud
with open('last_ingest.txt', 'w') as f:
    f.write(str(datetime.now().strftime('%Y-%m-%d %H:%M')))
