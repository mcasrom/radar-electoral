#!/bin/bash
# Script para cron en ODROID-C2
REPO_DIR="/home/$(whoami)/espana-vota-2026"
cd $REPO_DIR

# Sincronizar cambios
git add .
git commit -m "Update Semanal: $(date +'%Y-%m-%d %H:%M')"
git push origin main
