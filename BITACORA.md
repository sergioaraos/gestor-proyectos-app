# Bitácora — gestor-proyectos-app

Instrucciones para la herramienta que trabaje en este proyecto: antes de empezar, revisa la última entrada para saber en qué se quedó. Al terminar una sesión de trabajo con cambios relevantes, agrega una entrada nueva al final de este archivo (no edites entradas anteriores) con este formato exacto:

## AAAA-MM-DD HH:MM — <herramienta>
Estado: <en progreso | bloqueado | terminado>
Resumen: <2 a 4 líneas de qué se hizo>
Archivos/carpetas tocados: <lista breve>
Recursos/URLs/config: <si aplica, si no, omitir la línea>
Pendientes: <qué queda para la próxima sesión>

---

## 2026-09-17 20:00 — Cowork
Estado: en progreso
Resumen: primer esqueleto funcional. FastAPI + SQLite, muestra una tabla con los proyectos registrados (TecnoRegistros y este mismo proyecto precargados). Sin mapa de actividad ni resúmenes con Ollama todavía.
Archivos/carpetas tocados: main.py, database.py, templates/index.html, requirements.txt
Pendientes: agregar formulario para crear proyectos, lectura de bitácoras de cada proyecto, integración con git log, y generación de resumen vía Ollama.