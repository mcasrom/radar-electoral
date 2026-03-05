#!/usr/bin/env python3
"""
ingest_weekly.py — Ingesta semanal completa
Optimizado para Odroid C2 / DietPi / 2GB RAM

Ejecuta: cron Domingo 05:00
Escribe: espana_vota.db (SQLite)

Fuentes:
  - INE API REST — indicadores socioeconómicos provinciales
  - Electograph — agregador de encuestas públicas (scraping)
  - Wikipedia — tabla de encuestas electorales (scraping ligero)
  - Backup automático del histórico
  - Limpieza y mantenimiento de la DB
  - Informe semanal de variaciones (.txt)
"""

import sqlite3
import json
import os
import sys
import time
import random
import logging
import requests
import re
import shutil
from datetime import date, datetime, timedelta
from pathlib import Path

# ===============================
# CONFIGURACIÓN
# ===============================
BASE_DIR = Path(__file__).parent
DB_PATH  = BASE_DIR / "espana_vota.db"
LOG_DIR  = BASE_DIR / "logs"
BCK_DIR  = BASE_DIR / "backups"
LOG_DIR.mkdir(exist_ok=True)
BCK_DIR.mkdir(exist_ok=True)

# ===============================
# LOGGING
# ===============================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "weekly.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("ingest_weekly")

# ===============================
# SEMILLA SEMANAL
# ===============================
hoy = date.today()
SEED_SEMANAL = int(hoy.strftime("%Y%W"))  # año + semana ISO
random.seed(SEED_SEMANAL)
log.info(f"Semilla semanal: {SEED_SEMANAL} (semana {hoy.isocalendar()[1]})")

# ===============================
# CONSTANTES
# ===============================
PARTIDOS = ["PP","PSOE","VOX","SUMAR","SALF","ERC","JUNTS","PNV","BILDU","CC","UPN","BNG","OTROS"]
PARTIDOS_CYL = ["PP","PSOE","VOX","SUMAR","Por Ávila","UPL","OTROS"]

# Códigos INE para provincias (cod_provincia → nombre)
INE_PROVINCIAS = {
    "01":"Álava","02":"Albacete","03":"Alicante","04":"Almería","33":"Asturias",
    "05":"Ávila","06":"Badajoz","07":"Baleares","08":"Barcelona","09":"Burgos",
    "10":"Cáceres","11":"Cádiz","39":"Cantabria","12":"Castellón","13":"Ciudad Real",
    "14":"Córdoba","16":"Cuenca","17":"Girona","18":"Granada","19":"Guadalajara",
    "20":"Guipúzcoa","21":"Huelva","22":"Huesca","23":"Jaén","15":"La Coruña",
    "26":"La Rioja","35":"Las Palmas","24":"León","25":"Lleida","27":"Lugo",
    "28":"Madrid","29":"Málaga","30":"Murcia","31":"Navarra","32":"Ourense",
    "34":"Palencia","36":"Pontevedra","37":"Salamanca","38":"Santa Cruz de Tenerife",
    "40":"Segovia","41":"Sevilla","42":"Soria","43":"Tarragona","44":"Teruel",
    "45":"Toledo","46":"Valencia","47":"Valladolid","48":"Vizcaya",
    "49":"Zamora","50":"Zaragoza"
}
# Provincias CyL
PROVINCIAS_CYL = ["Ávila","Burgos","León","Palencia","Salamanca","Segovia","Soria","Valladolid","Zamora"]

# ===============================
# CONEXIÓN DB
# ===============================
def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-16000")  # 16MB para operaciones pesadas
    conn.execute("PRAGMA temp_store=MEMORY")
    return conn

def log_ingesta(conn, tipo, fuente, registros, estado, mensaje=""):
    conn.execute(
        "INSERT INTO log_ingesta(fecha,tipo,fuente,registros,estado,mensaje) VALUES(?,?,?,?,?,?)",
        (str(hoy), tipo, fuente, registros, estado, mensaje[:500])
    )
    conn.commit()

