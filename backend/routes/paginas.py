"""RUTAS · Páginas: qué dirección del navegador muestra qué archivo de `frontend/`. No aparecen en /docs."""

from fastapi import APIRouter

from controllers import paginas

router = APIRouter(include_in_schema=False)

router.get("/")(paginas.encargos)
router.get("/encargos/nuevo")(paginas.nuevo_encargo)
router.get("/encargos/{encargo_id}")(paginas.ver_encargo)
router.get("/pagos")(paginas.pagos)
router.get("/avisos")(paginas.avisos)
router.get("/config.js")(paginas.configuracion)
