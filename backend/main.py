"""Pastelería La Cuchara: encargos de tartas con señal.

Estructura (MVC):
  models/       MODELO      los datos y las reglas del negocio (señal mínima, plazo de entrega...)
  schemas/                  la forma de los datos que entran y salen por la API (Pydantic)
  routes/                   qué URL llega a qué función del controlador
  controllers/  CONTROLADOR la lógica de cada petición: llama a los modelos y devuelve la respuesta
  middleware/               lo que se ejecuta antes o alrededor: comprobar la clave, convertir errores en respuestas
  ../frontend/  VISTA       la interfaz (HTML, CSS y JavaScript), que usa la API como cualquier otro cliente

Este archivo solo junta las piezas. La API (la que usa n8n) está documentada en /docs.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

import config
import database
import seed
from middleware import errores
from routes import avisos, encargos, pagos, paginas, utilidades

app = FastAPI(title="Pastelería La Cuchara", description="API para integrar n8n con la pastelería.")

errores.registrar(app)
for modulo in (encargos, pagos, avisos, utilidades, paginas):
    app.include_router(modulo.router)
app.mount("/static", StaticFiles(directory=config.FRONTEND_DIR), name="frontend")

database.crear_tablas()
if config.SEED and database.esta_vacia():
    seed.cargar()
