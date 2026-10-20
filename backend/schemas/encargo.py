"""SCHEMAS · Encargo: la forma de los datos que entran y salen por la API."""

from datetime import date

from pydantic import BaseModel, Field

from schemas.pago import PagoOut


class EncargoIn(BaseModel):
    cliente: str
    email: str | None = None
    tarta: str
    raciones: int = Field(gt=0)
    precio: float = Field(gt=0)
    fecha_entrega: date = Field(description="Entre mañana y dentro de 30 días")
    senal: float = Field(description="Mínimo 10 €")
    forma_pago: str = "efectivo"


class EncargoOut(BaseModel):
    id: int
    fecha: date
    cliente: str
    email: str | None
    tarta: str
    raciones: int
    precio: float
    fecha_entrega: date
    estado: str
    pagado: float
    pendiente: float


class EncargoDetalle(EncargoOut):
    pagos: list[PagoOut]


class Resumen(BaseModel):
    pendiente: int
    pagado: int
    total: int
