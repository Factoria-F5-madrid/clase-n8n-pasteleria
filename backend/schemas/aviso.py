"""SCHEMAS · Aviso: lo que la app ha enviado (o intentado enviar) a n8n."""

from pydantic import BaseModel


class AvisoOut(BaseModel):
    hora: str
    evento: str
    json_enviado: str
    ok: bool
    resultado: str = ""


class AvisosOut(BaseModel):
    url: str
    avisos: list[AvisoOut]
