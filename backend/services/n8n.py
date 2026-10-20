"""SERVICIO · Avisar a n8n por webhook y guardar los últimos avisos para poder verlos en pantalla."""

import json
import logging
import urllib.error
import urllib.request
from collections import deque
from datetime import datetime

import config

log = logging.getLogger("pasteleria")
AVISOS = deque(maxlen=20)  # los últimos 20, el más reciente primero


def avisar(evento, datos):
    """Envía el aviso a n8n. Si n8n no responde, la pastelería sigue funcionando."""
    cuerpo = json.dumps({"evento": evento, "datos": datos}, ensure_ascii=False, indent=2, default=str)
    aviso = {"hora": datetime.now().strftime("%H:%M:%S"), "evento": evento, "json_enviado": cuerpo, "ok": False}
    AVISOS.appendleft(aviso)
    if not config.N8N_WEBHOOK_URL:
        aviso["resultado"] = "No se ha enviado: N8N_WEBHOOK_URL está vacío en el .env"
        return
    peticion = urllib.request.Request(config.N8N_WEBHOOK_URL, cuerpo.encode(), {"Content-Type": "application/json"})
    try:
        respuesta = urllib.request.urlopen(peticion, timeout=5)
        aviso["ok"], aviso["resultado"] = True, f"Enviado. n8n respondió {respuesta.status}"
    except urllib.error.HTTPError as e:
        pista = " (ningún flujo publicado escucha esta dirección)" if e.code == 404 else ""
        aviso["resultado"] = f"n8n respondió {e.code}{pista}"
    except Exception as e:
        aviso["resultado"] = f"No se pudo llegar a n8n: {e}"
        log.warning("No se pudo avisar a n8n (%s): %s", evento, e)


def ultimos():
    return list(AVISOS)