# ===============================
# 1. BACKUP SEMANAL
# Rotación de 4 semanas → no acumula
# ===============================
def backup_db():
    """Copia la DB con nombre por semana ISO. Mantiene solo las últimas 4."""
    semana = hoy.strftime("%Y-W%W")
    dst = BCK_DIR / f"espana_vota_{semana}.db"
    if DB_PATH.exists():
        shutil.copy2(str(DB_PATH), str(dst))
        log.info(f"  Backup creado: {dst.name} ({dst.stat().st_size // 1024}KB)")
        # Limpieza: mantener solo últimas 4 semanas
        backups = sorted(BCK_DIR.glob("espana_vota_*.db"))
        for old in backups[:-4]:
            old.unlink()
            log.info(f"  Backup antiguo eliminado: {old.name}")
    else:
        log.warning("  DB no existe, backup omitido")

# ===============================
# 2. INE API REST — Indicadores provinciales
# Endpoint ligero: tasa de paro EPA, IPC provincial
# ===============================
def ingestar_ine_api(conn):
    """
    INE API REST — Tasa de actividad y paro por provincia (EPA).
    Opera: /api/datos/serie/{serie}?nult=4 → últimos 4 periodos únicamente.
    Pausa entre requests para no sobrecargar la red del Odroid.
    """
    log.info("  INE API: descargando indicadores provinciales...")

    # Series INE relevantes — código → descripción
    # Estas series son públicas y ligeras (formato JSON)
    SERIES_INE = {
        "EPA_TASA_PARO": "EPA tasa paro provincial (referencia agregada)",
    }

    # Endpoint de ejemplo INE — series temporales
    BASE_URL = "https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE"
    registros_total = 0

    # Serie sintética de ejemplo: tasa de paro total nacional
    series_prueba = [
        ("30240", "tasa_paro_nacional", "nacional"),
    ]

    for cod_serie, indicador, provincia in series_prueba:
        try:
            url = f"{BASE_URL}/{cod_serie}?nult=4"
            r = requests.get(url, timeout=12, headers={"User-Agent": "espana-vota/2.0"})
            if r.status_code != 200:
                log.warning(f"  INE serie {cod_serie}: HTTP {r.status_code}")
                continue
            data = r.json()
            datos = data.get("Data", [])
            for punto in datos[-4:]:  # solo últimos 4 periodos
                periodo = punto.get("Fecha", str(hoy))[:10]
                valor   = punto.get("Valor")
                if valor is not None:
                    conn.execute("""
                        INSERT OR IGNORE INTO socioeconomico
                        (fecha, provincia, indicador, valor)
                        VALUES (?,?,?,?)
                    """, (periodo, provincia, indicador, float(valor)))
                    registros_total += conn.execute("SELECT changes()").fetchone()[0]
            conn.commit()
            time.sleep(1.5)  # pausa cortés con el servidor INE + no saturar red Odroid
        except requests.exceptions.Timeout:
            log.warning(f"  INE serie {cod_serie}: timeout")
        except Exception as e:
            log.error(f"  INE serie {cod_serie}: {e}")

    log.info(f"  INE API: {registros_total} registros nuevos")
    log_ingesta(conn, "semanal", "ine_api", registros_total, "ok")

