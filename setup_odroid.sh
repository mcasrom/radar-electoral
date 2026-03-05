#!/bin/bash
# setup_odroid.sh — Configuración completa para Odroid C2 / DietPi
# Ejecutar UNA sola vez como usuario dietpi:
#   chmod +x setup_odroid.sh && ./setup_odroid.sh

set -e
PROYECTO="$HOME/espana-vota-2026"
PYTHON=$(which python3)

echo "=================================================="
echo "  España Vota 2026 — Setup Odroid C2 / DietPi"
echo "=================================================="

# --- 1. Estructura de directorios
echo "[1/6] Creando estructura de directorios..."
mkdir -p "$PROYECTO/logs"
mkdir -p "$PROYECTO/backups"
mkdir -p "$PROYECTO/data"
echo "  OK: logs/, backups/, data/"

# --- 2. Dependencias Python mínimas
echo "[2/6] Instalando dependencias Python..."
pip install --quiet --no-cache-dir \
    streamlit==1.32.0 \
    pandas==2.1.4 \
    numpy==1.26.4 \
    plotly==5.18.0 \
    requests==2.31.0
echo "  OK: dependencias instaladas"

# --- 3. Inicializar DB SQLite
echo "[3/6] Inicializando base de datos SQLite..."
$PYTHON - <<'PYEOF'
import sqlite3
from pathlib import Path
DB = Path.home() / "espana-vota-2026/espana_vota.db"
conn = sqlite3.connect(str(DB))
conn.execute("PRAGMA journal_mode=WAL")
conn.executescript("""
    CREATE TABLE IF NOT EXISTS historico_nacional (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT, provincia TEXT, partido TEXT,
        votos_pct REAL, escanos INTEGER, fuente TEXT,
        UNIQUE(fecha, provincia, partido)
    );
    CREATE TABLE IF NOT EXISTS historico_cyl (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT, provincia TEXT, partido TEXT,
        votos_pct REAL, escanos INTEGER, escenario TEXT, fuente TEXT,
        UNIQUE(fecha, provincia, partido, escenario)
    );
    CREATE TABLE IF NOT EXISTS encuestas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT, fuente TEXT, partido TEXT,
        valor_pct REAL, tipo TEXT,
        UNIQUE(fecha, fuente, partido)
    );
    CREATE TABLE IF NOT EXISTS socioeconomico (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT, provincia TEXT, indicador TEXT, valor REAL,
        UNIQUE(fecha, provincia, indicador)
    );
    CREATE TABLE IF NOT EXISTS log_ingesta (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT, tipo TEXT, fuente TEXT,
        registros INTEGER, estado TEXT, mensaje TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_hn_fecha ON historico_nacional(fecha);
    CREATE INDEX IF NOT EXISTS idx_hn_partido ON historico_nacional(partido);
    CREATE INDEX IF NOT EXISTS idx_cyl_fecha ON historico_cyl(fecha);
    CREATE INDEX IF NOT EXISTS idx_enc_fecha ON encuestas(fecha);
""")
conn.commit()
conn.close()
print("  OK: espana_vota.db creada y configurada")
PYEOF

# --- 4. Migrar CSVs existentes a SQLite (si existen)
echo "[4/6] Migrando datos CSV existentes a SQLite..."
$PYTHON - <<'PYEOF'
import sqlite3, csv, os
from pathlib import Path
BASE = Path.home() / "espana-vota-2026"
DB   = BASE / "espana_vota.db"
conn = sqlite3.connect(str(DB))

# Migrar historico_semanal.csv
csv_nac = BASE / "historico_semanal.csv"
if csv_nac.exists():
    migrados = 0
    with open(csv_nac, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO historico_nacional
                    (fecha, provincia, partido, votos_pct, escanos, fuente)
                    VALUES (?,?,?,?,?,?)
                """, (row.get("Fecha",""), row.get("Provincia",""),
                      row.get("Partido",""), float(row.get("Votos",0)),
                      int(float(row.get("Escaños",0))), "csv_migrado"))
                migrados += conn.execute("SELECT changes()").fetchone()[0]
            except:
                pass
    conn.commit()
    print(f"  OK: {migrados} registros migrados desde historico_semanal.csv")
else:
    print("  INFO: No hay historico_semanal.csv que migrar")

# Migrar historico_cyl.csv
csv_cyl = BASE / "historico_cyl.csv"
if csv_cyl.exists():
    migrados = 0
    with open(csv_cyl, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO historico_cyl
                    (fecha, provincia, partido, votos_pct, escanos, escenario, fuente)
                    VALUES (?,?,?,?,?,?,?)
                """, (row.get("Fecha",""), row.get("Provincia",""),
                      row.get("Partido",""), float(row.get("Votos",0)),
                      int(float(row.get("Escaños",0))),
                      row.get("Escenario",""), "csv_migrado"))
                migrados += conn.execute("SELECT changes()").fetchone()[0]
            except:
                pass
    conn.commit()
    print(f"  OK: {migrados} registros migrados desde historico_cyl.csv")
