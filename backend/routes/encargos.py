"""RUTAS · Encargos: qué URL llega a qué función del controlador."""

from fastapi import APIRouter, Depends

from controllers import encargos
from middleware.seguridad import exigir_clave
from schemas.encargo import EncargoDetalle, EncargoOut, Resumen

router = APIRouter(prefix="/api/encargos", tags=["encargos"], dependencies=[Depends(exigir_clave)])

router.get("", response_model=list[EncargoOut], summary="Lista de encargos")(encargos.listar)
router.get("/resumen", response_model=Resumen, summary="Cuántos encargos hay por estado")(encargos.resumen)
router.get("/{encargo_id}", response_model=EncargoDetalle, summary="Un encargo con todos sus pagos")(encargos.ver)
router.post("", response_model=EncargoOut, status_code=201, summary="Crear un encargo (con su señal)")(encargos.crear)
router.post("/{encargo_id}/pagos", response_model=EncargoOut, status_code=201, summary="Registrar un pago")(encargos.pagar)
