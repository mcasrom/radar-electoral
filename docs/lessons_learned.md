# 📚 Lecciones Aprendidas — España Vota 2026
**Modelo electoral autonómico · Autor: M. Castillo**  
*Documento vivo — se actualiza al cerrar cada laboratorio*

---

## Historial de laboratorios

| Comunidad | Fecha elección | RMSE | MAE | Bias | Estado |
|-----------|---------------|------|-----|------|--------|
| Castilla y León | 15-Mar-2026 | 1.87 | 1.50 | -0.13 | ✅ Cerrado |
| Andalucía | ~2027 | — | — | — | 🔄 En curso |
| Galicia | — | — | — | — | 🔄 Abierto |
| Madrid | — | — | — | — | 🔄 Abierto |
| Euskadi | — | — | — | — | 🔄 Abierto |

---

## 🏰 Castilla y León — 15 de marzo de 2026

### Resultados vs Predicción

| Partido | Predicción | Real | Error |
|---------|-----------|------|-------|
| PP | 33 | 33 | 0 |
| PSOE | 27 | 30 | **+3** |
| VOX | 17 | 14 | **-3** |
| UPL | 3 | 3 | 0 |
| Por Ávila | 1 | 1 | 0 |
| Soria ¡Ya! | 1 | 1 | 0 |
| SUMAR | 1 | 0 | -1 |
| OTROS | 5 | 0 | -5 |

### ✅ Aciertos
- **PP exacto (33/33):** el modelo captura bien el voto conservador rural envejecido
- **Partidos localistas correctos:** UPL, Por Ávila y Soria ¡Ya! en línea
- **Desaparición de fragmentación izquierda:** confirmada, aunque subestimamos velocidad

### ⚠️ Fallos y causas raíz

**1. PSOE infraestimado (+3 escaños)**
- Causa: no modelamos el efecto "voto útil" cuando VOX supera el 15%
- La amenaza VOX moviliza al votante socialista hesitante hacia PSOE
- El modelo trataba PSOE como constante estructural, sin este mecanismo dinámico

**2. VOX sobreestimado (-3 escaños)**
- Causa: las encuestas de SocioMétrica y Gesop tienen sesgo sistemático +2-3 pts en CyL
- El modelo heredó ese sesgo directamente de BASE_CYL sin corrección
- VOX tiene techo real más bajo en electorado rural envejecido de lo que miden las encuestas

**3. OTROS muy sobreestimado (-5 escaños)**
- Causa: agregamos Cs, IU, Podemos y residuales en un único bucket
- Cs desapareció más rápido de lo esperado (ningún escaño)
- IU/Podemos absorbidos por SUMAR, que también cayó a 0
- Soria ¡Ya! tiene dinámica completamente independiente

### 🔧 Correcciones aplicadas al modelo

Factores derivados automáticamente por `model_memory.py`:

| Partido | Factor corrección | Aplicación |
|---------|-----------------|-----------|
| PSOE | +1.5 escaños | Cuando VOX >15% en encuestas → añadir factor voto útil |
| VOX | -1.5 escaños | Corrección sesgo encuestador en CyL y comunidades similares |
| OTROS | -2.5 escaños | Desagregar siempre; no usar bucket residual >5% |

### 📋 Mejoras técnicas implementadas

1. **`model_memory.py`:** módulo central de memoria persistente entre labs
2. **Corrección sesgo VOX:** `BASE_AND["VOX"]` ajustado según perfil sociológico AND vs CyL
3. **Factor voto útil PSOE:** añadido en `ajustar_escenario_and()` cuando VOX >12%
4. **Desagregación OTROS:** separados Cs (liquidación), SUMAR/Por Andalucía, residuales
5. **Tab Historial:** visualización comparada de todos los labs en la app

---

## 🌞 Andalucía — Próximas elecciones (~2027)

### Contexto de partida
- Elecciones 2022: PP 58 / PSOE 30 / VOX 14 / Por Andalucía 5 / Cs 2
- PP con mayoría absoluta histórica bajo Moreno Bonilla
- VOX en retroceso respecto a máximos; Por Andalucía estabilizada

### Correcciones CyL aplicadas al modelo AND

**Sesgo VOX:** reducido `BASE_AND["VOX"]` de 10.5% a 9.0%  
→ VOX en AND tiene perfil distinto (más urbano-costera que rural-interior)  
→ aun así aplicamos -1 pt como corrección conservadora

**Voto útil PSOE:** añadido factor dinámico en `ajustar_escenario_and()`  
→ si VOX simulado > 12% → PSOE +0.8 pts por transferencia de voto útil

**OTROS desagregado:** Cs eliminado (0 escaños esperados), residual reducido a 5%

### Variables críticas AND (no presentes en CyL)
- Desempleo estructural (AND ~17% vs CyL ~9%): mayor sensibilidad PSOE/Por AND
- Turismo y vivienda costera: Málaga, Cádiz, Almería con dinámica propia
- Agua y sequía: movilizador rural PP+VOX en Almería, Jaén, Córdoba
- Peso de Por Andalucía (IU histórica): más fuerte que SUMAR en CyL

---

## 🗺️ Roadmap del modelo

### Corto plazo (antes de AND)
- [x] Implementar `model_memory.py`
- [x] Aplicar correcciones CyL → AND
- [x] Tab historial en app
- [ ] Añadir encuestas AND reales cuando estén disponibles
- [ ] Calibrar factor voto útil con datos históricos AND 2018-2022

### Medio plazo
- [ ] Laboratorio Galicia (cierre pendiente — ya hay resultado 2024)
- [ ] Laboratorio Madrid (elecciones ~2027)
- [ ] Modelo ensemble: combinar estructural + encuestas + correcciones históricas
- [ ] Intervalo de confianza por partido (±N escaños al 80%)

### Largo plazo
- [ ] API de encuestas en tiempo real (ElectoPanel, KeyData)
- [ ] Backtesting automático contra resultados históricos 2015-2026
- [ ] Exportar factores de corrección a CSV para análisis externo

---

*Última actualización: 2026-03-16 · España Vota 2026 · © M. Castillo*
