# SERGIO 2026-09-18: lectura de informacion de git de cada proyecto (feature/integracion-git)
import subprocess
from pathlib import Path


def leer_git(carpeta: str):
    """
    Si la carpeta es un repositorio git, devuelve datos del ultimo commit
    (hash corto, fecha, mensaje, rama). Si no lo es, o git falla, devuelve None.
    """
    if not carpeta:
        return None

    ruta = Path(carpeta)
    if not (ruta / ".git").exists():
        return None

    try:
        resultado = subprocess.run(
            ["git", "log", "-1", "--pretty=format:%h|%ad|%s", "--date=format:%Y-%m-%d %H:%M"],
            cwd=ruta,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (subprocess.SubprocessError, OSError):
        return None

    if resultado.returncode != 0 or not resultado.stdout.strip():
        return None

    hash_corto, fecha, mensaje = resultado.stdout.strip().split("|", 2)

    return {
        "hash": hash_corto,
        "fecha": fecha,
        "mensaje": mensaje,
        "rama": _rama_actual(ruta),
    }


def _rama_actual(ruta: Path):
    try:
        resultado = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=ruta,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if resultado.returncode == 0:
            return resultado.stdout.strip()
    except (subprocess.SubprocessError, OSError):
        pass
    return ""
