"""CONTROLADOR · Páginas: entrega al navegador los archivos de la carpeta `frontend/`.

La interfaz no tiene lógica de negocio: cada página pide sus datos a la API, igual que n8n.
"""

from fastapi.responses import FileResponse, Response

import config


def pagina(archivo):
    return FileResponse(config.FRONTEND_DIR / archivo)


def encargos():
    return pagina("index.html")


def nuevo_encargo():
    return pagina("nuevo-encargo.html")


def ver_encargo(encargo_id: int):
    return pagina("encargo.html")


def pagos():
    return pagina("pagos.html")


def avisos():
    return pagina("avisos.html")


def configuracion():
    # ponytail: sin login. La clave viaja al navegador porque la interfaz usa la API como cualquier cliente.
    # Para publicar la app en internet haría falta un login de usuarios en vez de esta clave compartida.
    return Response(f'window.APP_CONFIG = {{ apiKey: "{config.API_KEY}" }};', media_type="text/javascript")