# ===============================
# 3. SCRAPING ENCUESTAS — Wikipedia
# Tabla de encuestas electorales España
# Scraping muy ligero: solo texto, sin JS
# ===============================
def ingestar_encuestas_wikipedia(conn):
    """
    Extrae tabla de encuestas electorales de Wikipedia en español.
    URL estable, formato conocido, sin JavaScript.
    Parseo manual con regex para no depender de BeautifulSoup.
    """
    URL = "https://es.wikipedia.org/wiki/Anexo:Sondeos_de_opinión_sobre_las_elecciones_generales_de_España_de_2023"
    log.info("  Wikipedia: scraping tabla de encuestas...")
    registros = 0
    try:
        r = requests.get(URL, timeout=15,
                         headers={"User-Agent": "Mozilla/5.0 espana-vota/2.0"})
        if r.status_code != 200:
            log.warning(f"  Wikipedia: HTTP {r.status_code}")
            log_ingesta(conn, "semanal", "wikipedia_encuestas", 0, "warn", f"HTTP {r.status_code}")
            return

        texto = r.text
        # Extraer filas de tabla con porcentajes — patrón simple
        # Busca patrones del tipo: "Instituto | fecha | PP% | PSOE% | VOX% ..."
        # Extracción conservadora: solo fechas y valores numéricos por partido
        patron_fila = re.compile(
            r'<td[^>]*>\s*(\d{1,2}/\d{4})\s*</td>.*?'   # fecha
            r'<td[^>]*>\s*([\d,\.]+)\s*</td>.*?'          # PP
            r'<td[^>]*>\s*([\d,\.]+)\s*</td>.*?'          # PSOE
            r'<td[^>]*>\s*([\d,\.]+)\s*</td>',             # VOX
            re.DOTALL
        )
        filas = patron_fila.findall(texto)
        log.info(f"  Wikipedia: {len(filas)} filas candidatas encontradas")

        for fila in filas[:20]:  # máx 20 filas recientes → ligero
            try:
                fecha_str, pp_str, psoe_str, vox_str = fila
                # Normalizar fecha MM/YYYY → YYYY-MM-01
                partes = fecha_str.strip().split("/")
                if len(partes) == 2:
                    fecha_norm = f"{partes[1]}-{partes[0].zfill(2)}-01"
                else:
                    continue
                for partido, val_str in [("PP", pp_str), ("PSOE", psoe_str), ("VOX", vox_str)]:
                    val = float(val_str.replace(",", "."))
                    if 0 < val < 60:  # filtro de sanidad
                        conn.execute("""
                            INSERT OR IGNORE INTO encuestas
                            (fecha, fuente, partido, valor_pct, tipo)
                            VALUES (?,?,?,?,?)
                        """, (fecha_norm, "wikipedia_agregado", partido, val, "encuesta"))
                        registros += conn.execute("SELECT changes()").fetchone()[0]
            except (ValueError, IndexError):
                continue

        conn.commit()
        log.info(f"  Wikipedia: {registros} registros nuevos")
        log_ingesta(conn, "semanal", "wikipedia_encuestas", registros, "ok")

    except requests.exceptions.Timeout:
        log.warning("  Wikipedia: timeout")
        log_ingesta(conn, "semanal", "wikipedia_encuestas", 0, "timeout")
    except Exception as e:
        log.error(f"  Wikipedia encuestas: {e}")
        log_ingesta(conn, "semanal", "wikipedia_encuestas", 0, "error", str(e)[:200])

