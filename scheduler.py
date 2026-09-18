# SERGIO 2026-09-18: actualizacion automatica de la actividad de cada proyecto (feature/actualizacion-automatica)
from apscheduler.schedulers.background import BackgroundScheduler
import database
import bitacoras
import git_info

_scheduler = None


def actualizar_actividad():
    # Revisa la bitacora y el ultimo commit de cada proyecto y guarda lo encontrado
    conn = database.get_connection()
    proyectos = conn.execute("SELECT id, carpeta FROM projects").fetchall()

    for proyecto in proyectos:
        bitacora = bitacoras.leer_bitacora(proyecto["carpeta"])
        if bitacora and bitacora["ultima_entrada"]:
            valor_actividad = bitacora["ultima_entrada"]["fecha_herramienta"]
        else:
            valor_actividad = None

        # SERGIO 2026-09-18: ultimo commit git, si la carpeta es un repositorio (feature/integracion-git)
        git = git_info.leer_git(proyecto["carpeta"])
        if git:
            valor_commit = f"{git['hash']} · {git['fecha']} · {git['mensaje']}"
        else:
            valor_commit = None

        conn.execute(
            "UPDATE projects SET ultima_actividad = ?, ultimo_commit = ? WHERE id = ?",
            (valor_actividad, valor_commit, proyecto["id"]),
        )

    conn.commit()
    conn.close()


def iniciar_scheduler(intervalo_minutos: int):
    # Corre una vez al arrancar, y despues cada intervalo_minutos en segundo plano
    global _scheduler
    actualizar_actividad()
    _scheduler = BackgroundScheduler()
    _scheduler.add_job(actualizar_actividad, "interval", minutes=intervalo_minutos)
    _scheduler.start()


def detener_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
