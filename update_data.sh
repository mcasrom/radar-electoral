#!/bin/bash
# Actualización semanal – backup y log
set -e
cd /home/dietpi/espana-vota-2026

# Crear carpeta de logs si no existe
mkdir -p logs

# Backup histórico
cp historico_semanal.csv historico_semanal_$(date '+%Y%m%d').bak

# Ejecutar actualización de datos
python3 update_data.py >> logs/update.log 2>&1
