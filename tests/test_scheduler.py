# SERGIO 2026-09-18: pruebas de la actualizacion automatica (feature/actualizacion-automatica)
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_actualizar_actividad_toma_la_ultima_entrada(tmp_path, monkeypatch):
    import database
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    database.init_db()

    carpeta = tmp_path / "proyecto_x"
    carpeta.mkdir()
    (carpeta / "BITACORA.md").write_text(
        "## 2026-09-18 09:00 — Cowork\n"
        "Estado: en progreso\n"
        "Resumen: prueba de actualizacion automatica.\n"
        "Pendientes: ninguno.\n",
        encoding="utf-8",
    )

    conn = database.get_connection()
    conn.execute(
        "INSERT INTO projects (nombre, carpeta, prioridad, estado, fecha_inicio) VALUES (?, ?, ?, ?, date('now'))",
        ("Proyecto X", str(carpeta), "media", "activo"),
    )
    conn.commit()
    conn.close()

    import scheduler
    scheduler.actualizar_actividad()

    conn = database.get_connection()
    fila = conn.execute("SELECT ultima_actividad FROM projects WHERE nombre = ?", ("Proyecto X",)).fetchone()
    conn.close()

    assert fila["ultima_actividad"] is not None
    assert "2026-09-18 09:00" in fila["ultima_actividad"]


def test_actualizar_actividad_sin_bitacora_deja_null(tmp_path, monkeypatch):
    import database
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    database.init_db()

    carpeta = tmp_path / "proyecto_sin_bitacora"
    carpeta.mkdir()

    conn = database.get_connection()
    conn.execute(
        "INSERT INTO projects (nombre, carpeta, prioridad, estado, fecha_inicio) VALUES (?, ?, ?, ?, date('now'))",
        ("Proyecto sin bitacora", str(carpeta), "media", "activo"),
    )
    conn.commit()
    conn.close()

    import scheduler
    scheduler.actualizar_actividad()

    conn = database.get_connection()
    fila = conn.execute(
        "SELECT ultima_actividad FROM projects WHERE nombre = ?", ("Proyecto sin bitacora",)
    ).fetchone()
    conn.close()

    assert fila["ultima_actividad"] is None
