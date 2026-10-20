"""CONTROLADOR · Utilidades: descargar los datos en Excel y volver a los datos de ejemplo."""

import io
from datetime import date

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from openpyxl import Workbook

import database
import seed
from controllers.seguridad import exigir_clave
from models import encargo

router = APIRouter(prefix="/api", tags=["utilidades"], dependencies=[Depends(exigir_clave)])

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@router.get("/excel", summary="Descargar todos los datos en un Excel (una hoja por tabla)")
def excel():
    hojas = {
        "Encargos": (["id", "fecha", "cliente", "email", "tarta", "raciones", "precio", "pagado", "pendiente",
                      "fecha_entrega", "estado"], encargo.listar()[0]),
        "Pagos": (["id", "encargo_id", "fecha", "importe", "forma_pago"],
                  database.consultar("SELECT * FROM pagos ORDER BY fecha, id")),
    }
    libro = Workbook()
    libro.remove(libro.active)
    for nombre, (columnas, filas) in hojas.items():
        hoja = libro.create_sheet(nombre)
        hoja.append(columnas)
        for fila in filas:
            hoja.append([fila[c] for c in columnas])
    memoria = io.BytesIO()
    libro.save(memoria)
    memoria.seek(0)
    return StreamingResponse(memoria, media_type=XLSX,
                             headers={"Content-Disposition": f'attachment; filename="la-cuchara-{date.today()}.xlsx"'})


@router.post("/reset", summary="Borra todo y vuelve a cargar los datos de ejemplo")
def reset():
    database.vaciar()
    seed.cargar()
    return {"ok": True}
