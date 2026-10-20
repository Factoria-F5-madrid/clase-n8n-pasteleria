"""SCHEMAS · Pago: la forma de los datos que entran y salen por la API."""

from datetime import date

from pydantic import BaseModel


class PagoIn(BaseModel):
    importe: float
    forma_pago: str = "efectivo"


class PagoOut(BaseModel):
    id: int
    encargo_id: int
    fecha: date
    importe: float
    forma_pago: str
    cliente: str | None = None  # solo aparece al listar pagos
