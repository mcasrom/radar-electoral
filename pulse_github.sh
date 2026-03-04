#!/bin/bash
# pulse_github.sh — Commit diario y push de votos_historicos.csv
# Para uso en ODROID con cron

# Variables
REPO_DIR="/home/dietpi/espana-vota-2026"
DATA_FILE="$REPO_DIR/data/votos_historicos.csv"
LOG_DIR="$REPO_DIR/logs"
DATE_STR=$(date '+%Y-%m-%d %H:%M:%S')
LOG_FILE="$LOG_DIR/github_$(date +%Y%m%d).log"

# Crear carpeta de logs si no existe
mkdir -p "$LOG_DIR"

# Cambiar al repo
cd "$REPO_DIR" || exit 1

# Git pull para actualizar
echo "[$DATE_STR] 🔄 Pull desde GitHub" >> "$LOG_FILE"
git pull origin main >> "$LOG_FILE" 2>&1

# Añadir archivo de datos
git add "$DATA_FILE" >> "$LOG_FILE" 2>&1

# Commit con fecha/hora
git commit -m "Actualización automática: $DATE_STR" >> "$LOG_FILE" 2>&1

# Push a GitHub
git push origin main >> "$LOG_FILE" 2>&1

echo "[$DATE_STR] ✅ Commit y push realizados" >> "$LOG_FILE"
