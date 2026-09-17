# SERGIO 2026-09-17: esqueleto inicial, listado de proyectos leido desde SQLite
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
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
