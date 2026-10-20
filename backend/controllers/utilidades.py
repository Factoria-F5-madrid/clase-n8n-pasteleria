"""CONTROLADOR · Utilidades: descargar los datos en Excel y volver a los datos de ejemplo."""

import io
from datetime import date

from fastapi.responses import StreamingResponse
from openpyxl import Workbook

import database
import seed
from models import encargo

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


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


def reset():
    database.vaciar()
    seed.cargar()
    return {"ok": True}
