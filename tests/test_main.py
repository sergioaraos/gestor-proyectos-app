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


# SERGIO 2026-09-17: prueba del detalle de proyecto (feature/lectura-bitacoras)
def test_detalle_proyecto_muestra_bitacora(client, tmp_path):
    import database

    carpeta_proyecto = tmp_path / "proyecto_con_bitacora"
    carpeta_proyecto.mkdir()
    (carpeta_proyecto / "BITACORA.md").write_text(
        "## 2026-09-17 10:00 — Cowork\n"
        "Estado: en progreso\n"
        "Resumen: prueba de deteccion de bitacora.\n"
        "Pendientes: ninguno.\n",
        encoding="utf-8",
    )

    client.post(
        "/nuevo",
        data={
            "nombre": "Proyecto con bitacora",
            "cliente": "Cliente test",
            "prioridad": "alta",
            "carpeta": str(carpeta_proyecto),
            "herramienta": "Cowork",
        },
    )

    conn = database.get_connection()
    fila = conn.execute(
        "SELECT id FROM projects WHERE nombre = ?", ("Proyecto con bitacora",)
    ).fetchone()
    conn.close()

    response = client.get(f"/proyecto/{fila['id']}")
    assert response.status_code == 200
    assert "prueba de deteccion de bitacora" in response.text


def test_detalle_proyecto_inexistente_devuelve_404(client):
    response = client.get("/proyecto/9999")
    assert response.status_code == 404
