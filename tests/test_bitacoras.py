# SERGIO 2026-09-17: pruebas del parser de bitacoras (feature/lectura-bitacoras)
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

import bitacoras

CONTENIDO_EJEMPLO = """# Bitacora - Proyecto de prueba

Instrucciones para la herramienta que trabaje en este proyecto...

---

## 2026-09-10 10:00 — Claude Code
Estado: en progreso
Resumen: primera entrada de prueba.
Pendientes: nada por ahora.

## 2026-09-17 22:30 — Cowork
Estado: terminado
Resumen: segunda entrada de prueba, esta es la mas reciente.
Pendientes: ninguno.
"""


def test_leer_bitacora_inexistente_devuelve_none(tmp_path):
    resultado = bitacoras.leer_bitacora(str(tmp_path))
    assert resultado is None


def test_leer_bitacora_carpeta_vacia_no_revienta():
    resultado = bitacoras.leer_bitacora("")
    assert resultado is None


def test_leer_bitacora_toma_la_ultima_entrada(tmp_path):
    (tmp_path / "BITACORA.md").write_text(CONTENIDO_EJEMPLO, encoding="utf-8")
    resultado = bitacoras.leer_bitacora(str(tmp_path))
    assert resultado is not None
    assert resultado["ultima_entrada"]["estado"] == "terminado"
    assert "segunda entrada" in resultado["ultima_entrada"]["resumen"]
