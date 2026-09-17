# SERGIO 2026-09-18: actualizacion automatica de la actividad de cada proyecto (feature/actualizacion-automatica)
from apscheduler.schedulers.background import BackgroundScheduler
import database
import bitacoras

_scheduler = None


def actualizar_actividad():
    # Revisa la bitacora de cada proyecto y guarda la fecha de su ultima entrada
    conn = database.get_connection()
    proyectos = conn.execute("SELECT id, carpeta FROM projects").fetchall()

    for proyecto in proyectos:
        bitacora = bitacoras.leer_bitacora(proyecto["carpeta"])
        if bitacora and bitacora["ultima_entrada"]:
            valor = bitacora["ultima_entrada"]["fecha_herramienta"]
        else:
            valor = None
        conn.execute(
            "UPDATE projects SET ultima_actividad = ? WHERE id = ?",
            (valor, proyecto["id"]),
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
