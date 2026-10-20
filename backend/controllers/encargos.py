"""CONTROLADOR · Encargos: la lógica de cada petición.

Recibe los datos ya validados, llama a los modelos y devuelve el resultado.
Qué URL llega a cada función se define en routes/encargos.py.
"""

from fastapi import BackgroundTasks, Response

from models import encargo, pago
from schemas.encargo import EncargoIn
from schemas.pago import PagoIn
from services import n8n


def listar(response: Response, estado: str | None = None, q: str = "", pagina: int | None = None, por_pagina: int = 25):
    """Filtra por `estado` (pendiente o pagado) y busca con `q`. Sin `pagina` devuelve todos.
    El total de resultados va en la cabecera `X-Total-Count`."""
    limite = por_pagina if pagina else None
    encargos, total = encargo.listar(estado, q, limite, (max(pagina or 1, 1) - 1) * por_pagina)
    response.headers["X-Total-Count"] = str(total)
    return encargos


def resumen():
    return encargo.contar_por_estado()


def ver(encargo_id: int):
    return encargo.obtener(encargo_id) | {"pagos": pago.de_encargo(encargo_id)}


def crear(datos: EncargoIn, tareas: BackgroundTasks):
    nuevo = encargo.crear(**datos.model_dump())
    tareas.add_task(n8n.avisar, "encargo.creado", nuevo)
    return nuevo


def pagar(encargo_id: int, datos: PagoIn, tareas: BackgroundTasks):
    actualizado = pago.registrar(encargo_id, **datos.model_dump())
    tareas.add_task(n8n.avisar, "pago.registrado", actualizado | {"importe": datos.importe})
    return actualizado
