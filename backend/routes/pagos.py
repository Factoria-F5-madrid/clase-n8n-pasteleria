"""RUTAS · Pagos: qué URL llega a qué función del controlador."""

from fastapi import APIRouter, Depends

from controllers import pagos
from middleware.seguridad import exigir_clave
from schemas.pago import PagoOut

router = APIRouter(prefix="/api/pagos", tags=["consultas"], dependencies=[Depends(exigir_clave)])

router.get("", response_model=list[PagoOut], summary="Pagos entre dos fechas (incluidas)")(pagos.listar)
