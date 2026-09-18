# SERGIO 2026-09-18: pruebas de las migraciones de la base de datos (feature/tabla-clientes)
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import database


def test_init_db_migra_los_clientes_ya_escritos_en_proyectos(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")

    # Se simula una base ya existente, con un proyecto que tiene un cliente escrito a
    # mano antes de que existiera la tabla de clientes
    database.init_db()
    conn = database.get_connection()
    conn.execute(
        "INSERT INTO projects (nombre, cliente, prioridad, estado, fecha_inicio) VALUES (?, ?, ?, ?, date('now'))",
        ("Proyecto viejo", "Cliente Historico", "media", "activo"),
    )
    conn.commit()
    conn.close()

    # init_db se vuelve a llamar, como pasaria al reiniciar la app, y deberia migrar el cliente
    database.init_db()

    conn = database.get_connection()
    fila = conn.execute("SELECT nombre FROM clientes WHERE nombre = ?", ("Cliente Historico",)).fetchone()
    conn.close()

    assert fila is not None


def test_init_db_no_migra_proyectos_sin_cliente(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")

    database.init_db()
    conn = database.get_connection()
    conn.execute(
        "INSERT INTO projects (nombre, cliente, prioridad, estado, fecha_inicio) VALUES (?, ?, ?, ?, date('now'))",
        ("Proyecto sin cliente", "", "media", "activo"),
    )
    conn.commit()
    conn.close()

    database.init_db()

    conn = database.get_connection()
    cantidad = conn.execute("SELECT COUNT(*) as c FROM clientes WHERE nombre = ''").fetchone()["c"]
    conn.close()

    assert cantidad == 0
