# SERGIO 2026-09-18: resumen de bitacora via Ollama local, sin costo de API (feature/resumen-ollama)
import requests

# SERGIO 2026-09-18: mismo modelo y contexto que ya se usa en herramientas-app
OLLAMA_URL = "http://localhost:11434/api/generate"
MODELO = "qwen2.5vl:7b"
CONTEXTO = 16384

PROMPT_BASE = (
    "Eres un asistente que redacta un resumen breve, en espanol neutro, "
    "del avance de un proyecto de software a partir de su bitacora de trabajo. "
    "La bitacora tiene varias entradas en orden cronologico. Considera la evolucion "
    "completa, no solo la ultima entrada, para describir en que estado esta el proyecto "
    "y hacia donde va. Responde solo con el resumen, en un parrafo, sin titulos ni listas.\n\n"
    "Bitacora:\n"
)

# SERGIO 2026-09-18: prompt para el resumen corto de las tarjetas, enfocado solo
# en las ultimas tareas realizadas (feature/resumen-ollama)
PROMPT_BASE_CORTO = (
    "Eres un asistente que redacta, en espanol neutro y en un parrafo breve (2 a 3 "
    "oraciones), un resumen de las ultimas tareas realizadas en un proyecto de "
    "software, a partir de las ultimas entradas de su bitacora de trabajo. "
    "Responde solo con el resumen, sin titulos ni listas.\n\n"
    "Ultimas entradas de la bitacora:\n"
)


def _llamar_ollama(prompt: str):
    """
    Llamado HTTP compartido a la API local de Ollama. Devuelve el texto de la
    respuesta, o None si Ollama no esta disponible, no responde a tiempo, o la
    respuesta viene vacia. Comparte esta logica generar_resumen y
    generar_resumen_corto para no duplicar el manejo de errores.
    """
    try:
        respuesta = requests.post(
            OLLAMA_URL,
            json={
                "model": MODELO,
                "prompt": prompt,
                "stream": False,
                "options": {"num_ctx": CONTEXTO},
            },
            # SERGIO 2026-09-18: 300s, una bitacora grande puede tardar mas en
            # procesarse con un modelo local (feature/resumen-ollama)
            timeout=300,
        )
        respuesta.raise_for_status()
    except (requests.exceptions.RequestException, ValueError) as error:
        # SERGIO 2026-09-18: se deja un aviso en consola para no fallar en silencio
        # (feature/resumen-ollama)
        print(f"[ollama_resumen] no se pudo generar el resumen: {error}")
        return None

    texto = respuesta.json().get("response", "").strip()
    return texto or None


def generar_resumen(bitacora_texto: str):
    """
    Le pide a Ollama un resumen en palabras del avance de un proyecto, a partir
    del contenido completo de su bitacora (todas las entradas, no solo la ultima).
    """
    if not bitacora_texto:
        return None

    return _llamar_ollama(PROMPT_BASE + bitacora_texto)


def generar_resumen_corto(entradas_texto):
    """
    Le pide a Ollama un resumen breve de las ultimas tareas realizadas, a partir
    de una lista de bloques crudos con las ultimas entradas de la bitacora
    (ver bitacoras.leer_bitacora -> "ultimas_entradas_texto"). Se usa para el
    texto que se muestra en las tarjetas del listado.
    """
    if not entradas_texto:
        return None

    texto_entradas = "\n\n".join(entradas_texto)
    return _llamar_ollama(PROMPT_BASE_CORTO + texto_entradas)
