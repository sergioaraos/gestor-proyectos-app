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

    # SERGIO 2026-09-18: evita llamar a Ollama de verdad en este test (feature/resumen-ollama)
    import ollama_resumen
    monkeypatch.setattr(ollama_resumen, "generar_resumen", lambda texto: None)

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


# SERGIO 2026-09-18: pruebas del resumen via Ollama dentro del ciclo de actualizacion (feature/resumen-ollama)
def test_actualizar_actividad_genera_resumen_cuando_la_bitacora_cambio(tmp_path, monkeypatch):
    import database
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    database.init_db()

    carpeta = tmp_path / "proyecto_y"
    carpeta.mkdir()
    (carpeta / "BITACORA.md").write_text(
        "## 2026-09-18 10:00 — Cowork\nEstado: activo\nResumen: primera entrada.\nPendientes: nada.\n",
        encoding="utf-8",
    )

    conn = database.get_connection()
    conn.execute(
        "INSERT INTO projects (nombre, carpeta, prioridad, estado, fecha_inicio) VALUES (?, ?, ?, ?, date('now'))",
        ("Proyecto Y", str(carpeta), "media", "activo"),
    )
    conn.commit()
    conn.close()

    import ollama_resumen
    monkeypatch.setattr(ollama_resumen, "generar_resumen", lambda texto: "Resumen de prueba generado por IA.")
    # SERGIO 2026-09-18: el resumen corto ahora es un llamado aparte a Ollama, en base
    # a las ultimas entradas (feature/resumen-ollama)
    monkeypatch.setattr(ollama_resumen, "generar_resumen_corto", lambda entradas: "Ultimas tareas: prueba.")

    import scheduler
    scheduler.actualizar_actividad()

    conn = database.get_connection()
    fila = conn.execute(
        "SELECT resumen_ia, resumen_ia_corto, bitacora_hash FROM projects WHERE nombre = ?", ("Proyecto Y",)
    ).fetchone()
    conn.close()

    assert fila["resumen_ia"] == "Resumen de prueba generado por IA."
    assert fila["resumen_ia_corto"] == "Ultimas tareas: prueba."
    assert fila["bitacora_hash"] is not None


def test_actualizar_actividad_no_llama_a_ollama_si_la_bitacora_no_cambio(tmp_path, monkeypatch):
    import database
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    database.init_db()

    carpeta = tmp_path / "proyecto_z"
    carpeta.mkdir()
    (carpeta / "BITACORA.md").write_text(
        "## 2026-09-18 11:00 — Cowork\nEstado: activo\nResumen: entrada sin cambios.\nPendientes: nada.\n",
        encoding="utf-8",
    )

    conn = database.get_connection()
    conn.execute(
        "INSERT INTO projects (nombre, carpeta, prioridad, estado, fecha_inicio) VALUES (?, ?, ?, ?, date('now'))",
        ("Proyecto Z", str(carpeta), "media", "activo"),
    )
    conn.commit()
    conn.close()

    import ollama_resumen
    import scheduler

    llamados = []

    def generar_falso(texto):
        llamados.append(texto)
        return "Resumen inicial."

    monkeypatch.setattr(ollama_resumen, "generar_resumen", generar_falso)
    # SERGIO 2026-09-18: tambien hay que simular el resumen corto, si no queda en None
    # y el ciclo nunca actualiza el hash (feature/resumen-ollama)
    monkeypatch.setattr(ollama_resumen, "generar_resumen_corto", lambda entradas: "Ultimas tareas: prueba.")

    # SERGIO 2026-09-18: la base de prueba precarga proyectos por defecto (con carpetas
    # reales) ademas de "Proyecto Z", asi que no se asume un total fijo de llamados: solo
    # que la segunda corrida, sin cambios en ninguna bitacora, no agregue llamados nuevos
    scheduler.actualizar_actividad()
    llamados_primera_corrida = len(llamados)
    assert llamados_primera_corrida >= 1

    scheduler.actualizar_actividad()
    assert len(llamados) == llamados_primera_corrida
