#!/bin/bash

REPO="/home/dietpi/espana-vota-2026"
LOG="$REPO/logs/github_$(date +%Y%m%d).log"

cd "$REPO" || exit 1

echo "----- $(date) -----" >> "$LOG"

git add -A >> "$LOG" 2>&1

if git diff --cached --quiet; then
    echo "No hay cambios para subir" >> "$LOG"
else
    git commit -m "Auto pulse $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG" 2>&1
    git push origin main >> "$LOG" 2>&1
    echo "Push realizado correctamente" >> "$LOG"
fi
