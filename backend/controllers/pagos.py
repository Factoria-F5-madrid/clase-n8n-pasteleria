"""CONTROLADOR · Pagos: consultas sobre todos los pagos. Las URL están en routes/pagos.py."""

from datetime import date

from fastapi import Response

from models import pago


def listar(response: Response, desde: date | None = None, hasta: date | None = None, orden: str = "asc",
           pagina: int | None = None, por_pagina: int = 25):
    """Sin `pagina` devuelve todos. `orden=desc` muestra primero los más recientes."""
    limite = por_pagina if pagina else None
    pagos, total = pago.listar(desde, hasta, orden == "desc", limite, (max(pagina or 1, 1) - 1) * por_pagina)
    response.headers["X-Total-Count"] = str(total)
    return pagos
