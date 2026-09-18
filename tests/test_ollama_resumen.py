# SERGIO 2026-09-18: pruebas del modulo de resumen via Ollama (feature/resumen-ollama)
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import ollama_resumen


class RespuestaFalsa:
    """Simula la respuesta de requests.post sin llamar a Ollama de verdad."""

    def __init__(self, texto, status_ok=True):
        self._texto = texto
        self._status_ok = status_ok

    def raise_for_status(self):
        if not self._status_ok:
            raise ollama_resumen.requests.exceptions.RequestException("error simulado")

    def json(self):
        return {"response": self._texto}


def test_generar_resumen_devuelve_texto_de_ollama(monkeypatch):
    def post_falso(url, json, timeout):
        assert url == ollama_resumen.OLLAMA_URL
        assert json["model"] == ollama_resumen.MODELO
        assert json["options"]["num_ctx"] == ollama_resumen.CONTEXTO
        return RespuestaFalsa("El proyecto avanza bien, con foco en la integracion git.")

    monkeypatch.setattr(ollama_resumen.requests, "post", post_falso)

    resultado = ollama_resumen.generar_resumen("## 2026-09-18 — Cowork\nEstado: activo\n")

    assert resultado == "El proyecto avanza bien, con foco en la integracion git."


def test_generar_resumen_devuelve_none_si_ollama_no_responde(monkeypatch):
    def post_falso(url, json, timeout):
        raise ollama_resumen.requests.exceptions.ConnectionError("Ollama no esta corriendo")

    monkeypatch.setattr(ollama_resumen.requests, "post", post_falso)

    resultado = ollama_resumen.generar_resumen("## 2026-09-18 — Cowork\nEstado: activo\n")

    assert resultado is None


def test_generar_resumen_sin_bitacora_no_llama_a_ollama(monkeypatch):
    def post_falso(url, json, timeout):
        raise AssertionError("no deberia llamarse a Ollama sin contenido de bitacora")

    monkeypatch.setattr(ollama_resumen.requests, "post", post_falso)

    assert ollama_resumen.generar_resumen("") is None
    assert ollama_resumen.generar_resumen(None) is None


# SERGIO 2026-09-18: pruebas del resumen corto de las tarjetas (feature/resumen-ollama)
def test_generar_resumen_corto_devuelve_texto_de_ollama(monkeypatch):
    def post_falso(url, json, timeout):
        assert url == ollama_resumen.OLLAMA_URL
        assert "entrada A" in json["prompt"]
        assert "entrada B" in json["prompt"]
        return RespuestaFalsa("Se avanzo en la entrada A y se cerro la entrada B.")

    monkeypatch.setattr(ollama_resumen.requests, "post", post_falso)

    resultado = ollama_resumen.generar_resumen_corto(["## ... entrada A ...", "## ... entrada B ..."])

    assert resultado == "Se avanzo en la entrada A y se cerro la entrada B."


def test_generar_resumen_corto_devuelve_none_si_ollama_no_responde(monkeypatch):
    def post_falso(url, json, timeout):
        raise ollama_resumen.requests.exceptions.Timeout("Ollama tardo demasiado")

    monkeypatch.setattr(ollama_resumen.requests, "post", post_falso)

    resultado = ollama_resumen.generar_resumen_corto(["## ... entrada A ..."])

    assert resultado is None


def test_generar_resumen_corto_sin_entradas_no_llama_a_ollama(monkeypatch):
    def post_falso(url, json, timeout):
        raise AssertionError("no deberia llamarse a Ollama sin entradas")

    monkeypatch.setattr(ollama_resumen.requests, "post", post_falso)

    assert ollama_resumen.generar_resumen_corto([]) is None
    assert ollama_resumen.generar_resumen_corto(None) is None
