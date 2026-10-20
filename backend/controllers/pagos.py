"""CONTROLADOR · Pagos: consultas sobre todos los pagos."""

from datetime import date

from fastapi import APIRouter, Depends, Response

from controllers.seguridad import exigir_clave
from models import pago
from schemas.pago import PagoOut

router = APIRouter(prefix="/api/pagos", tags=["consultas"], dependencies=[Depends(exigir_clave)])


@router.get("", response_model=list[PagoOut], summary="Pagos entre dos fechas (incluidas)")
def listar(response: Response, desde: date | None = None, hasta: date | None = None, orden: str = "asc",
           pagina: int | None = None, por_pagina: int = 25):
    """Sin `pagina` devuelve todos. `orden=desc` muestra primero los más recientes."""
    limite = por_pagina if pagina else None
    pagos, total = pago.listar(desde, hasta, orden == "desc", limite, (max(pagina or 1, 1) - 1) * por_pagina)
    response.headers["X-Total-Count"] = str(total)
    return pagos
