# SERGIO 2026-09-18: pruebas de la lectura de git (feature/integracion-git)
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import git_info


def _crear_repo_con_commit(ruta: Path, mensaje: str):
    subprocess.run(["git", "init"], cwd=ruta, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=ruta, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=ruta, capture_output=True, check=True)
    (ruta / "archivo.txt").write_text("contenido", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=ruta, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", mensaje], cwd=ruta, capture_output=True, check=True)


def test_leer_git_carpeta_sin_git_devuelve_none(tmp_path):
    assert git_info.leer_git(str(tmp_path)) is None


def test_leer_git_carpeta_vacia_no_revienta():
    assert git_info.leer_git("") is None


def test_leer_git_repo_con_commit(tmp_path):
    _crear_repo_con_commit(tmp_path, "mensaje de prueba")
    resultado = git_info.leer_git(str(tmp_path))
    assert resultado is not None
    assert resultado["mensaje"] == "mensaje de prueba"
    assert len(resultado["hash"]) > 0