else:
    print("  INFO: No hay historico_cyl.csv que migrar")

conn.close()
PYEOF

# --- 5. Configurar cron (SEGURO — no toca entradas existentes)
echo "[5/6] Añadiendo cron jobs sin modificar crons existentes..."

# Backup de seguridad del crontab completo actual
crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S).txt 2>/dev/null || true
echo "  Backup crontab guardado en /tmp/crontab_backup_$(date +%Y%m%d)*.txt"

# Comprobar si ya están instalados — no duplicar
if crontab -l 2>/dev/null | grep -q "espana-vota"; then
    echo "  INFO: cron jobs de espana-vota ya presentes — omitiendo"
else
    # Añadir AL FINAL del crontab existente, sin tocar nada
    (crontab -l 2>/dev/null; cat << 'CRONEOF'

# === España Vota 2026 — añadido por setup_odroid.sh ===
# Diario 06:00 — ingesta ligera
0 6 * * * /usr/bin/python3 /home/dietpi/espana-vota-2026/ingest_daily.py >> /home/dietpi/espana-vota-2026/logs/daily.log 2>&1
# Semanal Domingo 05:00 — ingesta completa + backup
0 5 * * 0 /usr/bin/python3 /home/dietpi/espana-vota-2026/ingest_weekly.py >> /home/dietpi/espana-vota-2026/logs/weekly.log 2>&1
# Salud sistema cada 6h
0 */6 * * * echo "$(date '+%Y-%m-%d %H:%M') RAM:$(free -m | awk 'NR==2{print $3}')MB DISK:$(df -h / | awk 'NR==2{print $5}')" >> /home/dietpi/espana-vota-2026/logs/salud.log 2>&1
CRONEOF
    ) | crontab -
    echo "  OK: 3 entradas añadidas al crontab existente"
fi

# Verificar resultado — solo mostrar las nuevas entradas
echo ""
echo "  Cron activo (entradas espana-vota):"
crontab -l | grep -A1 "España Vota" | grep -v "^--$"
echo ""
echo "  Crontab completo preservado:"
crontab -l | wc -l
echo "  líneas totales en crontab"


# --- 6. Servicio systemd
echo "[6/6] Configurando servicio systemd..."
sudo tee /etc/systemd/system/espana-vota.service > /dev/null << SVCEOF
[Unit]
Description=España Vota 2026 — Streamlit
After=network.target
StartLimitIntervalSec=60
StartLimitBurst=3

[Service]
Type=simple
User=dietpi
WorkingDirectory=$PROYECTO
ExecStart=$PYTHON -m streamlit run $PROYECTO/app.py \\
    --server.port 8501 \\
    --server.headless true \\
    --server.maxUploadSize 5 \\
    --server.maxMessageSize 50 \\
    --browser.gatherUsageStats false \\
    --server.enableCORS false \\
    --server.enableXsrfProtection false
Restart=on-failure
RestartSec=15
# Limitar recursos para no saturar el Odroid C2
CPUQuota=70%
MemoryMax=512M

[Install]
WantedBy=multi-user.target
SVCEOF

sudo systemctl daemon-reload
sudo systemctl enable espana-vota
sudo systemctl restart espana-vota
echo "  OK: servicio espana-vota habilitado y arrancado"

# --- Ejecución inicial de ingesta
echo ""
echo "=================================================="
echo "  Ejecutando ingesta inicial (primera vez)..."
echo "=================================================="
$PYTHON "$PROYECTO/ingest_daily.py"

# --- Resumen final
echo ""
echo "=================================================="
echo "  ✓ Setup completado"
echo "=================================================="
echo ""
echo "  App accesible en: http://$(hostname -I | awk '{print $1}'):8501"
echo ""
echo "  Comandos útiles:"
echo "  sudo systemctl status espana-vota    # estado del servicio"
echo "  sudo journalctl -u espana-vota -f    # logs en tiempo real"
echo "  tail -f $PROYECTO/logs/daily.log     # log ingesta diaria"
echo "  tail -f $PROYECTO/logs/salud.log     # métricas de sistema"
echo "  crontab -l                           # ver cron activo"
echo ""
echo "  Base de datos:"
echo "  sqlite3 $PROYECTO/espana_vota.db"
echo "  > SELECT fecha, partido, AVG(votos_pct) FROM historico_nacional GROUP BY partido;"
echo ""
