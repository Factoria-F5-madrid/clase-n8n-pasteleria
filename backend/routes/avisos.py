"""RUTAS · Avisos: qué URL llega a qué función del controlador."""

from fastapi import APIRouter, Depends

from controllers import avisos
from middleware.seguridad import exigir_clave
from schemas.aviso import AvisosOut

router = APIRouter(prefix="/api/avisos", tags=["consultas"], dependencies=[Depends(exigir_clave)])

router.get("", response_model=AvisosOut, summary="Últimos avisos enviados a n8n")(avisos.listar)
