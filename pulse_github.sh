#!/bin/bash
# --- CONFIGURACIÓN PARA USUARIO DIETPI ---
REPO_DIR="/home/dietpi/espana-vota-2026"
LOG_PULSE="$REPO_DIR/pulse.log"
LOG_ERROR="$REPO_DIR/error_sync.log"
MAX_LOG_SIZE=2000

cd $REPO_DIR || exit 1

# --- FUNCIÓN DE ROTACIÓN ---
rotate_logs() {
    if [ -f "$LOG_ERROR" ]; then
        SIZE=$(du -k "$LOG_ERROR" | cut -f1)
        if [ $SIZE -gt $MAX_LOG_SIZE ]; then
            mv "$LOG_ERROR" "${LOG_ERROR}.old"
            touch "$LOG_ERROR"
        fi
    fi
    if [ -f "$LOG_PULSE" ]; then
        tail -n 30 "$LOG_PULSE" > "${LOG_PULSE}.tmp" && mv "${LOG_PULSE}.tmp" "$LOG_PULSE"
    fi
}

# --- EJECUCIÓN ---
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

{
    echo "--- Inicio Sincronización Dietpi: $TIMESTAMP ---"
    rotate_logs
    
    # Git Add de componentes críticos
    git add pulse.log app.py README.md data/provincias.json .gitignore
    
    if ! git diff-index --quiet HEAD --; then
        echo "$TIMESTAMP - Pulso OSINT activo." >> "$LOG_PULSE"
        git commit -m "Radar Sync (Dietpi): $TIMESTAMP"
        
        if git push origin main; then
            echo "ÉXITO: Sincronización con GitHub completada."
        else
            echo "ERROR: Fallo de conexión o credenciales en Git push." >&2
            exit 1
        fi
    else
        echo "INFO: Sin cambios detectados en el radar."
    fi
} >> "$LOG_ERROR" 2>&1
