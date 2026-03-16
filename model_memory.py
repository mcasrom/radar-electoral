#!/usr/bin/env python3
# model_memory.py
# Memoria del modelo electoral — España Vota 2026
# Almacena predicciones, resultados reales, sesgos y factores de corrección
# por laboratorio. Reutilizable entre módulos.
# Autor: M. Castillo · mybloggingnotes@gmail.com

import json
import math
import os
from datetime import datetime

MEMORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model_memory.json")


# ── Estructura de un laboratorio cerrado ─────────────────────────────────────
def _lab_vacio():
    return {
        "comunidad":      "",
        "fecha_eleccion": "",
        "fecha_cierre":   "",
        "total_escanos":  0,
        "prediccion":     {},   # {partido: escaños}
        "resultado_real": {},   # {partido: escaños}
        "metricas":       {},   # rmse, mae, sesgo_vox, sesgo_psoe...
        "correcciones":   {},   # factores de ajuste derivados
        "lecciones":      [],   # lista de strings
        "cerrado":        False,
    }


# ── Persistencia ─────────────────────────────────────────────────────────────
def cargar_memoria() -> dict:
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def guardar_memoria(memoria: dict):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memoria, f, indent=2, ensure_ascii=False)


# ── Cálculo de métricas ───────────────────────────────────────────────────────
def calcular_metricas(prediccion: dict, resultado: dict) -> dict:
    partidos = set(prediccion) | set(resultado)
    errores = []
    detalle = {}
    for p in partidos:
        pred = prediccion.get(p, 0)
        real = resultado.get(p, 0)
        err  = real - pred
        detalle[p] = {"pred": pred, "real": real, "error": err}
        errores.append(err)

    n    = len(errores)
    rmse = math.sqrt(sum(e**2 for e in errores) / n) if n else 0
    mae  = sum(abs(e) for e in errores) / n if n else 0
    bias = sum(errores) / n if n else 0   # + = infraestimación sistemática

    return {
        "rmse":    round(rmse, 2),
        "mae":     round(mae, 2),
        "bias":    round(bias, 2),
        "detalle": detalle,
    }


# ── Derivar factores de corrección ────────────────────────────────────────────
def derivar_correcciones(metricas: dict) -> dict:
    """
    A partir de los errores por partido, genera factores de corrección
    para aplicar en el siguiente laboratorio.
    """
    correcciones = {}
    detalle = metricas.get("detalle", {})
    for partido, d in detalle.items():
        error = d["error"]
        # Factor de corrección = mitad del error observado (corrección conservadora)
        if abs(error) >= 2:
            correcciones[partido] = round(error * 0.5, 1)
    return correcciones


# ── API pública ───────────────────────────────────────────────────────────────
def registrar_laboratorio(
    clave: str,           # ej: "cyl_2026", "and_2027"
    comunidad: str,
    fecha_eleccion: str,
    total_escanos: int,
    prediccion: dict,
    resultado_real: dict,
    lecciones: list,
):
    """Registra un laboratorio cerrado con sus métricas calculadas."""
    memoria = cargar_memoria()
    lab = _lab_vacio()
    lab["comunidad"]      = comunidad
    lab["fecha_eleccion"] = fecha_eleccion
    lab["fecha_cierre"]   = datetime.now().strftime("%Y-%m-%d")
    lab["total_escanos"]  = total_escanos
    lab["prediccion"]     = prediccion
    lab["resultado_real"] = resultado_real
    lab["metricas"]       = calcular_metricas(prediccion, resultado_real)
    lab["correcciones"]   = derivar_correcciones(lab["metricas"])
    lab["lecciones"]      = lecciones
    lab["cerrado"]        = True
    memoria[clave]        = lab
    guardar_memoria(memoria)
    return lab


def obtener_correcciones(clave: str) -> dict:
    """Devuelve los factores de corrección de un laboratorio cerrado."""
    memoria = cargar_memoria()
    lab = memoria.get(clave, {})
    return lab.get("correcciones", {})


def obtener_todos_labs() -> dict:
    """Devuelve todos los laboratorios registrados."""
    return cargar_memoria()


def resumen_labs() -> list:
    """Lista resumida de labs para mostrar en tabla."""
    memoria = cargar_memoria()
    filas = []
    for clave, lab in memoria.items():
        m = lab.get("metricas", {})
        filas.append({
            "Clave":          clave,
            "Comunidad":      lab.get("comunidad", ""),
            "Fecha":          lab.get("fecha_eleccion", ""),
            "Escaños":        lab.get("total_escanos", 0),
            "RMSE":           m.get("rmse", "-"),
            "MAE":            m.get("mae", "-"),
            "Bias":           m.get("bias", "-"),
            "Cerrado":        "✅" if lab.get("cerrado") else "🔄",
        })
    return filas


# ── Registro inicial: CyL 2026 ────────────────────────────────────────────────
CYL_2026_PREDICCION = {
    "PP": 33, "PSOE": 27, "VOX": 17, "UPL": 3,
    "Por Ávila": 1, "Soria ¡Ya!": 1, "SUMAR": 1, "OTROS": 5,
}
CYL_2026_RESULTADO = {
    "PP": 33, "PSOE": 30, "VOX": 14, "UPL": 3,
    "Por Ávila": 1, "Soria ¡Ya!": 1, "SUMAR": 0, "OTROS": 0,
}
CYL_2026_LECCIONES = [
    "El modelo captura bien el voto conservador rural (PP exacto)",
    "PSOE infraestimado +3: subestimamos movilización urbana y voto útil anti-VOX",
    "VOX sobreestimado -3: encuestas SocioMétrica tienen sesgo +2-3 en CyL",
    "OTROS sobreestimado: Cs/Podemos desaparecen más rápido de lo modelado",
    "Aplicar corrección sesgo VOX (-0.75 esc/prov grande) en próximo laboratorio",
    "Modelar explícitamente voto útil PSOE cuando VOX >15% en encuestas",
    "Desagregar Soria ¡Ya! de OTROS — tiene dinámica propia e impredecible",
]


def inicializar_cyl_2026():
    """Registra CyL 2026 si no existe ya en memoria."""
    memoria = cargar_memoria()
    if "cyl_2026" not in memoria:
        registrar_laboratorio(
            clave="cyl_2026",
            comunidad="Castilla y León",
            fecha_eleccion="2026-03-15",
            total_escanos=82,
            prediccion=CYL_2026_PREDICCION,
            resultado_real=CYL_2026_RESULTADO,
            lecciones=CYL_2026_LECCIONES,
        )


if __name__ == "__main__":
    inicializar_cyl_2026()
    labs = resumen_labs()
    print("\n=== Memoria del Modelo ===")
    for l in labs:
        print(f"  {l['Clave']:15} | {l['Comunidad']:20} | {l['Fecha']} | RMSE={l['RMSE']} | MAE={l['MAE']} | Bias={l['Bias']}")
    correcciones = obtener_correcciones("cyl_2026")
    print(f"\n=== Correcciones derivadas para siguiente lab ===")
    for p, c in correcciones.items():
        print(f"  {p:15}: {c:+.1f} escaños")
