# SERGIO 2026-09-18: configuracion parametrizable (feature/actualizacion-automatica)
import os

# Cada cuantos minutos se relee la bitacora de todos los proyectos.
# Se puede cambiar sin tocar codigo con la variable de entorno REFRESH_INTERVAL_MINUTES.
REFRESH_INTERVAL_MINUTES = int(os.environ.get("REFRESH_INTERVAL_MINUTES", "10"))