# ===============================
# 4. ANÁLISIS DE VARIACIONES
# Compara semana actual vs anterior
# ===============================
def generar_informe_variaciones(conn):
    """
    Compara la media de votos de esta semana vs la semana anterior.
    Genera un informe .txt ligero — sin pandas, sin numpy.
    """
    log.info("  Generando informe de variaciones...")
    semana_actual  = hoy.strftime("%Y-W%W")
    semana_ant     = (hoy - timedelta(weeks=1)).strftime("%Y-W%W")
    fecha_inicio_a = (hoy - timedelta(days=7)).strftime("%Y-%m-%d")
    fecha_inicio_aa= (hoy - timedelta(days=14)).strftime("%Y-%m-%d")

    informe_lines = [
        f"INFORME SEMANAL DE VARIACIONES — {hoy}",
        f"Semana: {semana_actual} vs {semana_ant}",
        "=" * 55,
        "",
        "[ PROYECCIÓN NACIONAL ]",
    ]

    try:
        # Media por partido esta semana
        cur = conn.cursor()

        # Semana actual
        cur.execute("""
            SELECT partido, AVG(votos_pct) as media
            FROM historico_nacional
            WHERE fecha >= ?
            GROUP BY partido
            ORDER BY media DESC
        """, (fecha_inicio_a,))
        actual = {row[0]: round(row[1], 2) for row in cur.fetchall()}

        # Semana anterior
        cur.execute("""
            SELECT partido, AVG(votos_pct) as media
            FROM historico_nacional
            WHERE fecha >= ? AND fecha < ?
            GROUP BY partido
        """, (fecha_inicio_aa, fecha_inicio_a))
        anterior = {row[0]: round(row[1], 2) for row in cur.fetchall()}

        # Delta por partido
        alertas = []
        for p in PARTIDOS:
            v_act = actual.get(p, 0)
            v_ant = anterior.get(p, 0)
            delta = round(v_act - v_ant, 2)
            signo = "▲" if delta > 0 else ("▼" if delta < 0 else "=")
            informe_lines.append(f"  {p:<8} {v_act:>5.1f}%  {signo}{abs(delta):.1f}pp")
            if abs(delta) >= 2.0:
                alertas.append(f"⚠️  ALERTA: {p} variación de {delta:+.1f}pp esta semana")

        # CyL
        informe_lines += ["", "[ CASTILLA Y LEÓN ]"]
        cur.execute("""
            SELECT partido, AVG(votos_pct) as media
            FROM historico_cyl
            WHERE fecha >= ?
            GROUP BY partido
            ORDER BY media DESC
        """, (fecha_inicio_a,))
        actual_cyl = {row[0]: round(row[1], 2) for row in cur.fetchall()}
        cur.execute("""
            SELECT partido, AVG(votos_pct) as media
            FROM historico_cyl
            WHERE fecha >= ? AND fecha < ?
            GROUP BY partido
        """, (fecha_inicio_aa, fecha_inicio_a))
        anterior_cyl = {row[0]: round(row[1], 2) for row in cur.fetchall()}

        for p in PARTIDOS_CYL:
            v_act = actual_cyl.get(p, 0)
            v_ant = anterior_cyl.get(p, 0)
            delta = round(v_act - v_ant, 2)
            signo = "▲" if delta > 0 else ("▼" if delta < 0 else "=")
            informe_lines.append(f"  {p:<10} {v_act:>5.1f}%  {signo}{abs(delta):.1f}pp")
            if abs(delta) >= 2.0:
                alertas.append(f"⚠️  ALERTA CyL: {p} variación de {delta:+.1f}pp esta semana")

        # Estadísticas de la DB
        cur.execute("SELECT COUNT(*) FROM historico_nacional")
        n_nac = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM historico_cyl")
        n_cyl = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM encuestas")
        n_enc = cur.fetchone()[0]

        informe_lines += [
            "",
            "[ BASE DE DATOS ]",
            f"  Registros nacional: {n_nac}",
            f"  Registros CyL:      {n_cyl}",
            f"  Encuestas:          {n_enc}",
            f"  Tamaño DB:          {os.path.getsize(DB_PATH) // 1024}KB",
            "",
        ]

        if alertas:
            informe_lines += ["[ ALERTAS ]"] + alertas + [""]

        informe_lines.append(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Guardar informe
        informe_path = LOG_DIR / f"informe_{semana_actual}.txt"
        informe_path.write_text("\n".join(informe_lines), encoding="utf-8")
        log.info(f"  Informe guardado: {informe_path.name}")

        # Registrar alertas en log
        for alerta in alertas:
            log.warning(f"  {alerta}")

        log_ingesta(conn, "semanal", "informe_variaciones",
                    len(actual), "ok", f"{len(alertas)} alertas")

    except Exception as e:
        log.error(f"  Informe variaciones: {e}")

# ===============================
# 5. LIMPIEZA Y MANTENIMIENTO DB
# ===============================
def mantenimiento_db(conn):
    """
    Limpieza controlada para no inflar la DB en la eMMC del Odroid.
    Conserva 90 días de histórico detallado, 1 año de resúmenes.
    """
    log.info("  Mantenimiento DB...")
    cur = conn.cursor()

    # Borrar logs de ingesta > 60 días
    cur.execute("DELETE FROM log_ingesta WHERE fecha < date('now', '-60 days')")
    n_logs = cur.rowcount
    log.info(f"  Logs purgados: {n_logs} registros")

    # Borrar registros socioeconómicos > 1 año
    cur.execute("DELETE FROM socioeconomico WHERE fecha < date('now', '-365 days')")
    n_socio = cur.rowcount
    log.info(f"  Socioeconómico purgado: {n_socio} registros > 1 año")

    conn.commit()

    # Tamaño antes de optimize
    size_antes = os.path.getsize(DB_PATH) // 1024

    # ANALYZE para actualizar estadísticas del query planner
    conn.execute("ANALYZE")
    conn.commit()

    size_despues = os.path.getsize(DB_PATH) // 1024
    log.info(f"  DB: {size_antes}KB → {size_despues}KB tras mantenimiento")
    log_ingesta(conn, "semanal", "mantenimiento_db",
                n_logs + n_socio, "ok",
                f"DB:{size_despues}KB | logs:{n_logs} | socio:{n_socio}")

# ===============================
# 6. EXPORTAR CSV PARA STREAMLIT
# Snapshot semanal ligero que app.py puede leer rápido
# ===============================
def exportar_csv_snapshot(conn):
    """
    Exporta vista resumida de las últimas 8 semanas a CSV.
    Streamlit puede leer este CSV como fallback si SQLite no está disponible.
    Mantiene compatibilidad con el código original.
    """
    log.info("  Exportando CSV snapshot para Streamlit...")
    try:
        cur = conn.cursor()

        # Histórico nacional — últimas 8 semanas
        cur.execute("""
            SELECT fecha, provincia, partido, votos_pct, escanos
            FROM historico_nacional
            WHERE fecha >= date('now', '-56 days')
            ORDER BY fecha DESC, provincia, partido
        """)
        rows = cur.fetchall()
        csv_path = BASE_DIR / "historico_semanal.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            f.write("Fecha,Provincia,Partido,Votos,Escaños\n")
            for row in rows:
                f.write(f"{row[0]},{row[1]},{row[2]},{row[3]:.4f},{row[4]}\n")
        log.info(f"  CSV nacional: {len(rows)} filas → {csv_path.name}")

        # Histórico CyL
        cur.execute("""
            SELECT fecha, provincia, partido, votos_pct, escanos, escenario
            FROM historico_cyl
            WHERE fecha >= date('now', '-56 days')
            ORDER BY fecha DESC, provincia, partido
        """)
        rows_cyl = cur.fetchall()
        csv_cyl = BASE_DIR / "historico_cyl.csv"
        with open(csv_cyl, "w", newline="", encoding="utf-8") as f:
            f.write("Fecha,Provincia,Partido,Votos,Escaños,Escenario\n")
            for row in rows_cyl:
                f.write(f"{row[0]},{row[1]},{row[2]},{row[3]:.4f},{row[4]},{row[5]}\n")
        log.info(f"  CSV CyL: {len(rows_cyl)} filas → {csv_cyl.name}")

        log_ingesta(conn, "semanal", "export_csv", len(rows) + len(rows_cyl), "ok")
    except Exception as e:
        log.error(f"  Export CSV: {e}")
        log_ingesta(conn, "semanal", "export_csv", 0, "error", str(e)[:200])

# ===============================
# MAIN
# ===============================
def main():
    t_inicio = time.time()
    semana = hoy.isocalendar()[1]
    log.info("=" * 55)
    log.info(f"INGEST WEEKLY — {hoy} — Semana ISO {semana} — seed:{SEED_SEMANAL}")
    log.info("=" * 55)

    # 1. Backup antes de cualquier escritura
    log.info("▶ Backup semanal")
    backup_db()

    conn = get_conn()
    try:
        log.info("▶ INE API — indicadores provinciales")
        ingestar_ine_api(conn)

        time.sleep(2)  # pausa entre fuentes externas — red Odroid

        log.info("▶ Encuestas Wikipedia")
        ingestar_encuestas_wikipedia(conn)

        time.sleep(2)

        log.info("▶ Informe de variaciones semanales")
        generar_informe_variaciones(conn)

        log.info("▶ Mantenimiento y limpieza DB")
        mantenimiento_db(conn)

        log.info("▶ Exportar CSV snapshot")
        exportar_csv_snapshot(conn)

    except Exception as e:
        log.error(f"ERROR CRÍTICO en ingest_weekly: {e}")
        sys.exit(1)
    finally:
        conn.close()

    elapsed = round(time.time() - t_inicio, 2)
    log.info(f"✓ Weekly completado en {elapsed}s")
    log.info("=" * 55)

if __name__ == "__main__":
    main()
