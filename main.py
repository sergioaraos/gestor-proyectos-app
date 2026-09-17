# SERGIO 2026-09-17: esqueleto inicial, listado de proyectos leido desde SQLite
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from pathlib import Path
import database

app = FastAPI(title="Gestor de Proyectos")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


@app.on_event("startup")
def on_startup():
    # Crea la tabla si no existe y precarga los proyectos iniciales la primera vez
    database.init_db()


@app.get("/")
def index(request: Request):
    # Lista todos los proyectos, prioridad alta primero
    conn = database.get_connection()
    projects = conn.execute("SELECT * FROM projects ORDER BY prioridad DESC, nombre").fetchall()
    conn.close()
    return templates.TemplateResponse(request, "index.html", {"projects": projects})


# SERGIO 2026-09-17: formulario de alta de proyectos (feature/alta-proyectos)
@app.get("/nuevo")
def nuevo_proyecto_form(request: Request):
    # Muestra el formulario vacio para dar de alta un proyecto nuevo
    return templates.TemplateResponse(request, "nuevo.html", {})


@app.post("/nuevo")
def crear_proyecto(
    nombre: str = Form(...),
    cliente: str = Form(""),
    prioridad: str = Form("media"),
    carpeta: str = Form(""),
    herramienta: str = Form(""),
):
    # Inserta el proyecto con estado "activo" y fecha de inicio de hoy por defecto
    conn = database.get_connection()
    conn.execute(
        """INSERT INTO projects (nombre, cliente, prioridad, carpeta, herramienta, estado, fecha_inicio)
           VALUES (?, ?, ?, ?, ?, 'activo', date('now'))""",
        (nombre, cliente, prioridad, carpeta, herramienta),
    )
    conn.commit()
    conn.close()
    # Vuelve al listado para ver el proyecto recien creado
    return RedirectResponse(url="/", status_code=303)
