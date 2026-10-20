"""CONTROLADOR · Avisos: qué ha enviado la app a n8n (para verlo en la pantalla «Avisos a n8n»)."""

import config
from services import n8n


def listar():
    return {"url": config.N8N_WEBHOOK_URL, "avisos": n8n.ultimos()}
