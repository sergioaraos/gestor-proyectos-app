# SERGIO 2026-09-18: actualizacion automatica de la actividad de cada proyecto (feature/actualizacion-automatica)
import hashlib
from apscheduler.schedulers.background import BackgroundScheduler
import database
import bitacoras
import git_info
import ollama_resumen

_scheduler = None


def actualizar_actividad():
    # Revisa la bitacora y el ultimo commit de cada proyecto y guarda lo encontrado
    conn = database.get_connection()
    proyectos = conn.execute("SELECT id, carpeta, bitacora_hash FROM projects").fetchall()

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

        # SERGIO 2026-09-18: resumen via Ollama, solo se regenera si la bitacora cambio desde
        # la ultima vez (evita llamados innecesarios al modelo local) (feature/resumen-ollama)
        contenido_bitacora = bitacora["contenido_completo"] if bitacora else None
        hash_actual = (
            hashlib.sha256(contenido_bitacora.encode("utf-8")).hexdigest()
            if contenido_bitacora
            else None
        )

        if hash_actual and hash_actual != proyecto["bitacora_hash"]:
            # SERGIO 2026-09-18: el resumen corto ahora lo redacta Ollama en base a las
            # ultimas entradas, no se deriva del resumen completo (feature/resumen-ollama)
            resumen = ollama_resumen.generar_resumen(contenido_bitacora)
            resumen_corto = (
                ollama_resumen.generar_resumen_corto(bitacora["ultimas_entradas_texto"])
                if resumen
                else None
            )
            if resumen and resumen_corto:
                conn.execute(
                    """UPDATE projects
                       SET ultima_actividad = ?, ultimo_commit = ?,
                           resumen_ia = ?, resumen_ia_corto = ?, bitacora_hash = ?
                       WHERE id = ?""",
                    (valor_actividad, valor_commit, resumen, resumen_corto, hash_actual, proyecto["id"]),
                )
                continue
            # Si Ollama no respondio para alguno de los dos resumenes, no se actualiza
            # el hash: se reintenta el ciclo completo en la proxima corrida

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
