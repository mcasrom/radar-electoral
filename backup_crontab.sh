#!/bin/bash
# backup_crontab.sh — Backup rotativo del crontab completo
# Mantiene 30 días de histórico

BACKUP_DIR="/home/dietpi/espana-vota-2026/crontab_backups"
mkdir -p "$BACKUP_DIR"

# Guardar crontab con timestamp
FECHA=$(date +%Y%m%d_%H%M%S)
crontab -l > "$BACKUP_DIR/crontab_$FECHA.txt"

# Verificar que no está vacío — alarma si lo está
LINEAS=$(wc -l < "$BACKUP_DIR/crontab_$FECHA.txt")
if [ "$LINEAS" -lt 5 ]; then
    echo "⚠️  ALERTA: crontab sospechosamente corto ($LINEAS líneas) — $(date)" >> "$BACKUP_DIR/alerta_crontab.log"
fi

# Rotación — mantener solo últimos 30 backups
ls -t "$BACKUP_DIR"/crontab_*.txt | tail -n +31 | xargs rm -f 2>/dev/null

echo "$(date '+%Y-%m-%d %H:%M') backup OK — $LINEAS líneas" >> "$BACKUP_DIR/backup_crontab.log"
