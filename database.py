import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "gestor.db"

def get_connection():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            cliente TEXT,
            prioridad TEXT,
            carpeta TEXT,
            herramienta TEXT,
            estado TEXT DEFAULT 'activo',
            fecha_inicio TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    existing = conn.execute("SELECT COUNT(*) as c FROM projects").fetchone()["c"]
    if existing == 0:
        conn.executemany(
            """INSERT INTO projects (nombre, cliente, prioridad, carpeta, herramienta, estado, fecha_inicio)
               VALUES (?, ?, ?, ?, ?, ?, date('now'))""",
            [
                ("TecnoRegistros", "TecnoPest", "media", r"C:\laragon\www\TecnoRegistros", "Claude Code", "activo"),
                ("gestor-proyectos-app", "uso propio", "alta", r"C:\laragon\www\gestor-proyectos-app", "Cowork", "activo"),
            ]
        )
        conn.commit()
    conn.close()

    