"""CONTROLADOR · Avisos: qué ha enviado la app a n8n (para verlo en la pantalla «Avisos a n8n»)."""

from fastapi import APIRouter, Depends

import config
from controllers.seguridad import exigir_clave
from schemas.aviso import AvisosOut
from services import n8n

router = APIRouter(prefix="/api/avisos", tags=["consultas"], dependencies=[Depends(exigir_clave)])


@router.get("", response_model=AvisosOut, summary="Últimos avisos enviados a n8n")
def listar():
    return {"url": config.N8N_WEBHOOK_URL, "avisos": n8n.ultimos()}
