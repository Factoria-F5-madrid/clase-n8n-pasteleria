"""CONTROLADOR · Páginas: entrega al navegador los archivos de la carpeta `frontend/`.

La interfaz no tiene lógica de negocio: cada página pide sus datos a la API, igual que n8n.
"""

from fastapi import APIRouter
from fastapi.responses import FileResponse, Response

import config

router = APIRouter(include_in_schema=False)


def pagina(archivo):
    return FileResponse(config.FRONTEND_DIR / archivo)


@router.get("/")
def encargos():
    return pagina("index.html")


@router.get("/encargos/nuevo")
def nuevo_encargo():
    return pagina("nuevo-encargo.html")


@router.get("/encargos/{encargo_id}")
def ver_encargo(encargo_id: int):
    return pagina("encargo.html")


@router.get("/pagos")
def pagos():
    return pagina("pagos.html")


@router.get("/avisos")
def avisos():
    return pagina("avisos.html")


@router.get("/config.js")
def configuracion():
    # ponytail: sin login. La clave viaja al navegador porque la interfaz usa la API como cualquier cliente.
    # Para publicar la app en internet haría falta un login de usuarios en vez de esta clave compartida.
    return Response(f'window.APP_CONFIG = {{ apiKey: "{config.API_KEY}" }};', media_type="text/javascript")
