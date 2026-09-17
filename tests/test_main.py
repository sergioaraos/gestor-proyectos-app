# SERGIO 2026-09-17: pruebas del listado y del alta de proyectos (feature/alta-proyectos)
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Usa una base de datos temporal para no tocar la base real durante las pruebas
    import database
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    import main
    with TestClient(main.app) as c:
        yield c


def test_listado_carga(client):
    # La pagina principal debe responder 200 aunque la base este vacia
    response = client.get("/")
    assert response.status_code == 200


def test_formulario_alta_se_muestra(client):
    # El formulario de alta debe estar disponible
    response = client.get("/nuevo")
    assert response.status_code == 200
    assert "Nombre" in response.text


def test_crear_proyecto_lo_agrega_al_listado(client):
    # Crear un proyecto por POST debe redirigir y luego aparecer en el listado
    response = client.post(
        "/nuevo",
        data={
            "nombre": "Proyecto de prueba",
            "cliente": "Cliente de prueba",
            "prioridad": "alta",
            "carpeta": r"C:\laragon\www\proyecto-prueba",
            "herramienta": "Cowork",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Proyecto de prueba" in response.text
