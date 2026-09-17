# SERGIO 2026-09-17: lectura y parseo de BITACORA.md de cada proyecto (feature/lectura-bitacoras)
import re
from pathlib import Path


def leer_bitacora(carpeta: str):
    """
    Busca BITACORA.md en la carpeta del proyecto y devuelve un diccionario
    con el contenido completo y los datos de la ultima entrada.
    Si la carpeta esta vacia o el archivo no existe, devuelve None.
    """
    if not carpeta:
        return None

    ruta = Path(carpeta) / "BITACORA.md"
    if not ruta.exists():
        return None

    contenido = ruta.read_text(encoding="utf-8")
    entradas = _separar_entradas(contenido)

    ultima_entrada = _parsear_entrada(entradas[-1]) if entradas else None

    return {
        "contenido_completo": contenido,
        "ultima_entrada": ultima_entrada,
    }


def _separar_entradas(contenido: str):
    # Cada entrada empieza con "## " seguido de una fecha AAAA-MM-DD
    # El primer bloque del archivo (instrucciones) no cuenta como entrada
    bloques = re.split(r"\n(?=## \d{4}-\d{2}-\d{2})", contenido)
    return [b.strip() for b in bloques if re.match(r"## \d{4}-\d{2}-\d{2}", b.strip())]


def _parsear_entrada(bloque: str):
    titulo = re.match(r"## (.+)", bloque)
    fecha_herramienta = titulo.group(1).strip() if titulo else ""

    def campo(nombre):
        m = re.search(rf"{nombre}:\s*(.+)", bloque)
        return m.group(1).strip() if m else ""

    return {
        "fecha_herramienta": fecha_herramienta,
        "estado": campo("Estado"),
        "resumen": campo("Resumen"),
        "pendientes": campo("Pendientes"),
    }
