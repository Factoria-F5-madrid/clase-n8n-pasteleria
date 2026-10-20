"""Pastelería La Cuchara: encargos de tartas con señal.

Estructura (MVC):
  models/       MODELO      los datos y las reglas del negocio (señal mínima, plazo de entrega...)
  schemas/                  la forma de los datos que entran y salen por la API (Pydantic)
  controllers/  CONTROLADOR las rutas HTTP: reciben la petición, llaman a los modelos y responden
  ../frontend/  VISTA       la interfaz (HTML, CSS y JavaScript), que usa la API como cualquier otro cliente

Este archivo solo junta las piezas. La API (la que usa n8n) está documentada en /docs.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

import config
import database
import seed
from controllers import avisos, encargos, pagos, paginas, utilidades
from models.errores import NoEncontrado, ReglaDeNegocio

app = FastAPI(title="Pastelería La Cuchara", description="API para integrar n8n con la pastelería.")


@app.exception_handler(ReglaDeNegocio)
def regla_rota(_: Request, error: ReglaDeNegocio):
    return JSONResponse({"detail": str(error)}, status_code=422)


@app.exception_handler(NoEncontrado)
def no_encontrado(_: Request, error: NoEncontrado):
    return JSONResponse({"detail": str(error)}, status_code=404)


for modulo in (encargos, pagos, avisos, utilidades, paginas):
    app.include_router(modulo.router)
app.mount("/static", StaticFiles(directory=config.FRONTEND_DIR), name="frontend")

database.crear_tablas()
if config.SEED and database.esta_vacia():
    seed.cargar()
