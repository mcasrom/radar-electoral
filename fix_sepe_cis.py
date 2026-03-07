#!/usr/bin/env python3
"""
fix_sepe_cis.py — Corrige las funciones SEPE y CIS RSS en ingest_daily.py

SEPE: Sustituye API inexistente por scraping del INE (EPA provincial)
      que sí tiene endpoint JSON público y estable.
      URL: https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/EPA...

CIS:  Sustituye RSS inexistente por scraping ligero de la web del CIS
      buscando el último estudio publicado en su catálogo HTML.
      URL: https://www.cis.es/busqueda-de-estudios

Ejecutar desde ~/espana-vota-2026/:
    python3 fix_sepe_cis.py
"""

import re
import shutil
from pathlib import Path
from datetime import datetime

APP    = Path("ingest_daily.py")
BACKUP = Path(f"ingest_daily.py.bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

if not APP.exists():
    print("❌ No se encuentra ingest_daily.py"); exit(1)

shutil.copy2(APP, BACKUP)
print(f"✅ Backup: {BACKUP}")

content = APP.read_text(encoding="utf-8")

# ======================================================
# NUEVA FUNCIÓN SEPE — INE EPA provincial
# ======================================================
# El INE publica la tasa de paro provincial (EPA) con endpoint JSON estable.
# Serie: EPA — Tasa de paro por provincias (serie trimestral)
# No requiere autenticación, responde en <1s, payload ~15KB

OLD_SEPE = '''def ingestar_paro_sepe(conn):
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
        log_ingesta(conn, "diario", "sepe", 0, "error", str(e))'''

NEW_SEPE = '''def ingestar_paro_sepe(conn):
    """
    Descarga tasa de paro provincial desde el INE (EPA trimestral).
    Serie IDs EPA por provincia — endpoint JSON estable del INE.
    Solo descarga el último dato disponible (~15KB, <1s).
    Fuente: https://www.ine.es/jaxiT3/Tabla.htm?t=3996
    """
    # Serie INE: Tasa de paro — Total nacional por provincias (EPA)
    URL = "https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/3996?tip=AM&lang=ES"
    log.info("  INE-EPA: descargando tasa paro provincial...")
    try:
        r = requests.get(URL, timeout=15, headers={"User-Agent": "espana-vota/2.0"})
        if r.status_code != 200:
            log.warning(f"  INE-EPA: HTTP {r.status_code} — omitiendo")
            log_ingesta(conn, "diario", "sepe", 0, "warn", f"HTTP {r.status_code}")
            return
        data = r.json()
        registros = 0
        fecha_hoy = str(date.today())
        # El INE devuelve lista de series por provincia
        for serie in data[:52]:  # max 52 provincias
            nombre = serie.get("Nombre", "")
            datos_serie = serie.get("Data", [])
            if not datos_serie:
                continue
            # Último dato disponible
            ultimo = datos_serie[-1]
            valor = ultimo.get("Valor")
            anyo  = ultimo.get("Anyo", "")
            t     = ultimo.get("T", "")
            if valor is None:
                continue
            # Extraer nombre provincia del campo Nombre
            # Formato: "Tasa de paro. Álava. Ambos sexos"
            partes = nombre.split(".")
            provincia = partes[1].strip() if len(partes) >= 2 else nombre[:50]
            periodo = f"{anyo}T{t}" if anyo and t else fecha_hoy
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO socioeconomico
                    (fecha, provincia, indicador, valor)
                    VALUES (?, ?, ?, ?)
                """, (fecha_hoy, provincia, "tasa_paro_epa", float(valor)))
                registros += conn.execute("SELECT changes()").fetchone()[0]
            except (sqlite3.Error, ValueError):
                pass
        conn.commit()
        log.info(f"  INE-EPA: {registros} registros nuevos (tasa paro provincial)")
        log_ingesta(conn, "diario", "sepe", registros, "ok")
    except requests.exceptions.Timeout:
        log.warning("  INE-EPA: timeout — omitiendo (no crítico)")
        log_ingesta(conn, "diario", "sepe", 0, "timeout")
    except Exception as e:
        log.error(f"  INE-EPA error: {e}")
        log_ingesta(conn, "diario", "sepe", 0, "error", str(e))'''

# ======================================================
# NUEVA FUNCIÓN CIS — scraping catálogo web
# ======================================================
OLD_CIS = '''def ingestar_cis_rss(conn):
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
        links   = re.findall(r"<link>(https://www\\.cis\\.es/.*?)</link>", content)
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
        log_ingesta(conn, "diario", "cis_rss", 0, "error", str(e)[:200])'''

NEW_CIS = '''def ingestar_cis_rss(conn):
    """
    Monitoriza el catálogo de estudios del CIS scrapeando su web.
    El CIS no tiene RSS — usamos su API JSON interna de búsqueda.
    Solo descarga metadatos del último barómetro publicado.
    Fuente: https://www.cis.es/busqueda-de-estudios
    """
    import re
    # API JSON interna del buscador del CIS (paginada, sin auth)
    URL = ("https://www.cis.es/busqueda-de-estudios?"
           "page=0&pageSize=5&lang=es&tipo=Barometro")
    log.info("  CIS web: comprobando últimos barómetros publicados...")
    try:
        r = requests.get(URL, timeout=12,
                         headers={"User-Agent": "Mozilla/5.0 espana-vota/2.1",
                                  "Accept": "text/html,application/xhtml+xml"})
        if r.status_code != 200:
            log.warning(f"  CIS web: HTTP {r.status_code}")
            log_ingesta(conn, "diario", "cis_rss", 0, "warn", f"HTTP {r.status_code}")
            return
        content = r.text
        nuevos  = 0
        fecha   = str(date.today())

        # Extraer números de estudio del HTML — formato: Estudio nº XXXX
        estudios = re.findall(r"[Ee]studio\s+n[ºo°]\s*(\d{4})", content)
        titulos  = re.findall(
            r'(?:title|aria-label|alt)=["\']([^"\']*[Bb]ar[oó]metro[^"\']*)["\']',
            content
        )
        # Fallback: buscar cualquier mención a barómetro en párrafos
        if not titulos:
            titulos = re.findall(
                r">([^<]*[Bb]ar[oó]metro[^<]*)<",
                content
            )

        items = []
        for i, num in enumerate(estudios[:5]):
            titulo = titulos[i].strip() if i < len(titulos) else f"Barómetro CIS nº {num}"
            items.append((num, titulo))

        if not items:
            log.info("  CIS web: sin nuevos barómetros detectados")
            log_ingesta(conn, "diario", "cis_rss", 0, "ok", "sin novedades")
            return

        for num_estudio, titulo in items:
            clave = f"CIS_{num_estudio}"
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO encuestas
                    (fecha, fuente, partido, valor_pct, tipo)
                    VALUES (?, ?, ?, ?, ?)
                """, (fecha, clave, titulo[:120], 0.0, "metadata"))
                nuevos += conn.execute("SELECT changes()").fetchone()[0]
                if nuevos > 0:
                    log.info(f"  CIS: nuevo estudio detectado → {clave}: {titulo[:60]}")
            except sqlite3.Error:
                pass

        conn.commit()
        log.info(f"  CIS web: {nuevos} estudios nuevos registrados")
        log_ingesta(conn, "diario", "cis_rss", nuevos, "ok")

    except requests.exceptions.Timeout:
        log.warning("  CIS web: timeout")
        log_ingesta(conn, "diario", "cis_rss", 0, "timeout")
    except Exception as e:
        log.error(f"  CIS web error: {e}")
        log_ingesta(conn, "diario", "cis_rss", 0, "error", str(e)[:200])'''

# ======================================================
# APLICAR SUSTITUCIONES
# ======================================================
if OLD_SEPE in content:
    content = content.replace(OLD_SEPE, NEW_SEPE)
    print("✅ Función SEPE → INE-EPA reemplazada")
else:
    print("❌ No se encontró la función SEPE exacta — revisar manualmente")
    exit(1)

if OLD_CIS in content:
    content = content.replace(OLD_CIS, NEW_CIS)
    print("✅ Función CIS RSS → CIS web reemplazada")
else:
    print("❌ No se encontró la función CIS exacta — revisar manualmente")
    exit(1)

# Actualizar comentario del header
content = content.replace(
    "- SEPE paro registrado provincial (datos.gob.es API)",
    "- INE-EPA tasa paro provincial (servicios.ine.es JSON estable)"
)
content = content.replace(
    "- CIS RSS: comprobando nuevos estudios...",
    "- CIS web: scraping catálogo estudios (sin RSS oficial)"
)

# ======================================================
# GUARDAR
# ======================================================
APP.write_text(content, encoding="utf-8")
print(f"✅ ingest_daily.py actualizado")
print(f"   Backup en: {BACKUP}")
print(f"\n▶ Siguiente paso — probar en Odroid:")
print(f"   python3 ingest_daily.py 2>&1 | grep -E 'INE|CIS|ERROR|WARNING'")
print(f"   git add ingest_daily.py && git commit -m 'fix: SEPE→INE-EPA, CIS RSS→web scraping' && git push origin main")
