# SERGIO 2026-09-17: esqueleto inicial, listado de proyectos leido desde SQLite
import os
import sqlite3
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import database
import bitacoras
import git_info
import scheduler
import config

app = FastAPI(title="Gestor de Proyectos")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
# SERGIO 2026-09-17: sirve el CSS del diseno visual (feature/diseno-visual)
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


@app.on_event("startup")
def on_startup():
    # Crea la tabla si no existe y precarga los proyectos iniciales la primera vez
    database.init_db()
    # SERGIO 2026-09-18: arranca la actualizacion automatica (feature/actualizacion-automatica)
    # Se desactiva bajo pytest para que las pruebas no dejen un hilo de fondo corriendo
    if not os.environ.get("PYTEST_CURRENT_TEST"):
        scheduler.iniciar_scheduler(config.REFRESH_INTERVAL_MINUTES)


@app.on_event("shutdown")
def on_shutdown():
    # SERGIO 2026-09-18: detiene el scheduler al cerrar la app (feature/actualizacion-automatica)
    scheduler.detener_scheduler()


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
    # SERGIO 2026-09-18: se pasa la ruta base para mostrarla como prefijo fijo (feature/prefijo-carpeta)
    # SERGIO 2026-09-18: se pasa la lista de clientes para el desplegable (feature/tabla-clientes)
    conn = database.get_connection()
    clientes = conn.execute("SELECT * FROM clientes ORDER BY nombre").fetchall()
    conn.close()
    return templates.TemplateResponse(
        request, "nuevo.html", {"ruta_base": config.RUTA_BASE_PROYECTOS, "clientes": clientes}
    )


# SERGIO 2026-09-18: alta y listado de clientes (feature/tabla-clientes)
@app.get("/clientes")
def listado_clientes(request: Request):
    # Muestra los clientes ya registrados y el formulario para agregar uno nuevo
    conn = database.get_connection()
    clientes = conn.execute("SELECT * FROM clientes ORDER BY nombre").fetchall()
    conn.close()
    return templates.TemplateResponse(request, "clientes.html", {"clientes": clientes})


@app.post("/clientes")
def crear_cliente(nombre: str = Form(...)):
    # Agrega un cliente nuevo; si el nombre ya existe, no hace nada (UNIQUE en la tabla)
    nombre = nombre.strip()
    if nombre:
        conn = database.get_connection()
        conn.execute("INSERT OR IGNORE INTO clientes (nombre) VALUES (?)", (nombre,))
        conn.commit()
        conn.close()
    return RedirectResponse(url="/clientes", status_code=303)


@app.post("/clientes/{cliente_id}/editar")
def editar_cliente(cliente_id: int, nombre: str = Form(...)):
    # SERGIO 2026-09-18: renombra un cliente y actualiza en cascada los proyectos que ya
    # lo tenian asignado (guardado como texto), para que no queden desincronizados
    # (feature/tabla-clientes)
    nombre = nombre.strip()
    if nombre:
        conn = database.get_connection()
        anterior = conn.execute("SELECT nombre FROM clientes WHERE id = ?", (cliente_id,)).fetchone()
        if anterior and anterior["nombre"] != nombre:
            try:
                conn.execute("UPDATE clientes SET nombre = ? WHERE id = ?", (nombre, cliente_id))
                conn.execute("UPDATE projects SET cliente = ? WHERE cliente = ?", (nombre, anterior["nombre"]))
                conn.commit()
            except sqlite3.IntegrityError:
                # Ya existe otro cliente con ese nombre (UNIQUE): se ignora el cambio
                conn.rollback()
        conn.close()
    return RedirectResponse(url="/clientes", status_code=303)


@app.post("/clientes/{cliente_id}/eliminar")
def eliminar_cliente(cliente_id: int):
    # SERGIO 2026-09-18: borra el cliente de la lista. Los proyectos que ya lo tenian
    # asignado no se tocan, solo deja de estar disponible para proyectos nuevos
    # (feature/tabla-clientes)
    conn = database.get_connection()
    conn.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/clientes", status_code=303)


@app.post("/nuevo")
def crear_proyecto(
    nombre: str = Form(...),
    cliente: str = Form(""),
    prioridad: str = Form("media"),
    carpeta_nombre: str = Form(""),
    herramienta: str = Form(""),
):
    # SERGIO 2026-09-18: la carpeta se arma con el prefijo fijo (RUTA_BASE_PROYECTOS) mas
    # el nombre que ingresa el usuario, ya que todos los proyectos viven en la misma
    # ubicacion (feature/prefijo-carpeta)
    carpeta_nombre = carpeta_nombre.strip().strip("\\/")
    carpeta = str(Path(config.RUTA_BASE_PROYECTOS) / carpeta_nombre) if carpeta_nombre else ""

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


# SERGIO 2026-09-17: detalle de proyecto, lee su bitacora (feature/lectura-bitacoras)
@app.get("/proyecto/{project_id}")
def detalle_proyecto(request: Request, project_id: int):
    # Muestra el detalle de un proyecto junto con lo que se lee de su bitacora
    conn = database.get_connection()
    proyecto = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    conn.close()

    bitacora = bitacoras.leer_bitacora(proyecto["carpeta"]) if proyecto else None
    # SERGIO 2026-09-18: info de git en vivo para el detalle (feature/integracion-git)
    git = git_info.leer_git(proyecto["carpeta"]) if proyecto else None

    status_code = 200 if proyecto else 404
    return templates.TemplateResponse(
        request,
        "detalle.html",
        {"proyecto": proyecto, "bitacora": bitacora, "git": git},
        status_code=status_code,
    )
