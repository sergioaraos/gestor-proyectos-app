# SERGIO 2026-09-18: pruebas del alta y listado de clientes (feature/tabla-clientes)
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


def test_listado_clientes_carga(client):
    response = client.get("/clientes")
    assert response.status_code == 200


def test_crear_cliente_lo_agrega_al_listado(client):
    response = client.post("/clientes", data={"nombre": "Cliente Nuevo"}, follow_redirects=True)
    assert response.status_code == 200
    assert "Cliente Nuevo" in response.text


def test_crear_cliente_duplicado_no_revienta(client):
    # El nombre es UNIQUE en la tabla: cargar el mismo cliente dos veces no debe fallar
    # ni duplicarlo en el listado
    client.post("/clientes", data={"nombre": "Cliente Repetido"})
    response = client.post("/clientes", data={"nombre": "Cliente Repetido"}, follow_redirects=True)
    assert response.status_code == 200
    assert response.text.count("Cliente Repetido") == 1


def test_formulario_alta_proyecto_muestra_clientes_en_el_select(client):
    client.post("/clientes", data={"nombre": "Cliente Para Elegir"})
    response = client.get("/nuevo")
    assert response.status_code == 200
    assert "Cliente Para Elegir" in response.text


# SERGIO 2026-09-18: pruebas de editar y eliminar clientes (feature/tabla-clientes)
def test_editar_cliente_le_cambia_el_nombre(client):
    import database

    client.post("/clientes", data={"nombre": "Cliente Original"})
    conn = database.get_connection()
    fila = conn.execute("SELECT id FROM clientes WHERE nombre = ?", ("Cliente Original",)).fetchone()
    conn.close()

    response = client.post(
        f"/clientes/{fila['id']}/editar", data={"nombre": "Cliente Renombrado"}, follow_redirects=True
    )

    assert response.status_code == 200
    assert "Cliente Renombrado" in response.text
    assert "Cliente Original" not in response.text


def test_editar_cliente_actualiza_los_proyectos_que_lo_tenian_asignado(client):
    import database

    client.post("/clientes", data={"nombre": "Cliente Con Proyecto"})
    client.post(
        "/nuevo",
        data={
            "nombre": "Proyecto del cliente",
            "cliente": "Cliente Con Proyecto",
            "prioridad": "media",
            "carpeta_nombre": "proyecto-del-cliente",
            "herramienta": "Cowork",
        },
    )

    conn = database.get_connection()
    fila_cliente = conn.execute(
        "SELECT id FROM clientes WHERE nombre = ?", ("Cliente Con Proyecto",)
    ).fetchone()
    conn.close()

    client.post(f"/clientes/{fila_cliente['id']}/editar", data={"nombre": "Cliente Renombrado 2"})

    conn = database.get_connection()
    fila_proyecto = conn.execute(
        "SELECT cliente FROM projects WHERE nombre = ?", ("Proyecto del cliente",)
    ).fetchone()
    conn.close()

    assert fila_proyecto["cliente"] == "Cliente Renombrado 2"


def test_editar_cliente_a_nombre_duplicado_no_revienta(client):
    import database

    client.post("/clientes", data={"nombre": "Cliente Uno"})
    client.post("/clientes", data={"nombre": "Cliente Dos"})
    conn = database.get_connection()
    fila = conn.execute("SELECT id FROM clientes WHERE nombre = ?", ("Cliente Dos",)).fetchone()
    conn.close()

    response = client.post(
        f"/clientes/{fila['id']}/editar", data={"nombre": "Cliente Uno"}, follow_redirects=True
    )

    assert response.status_code == 200
    # Sigue habiendo un "Cliente Uno" y un "Cliente Dos", no se fusionaron ni rompio nada
    assert "Cliente Uno" in response.text
    assert "Cliente Dos" in response.text


def test_eliminar_cliente_lo_saca_del_listado(client):
    import database

    client.post("/clientes", data={"nombre": "Cliente A Borrar"})
    conn = database.get_connection()
    fila = conn.execute("SELECT id FROM clientes WHERE nombre = ?", ("Cliente A Borrar",)).fetchone()
    conn.close()

    response = client.post(f"/clientes/{fila['id']}/eliminar", follow_redirects=True)

    assert response.status_code == 200
    assert "Cliente A Borrar" not in response.text


def test_eliminar_cliente_no_afecta_los_proyectos_existentes(client):
    import database

    client.post("/clientes", data={"nombre": "Cliente A Borrar 2"})
    client.post(
        "/nuevo",
        data={
            "nombre": "Proyecto que se queda",
            "cliente": "Cliente A Borrar 2",
            "prioridad": "media",
            "carpeta_nombre": "proyecto-que-se-queda",
            "herramienta": "Cowork",
        },
    )

    conn = database.get_connection()
    fila_cliente = conn.execute(
        "SELECT id FROM clientes WHERE nombre = ?", ("Cliente A Borrar 2",)
    ).fetchone()
    conn.close()

    client.post(f"/clientes/{fila_cliente['id']}/eliminar")

    conn = database.get_connection()
    fila_proyecto = conn.execute(
        "SELECT cliente FROM projects WHERE nombre = ?", ("Proyecto que se queda",)
    ).fetchone()
    conn.close()

    assert fila_proyecto["cliente"] == "Cliente A Borrar 2"
