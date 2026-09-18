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

    # SERGIO 2026-09-18: migracion simple, agrega la columna si la base ya existia sin ella
    columnas = [fila["name"] for fila in conn.execute("PRAGMA table_info(projects)").fetchall()]
    if "ultima_actividad" not in columnas:
        conn.execute("ALTER TABLE projects ADD COLUMN ultima_actividad TEXT")
        conn.commit()
    if "ultimo_commit" not in columnas:
        conn.execute("ALTER TABLE projects ADD COLUMN ultimo_commit TEXT")
        conn.commit()

    # SERGIO 2026-09-18: columnas para el resumen generado por IA (feature/resumen-ollama)
    if "resumen_ia" not in columnas:
        conn.execute("ALTER TABLE projects ADD COLUMN resumen_ia TEXT")
        conn.commit()
    if "resumen_ia_corto" not in columnas:
        conn.execute("ALTER TABLE projects ADD COLUMN resumen_ia_corto TEXT")
        conn.commit()
    if "bitacora_hash" not in columnas:
        conn.execute("ALTER TABLE projects ADD COLUMN bitacora_hash TEXT")
        conn.commit()

    # SERGIO 2026-09-18: tabla de clientes, para elegirlos desde una lista al crear
    # un proyecto en vez de escribirlos a mano (feature/tabla-clientes)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE
        )
    """)
    conn.commit()

    # SERGIO 2026-09-18: migra los nombres de cliente ya escritos en proyectos existentes,
    # para no perder lo que ya se habia cargado a mano (feature/tabla-clientes)
    clientes_existentes = conn.execute(
        "SELECT DISTINCT cliente FROM projects WHERE cliente IS NOT NULL AND TRIM(cliente) != ''"
    ).fetchall()
    for fila in clientes_existentes:
        conn.execute("INSERT OR IGNORE INTO clientes (nombre) VALUES (?)", (fila["cliente"].strip(),))
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

    