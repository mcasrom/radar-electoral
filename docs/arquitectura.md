# Arquitectura del Sistema

## Módulos

- ingestion.py: Lectura y validación de encuestas y provincias
- weighting.py: Cálculo de ponderación por muestra y antigüedad
- simulation.py: Monte Carlo y D’Hondt provincial
- dhondt.py: Motor D’Hondt
- indicators.py: Fragmentación, volatilidad
- narrative.py: Texto OSINT automático

## Flujo de Datos

1. Carga encuestas y provincias
2. Ponderación de datos
3. Simulación Monte Carlo
4. Reparto provincial con D’Hondt
5. Suma nacional y cálculo de indicadores
6. Visualización Streamlit (tabbed layout)
7. Generación de narrativa OSINT
