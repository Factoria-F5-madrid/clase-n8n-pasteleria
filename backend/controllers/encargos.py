"""CONTROLADOR · Encargos: recibe las peticiones HTTP, llama a los modelos y devuelve la respuesta."""

from fastapi import APIRouter, BackgroundTasks, Depends, Response

from controllers.seguridad import exigir_clave
from models import encargo, pago
from schemas.encargo import EncargoDetalle, EncargoIn, EncargoOut, Resumen
from schemas.pago import PagoIn
from services import n8n

router = APIRouter(prefix="/api/encargos", tags=["encargos"], dependencies=[Depends(exigir_clave)])


@router.get("", response_model=list[EncargoOut], summary="Lista de encargos")
def listar(response: Response, estado: str | None = None, q: str = "", pagina: int | None = None, por_pagina: int = 25):
    """Filtra por `estado` (pendiente o pagado) y busca con `q`. Sin `pagina` devuelve todos.
    El total de resultados va en la cabecera `X-Total-Count`."""
    limite = por_pagina if pagina else None
    encargos, total = encargo.listar(estado, q, limite, (max(pagina or 1, 1) - 1) * por_pagina)
    response.headers["X-Total-Count"] = str(total)
    return encargos


@router.get("/resumen", response_model=Resumen, summary="Cuántos encargos hay por estado")
def resumen():
    return encargo.contar_por_estado()


@router.get("/{encargo_id}", response_model=EncargoDetalle, summary="Un encargo con todos sus pagos")
def ver(encargo_id: int):
    return encargo.obtener(encargo_id) | {"pagos": pago.de_encargo(encargo_id)}


@router.post("", response_model=EncargoOut, status_code=201, summary="Crear un encargo (con su señal)")
def crear(datos: EncargoIn, tareas: BackgroundTasks):
    nuevo = encargo.crear(**datos.model_dump())
    tareas.add_task(n8n.avisar, "encargo.creado", nuevo)
    return nuevo


@router.post("/{encargo_id}/pagos", response_model=EncargoOut, status_code=201, summary="Registrar un pago")
def pagar(encargo_id: int, datos: PagoIn, tareas: BackgroundTasks):
    actualizado = pago.registrar(encargo_id, **datos.model_dump())
    tareas.add_task(n8n.avisar, "pago.registrado", actualizado | {"importe": datos.importe})
    return actualizado
