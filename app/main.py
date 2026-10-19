"""Pastelería La Cuchara: encargos de tartas con señal.

App de ejemplo para la clase de n8n. Guarda los encargos y los pagos, aplica las reglas
y avisa a n8n por webhook. Todo lo demás (avisos, cierres, leer correos) lo hace n8n.
Pantallas en http://localhost:8000 y API (la que usa n8n) documentada en http://localhost:8000/docs
"""

import io
import json
import logging
import os
import sqlite3
import urllib.parse
import urllib.error
import urllib.request
from collections import deque
from datetime import date, datetime, timedelta

from fastapi import BackgroundTasks, Depends, FastAPI, Form, HTTPException, Request
from fastapi.security import APIKeyHeader
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from openpyxl import Workbook
from pydantic import BaseModel, Field

DB_PATH = os.getenv("DB_PATH", "pasteleria.db")
API_KEY = os.getenv("API_KEY", "")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "")
SENAL_MINIMA = 10
MAX_DIAS_ENTREGA = 30
FORMAS_PAGO = ["efectivo", "tarjeta", "bizum", "transferencia"]

log = logging.getLogger("pasteleria")
app = FastAPI(title="Pastelería La Cuchara", description="API para integrar n8n con la pastelería.")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS encargos (
  id INTEGER PRIMARY KEY, fecha TEXT NOT NULL, cliente TEXT NOT NULL, email TEXT,
  tarta TEXT NOT NULL, raciones INTEGER NOT NULL, precio REAL NOT NULL, fecha_entrega TEXT NOT NULL,
  estado TEXT NOT NULL DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'pagado')));
CREATE TABLE IF NOT EXISTS pagos (
  id INTEGER PRIMARY KEY, encargo_id INTEGER NOT NULL REFERENCES encargos(id),
  fecha TEXT NOT NULL, importe REAL NOT NULL CHECK (importe > 0), forma_pago TEXT NOT NULL);
"""
ENCARGOS_SQL = """
SELECT e.*, ROUND(COALESCE(SUM(p.importe), 0), 2) AS pagado,
       ROUND(e.precio - COALESCE(SUM(p.importe), 0), 2) AS pendiente
FROM encargos e LEFT JOIN pagos p ON p.encargo_id = e.id
"""


def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def rows(sql, *args):
    with db() as con:
        return [dict(r) for r in con.execute(sql, args)]


def get_encargo(encargo_id):
    found = rows(ENCARGOS_SQL + " WHERE e.id = ? GROUP BY e.id", encargo_id)
    if not found:
        raise HTTPException(404, "Encargo no encontrado")
    return found[0]


AVISOS = deque(maxlen=20)  # los últimos avisos enviados a n8n, para verlos en /avisos


def notify(evento, datos):
    """Avisa a n8n y apunta el aviso para poder verlo. Si n8n no responde, la pastelería sigue funcionando."""
    cuerpo = json.dumps({"evento": evento, "datos": datos}, ensure_ascii=False, indent=2)
    aviso = {"hora": datetime.now().strftime("%H:%M:%S"), "evento": evento, "json": cuerpo, "ok": False}
    AVISOS.appendleft(aviso)
    if not N8N_WEBHOOK_URL:
        aviso["resultado"] = "No se ha enviado: N8N_WEBHOOK_URL está vacío en el .env"
        return
    req = urllib.request.Request(N8N_WEBHOOK_URL, cuerpo.encode(), {"Content-Type": "application/json"})
    try:
        r = urllib.request.urlopen(req, timeout=5)
        aviso["ok"], aviso["resultado"] = True, f"Enviado. n8n respondió {r.status}"
    except urllib.error.HTTPError as e:
        pista = " (ningún flujo publicado escucha esta dirección)" if e.code == 404 else ""
        aviso["resultado"] = f"n8n respondió {e.code}{pista}"
    except Exception as e:
        aviso["resultado"] = f"No se pudo llegar a n8n: {e}"
        log.warning("No se pudo avisar a n8n (%s): %s", evento, e)


# --- Reglas del negocio ---------------------------------------------------------

def crear_encargo(cliente, email, tarta, raciones, precio, fecha_entrega, senal, forma_pago, hoy=None):
    hoy = hoy or date.today()
    if senal < SENAL_MINIMA:
        raise ValueError(f"La señal mínima es de {SENAL_MINIMA} €")
    if senal > precio:
        raise ValueError("La señal no puede superar el precio")
    if forma_pago not in FORMAS_PAGO:
        raise ValueError(f"Forma de pago no válida: {forma_pago}")
    if not hoy < fecha_entrega <= hoy + timedelta(days=MAX_DIAS_ENTREGA):
        raise ValueError(f"La entrega tiene que ser en los próximos {MAX_DIAS_ENTREGA} días")
    with db() as con:
        cur = con.execute(
            "INSERT INTO encargos (fecha, cliente, email, tarta, raciones, precio, fecha_entrega)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (hoy.isoformat(), cliente.strip(), email, tarta.strip(), raciones, precio, fecha_entrega.isoformat()))
        con.execute("INSERT INTO pagos (encargo_id, fecha, importe, forma_pago) VALUES (?, ?, ?, ?)",
                    (cur.lastrowid, hoy.isoformat(), senal, forma_pago))
        if senal == precio:
            con.execute("UPDATE encargos SET estado = 'pagado' WHERE id = ?", (cur.lastrowid,))
    return get_encargo(cur.lastrowid)


def registrar_pago(encargo_id, importe, forma_pago, hoy=None):
    hoy = hoy or date.today()
    encargo = get_encargo(encargo_id)
    if encargo["estado"] == "pagado":
        raise ValueError("El encargo ya está pagado")
    if importe <= 0:
        raise ValueError("El importe debe ser mayor que 0")
    if importe > encargo["pendiente"]:
        raise ValueError(f"El importe supera lo pendiente ({encargo['pendiente']} €)")
    if forma_pago not in FORMAS_PAGO:
        raise ValueError(f"Forma de pago no válida: {forma_pago}")
    with db() as con:
        con.execute("INSERT INTO pagos (encargo_id, fecha, importe, forma_pago) VALUES (?, ?, ?, ?)",
                    (encargo_id, hoy.isoformat(), importe, forma_pago))
        if round(encargo["pendiente"] - importe, 2) == 0:
            con.execute("UPDATE encargos SET estado = 'pagado' WHERE id = ?", (encargo_id,))
    return get_encargo(encargo_id)


# --- API para n8n -----------------------------------------------------------------

# Declarar la cabecera como esquema de seguridad es lo que hace aparecer el botón Authorize en /docs.
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def check_key(x_api_key: str | None = Depends(api_key_header)):
    if not API_KEY or x_api_key != API_KEY:
        raise HTTPException(401, "Falta la cabecera X-API-Key o no es válida")


api = Depends(check_key)


def run(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except ValueError as e:
        raise HTTPException(422, str(e))


class EncargoIn(BaseModel):
    cliente: str
    email: str | None = None
    tarta: str
    raciones: int = Field(gt=0)
    precio: float = Field(gt=0)
    fecha_entrega: date = Field(description="Entre mañana y dentro de 30 días")
    senal: float = Field(description="Mínimo 10 €")
    forma_pago: str = "efectivo"


class PagoIn(BaseModel):
    importe: float
    forma_pago: str = "efectivo"


@app.get("/api/encargos", dependencies=[api], tags=["encargos"], summary="Lista de encargos (filtra por estado)")
def api_encargos(estado: str | None = None):
    if estado:
        return rows(ENCARGOS_SQL + " WHERE e.estado = ? GROUP BY e.id ORDER BY e.fecha_entrega", estado)
    return rows(ENCARGOS_SQL + " GROUP BY e.id ORDER BY e.fecha_entrega")


@app.get("/api/encargos/{encargo_id}", dependencies=[api], tags=["encargos"])
def api_encargo(encargo_id: int):
    return get_encargo(encargo_id) | {"pagos": rows("SELECT * FROM pagos WHERE encargo_id = ? ORDER BY fecha", encargo_id)}


@app.post("/api/encargos", dependencies=[api], tags=["encargos"], status_code=201)
def api_crear_encargo(body: EncargoIn, tasks: BackgroundTasks):
    encargo = run(crear_encargo, **body.model_dump())
    tasks.add_task(notify, "encargo.creado", encargo)
    return encargo


@app.post("/api/encargos/{encargo_id}/pagos", dependencies=[api], tags=["encargos"], status_code=201)
def api_pago(encargo_id: int, body: PagoIn, tasks: BackgroundTasks):
    encargo = run(registrar_pago, encargo_id, **body.model_dump())
    tasks.add_task(notify, "pago.registrado", encargo | {"importe": body.importe})
    return encargo


@app.post("/api/reset", dependencies=[api], tags=["utilidades"],
          summary="Borra todo y vuelve a cargar los datos de ejemplo")
def api_reset():
    with db() as con:
        con.executescript("DROP TABLE IF EXISTS pagos; DROP TABLE IF EXISTS encargos;")
        con.executescript(SCHEMA)
    seed()
    return {"ok": True}


@app.get("/api/pagos", dependencies=[api], tags=["consultas"], summary="Pagos entre dos fechas (incluidas)")
def api_pagos(desde: date | None = None, hasta: date | None = None):
    return rows("SELECT * FROM pagos WHERE fecha BETWEEN ? AND ? ORDER BY fecha, id",
                str(desde or "0000-01-01"), str(hasta or "9999-12-31"))


# --- Pantallas de la pastelería ---------------------------------------------------
# ponytail: sin login, pensada para el ordenador de la tienda. Añadir auth si se publica.

POR_PAGINA = 25
ESTADOS = ["pendiente", "pagado"]


def page(request, name, status_code=200, **ctx):
    ctx = {"formas_pago": FORMAS_PAGO, "error": "", "ok": request.query_params.get("ok", "")} | ctx
    return templates.TemplateResponse(request, name, ctx, status_code=status_code)


def con_dias(encargo):
    """Añade cuántos días quedan hasta la entrega (negativo si ya pasó)."""
    return encargo | {"dias": (date.fromisoformat(encargo["fecha_entrega"]) - date.today()).days}


def paginar(total, pagina):
    paginas = max(1, -(-total // POR_PAGINA))
    pagina = min(max(1, pagina), paginas)
    return pagina, paginas, (pagina - 1) * POR_PAGINA


@app.get("/", include_in_schema=False)
def ui_encargos(request: Request, estado: str = "pendiente", q: str = "", pagina: int = 1):
    where, args = [], []
    if estado in ESTADOS:
        where.append("e.estado = ?")
        args.append(estado)
    if q.strip():
        where.append("(e.cliente LIKE ? OR e.tarta LIKE ? OR CAST(e.id AS TEXT) = ?)")
        args += [f"%{q.strip()}%"] * 2 + [q.strip().lstrip("#")]
    filtro = (" WHERE " + " AND ".join(where)) if where else ""
    total = rows("SELECT COUNT(*) AS n FROM encargos e" + filtro, *args)[0]["n"]
    pagina, paginas, offset = paginar(total, pagina)
    encargos = rows(ENCARGOS_SQL + filtro + f" GROUP BY e.id ORDER BY e.fecha_entrega LIMIT {POR_PAGINA} OFFSET {offset}", *args)
    conteo = {r["estado"]: r["n"] for r in rows("SELECT estado, COUNT(*) AS n FROM encargos GROUP BY estado")}
    return page(request, "encargos.html", encargos=[con_dias(e) for e in encargos], estado=estado, q=q,
                conteo=conteo | {"": sum(conteo.values())}, total=total, pagina=pagina, paginas=paginas)


@app.get("/encargos/nuevo", include_in_schema=False)
def ui_nuevo_encargo(request: Request):
    return page(request, "nuevo_encargo.html", form={})


@app.post("/encargos", include_in_schema=False)
async def ui_crear_encargo(request: Request, tasks: BackgroundTasks):
    form = dict(await request.form())
    try:
        encargo = crear_encargo(form.get("cliente", ""), form.get("email", ""), form.get("tarta", ""),
                                int(form.get("raciones") or 0), float(form.get("precio") or 0),
                                date.fromisoformat(form.get("fecha_entrega") or ""),
                                float(form.get("senal") or 0), form.get("forma_pago", ""))
    except ValueError as e:
        # Se vuelve a mostrar el formulario con lo que se había escrito, para no perderlo.
        return page(request, "nuevo_encargo.html", 422, form=form, error=str(e))
    tasks.add_task(notify, "encargo.creado", encargo)
    return RedirectResponse(f"/encargos/{encargo['id']}?ok=Encargo+creado", 303)


@app.get("/encargos/{encargo_id}", include_in_schema=False)
def ui_encargo(request: Request, encargo_id: int, error: str = ""):
    return page(request, "encargo.html", e=con_dias(get_encargo(encargo_id)), error=error,
                pagos=rows("SELECT * FROM pagos WHERE encargo_id = ? ORDER BY fecha DESC, id DESC", encargo_id))


@app.post("/encargos/{encargo_id}/pagos", include_in_schema=False)
def ui_pago(encargo_id: int, tasks: BackgroundTasks, importe: float = Form(), forma_pago: str = Form()):
    try:
        encargo = registrar_pago(encargo_id, importe, forma_pago)
    except ValueError as e:
        return RedirectResponse(f"/encargos/{encargo_id}?error={urllib.parse.quote(str(e))}", 303)
    tasks.add_task(notify, "pago.registrado", encargo | {"importe": importe})
    ok = "Encargo pagado: ya puede recoger su tarta" if encargo["estado"] == "pagado" else "Pago registrado"
    return RedirectResponse(f"/encargos/{encargo_id}?ok={urllib.parse.quote(ok)}", 303)


@app.get("/pagos", include_in_schema=False)
def ui_pagos(request: Request, pagina: int = 1):
    total = rows("SELECT COUNT(*) AS n FROM pagos")[0]["n"]
    pagina, paginas, offset = paginar(total, pagina)
    pagos = rows("SELECT p.*, e.cliente FROM pagos p JOIN encargos e ON e.id = p.encargo_id "
                 f"ORDER BY p.fecha DESC, p.id DESC LIMIT {POR_PAGINA} OFFSET {offset}")
    return page(request, "pagos.html", pagos=pagos, total=total, pagina=pagina, paginas=paginas)


@app.get("/avisos", include_in_schema=False)
def ui_avisos(request: Request):
    return page(request, "avisos.html", avisos=list(AVISOS), url=N8N_WEBHOOK_URL)


@app.get("/excel", include_in_schema=False)
def excel():
    """Descarga todos los datos en un Excel, una hoja por tabla."""
    wb = Workbook()
    wb.remove(wb.active)
    hojas = {
        "Encargos": (["id", "fecha", "cliente", "email", "tarta", "raciones", "precio", "pagado", "pendiente",
                      "fecha_entrega", "estado"], rows(ENCARGOS_SQL + " GROUP BY e.id ORDER BY e.id")),
        "Pagos": (["id", "encargo_id", "fecha", "importe", "forma_pago"], rows("SELECT * FROM pagos ORDER BY fecha, id")),
    }
    for nombre, (columnas, datos) in hojas.items():
        ws = wb.create_sheet(nombre)
        ws.append(columnas)
        for r in datos:
            ws.append([r[c] for c in columnas])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": f'attachment; filename="la-cuchara-{date.today()}.xlsx"'})


# --- Datos de ejemplo -------------------------------------------------------------

def seed():
    """Encargos de ejemplo con fechas relativas a hoy. Se carga solo si la base está vacía."""
    hoy = date.today()
    # (cliente, tarta, raciones, precio, días desde hoy hasta la entrega, señal, pagos extra)
    ejemplos = [
        ("Carmen Ruiz", "Tarta de queso", 8, 32.0, 3, 10, [10]),
        ("Jorge Martín", "Tarta de chocolate", 12, 48.0, 5, 15, []),
        ("Lucía Gómez", "Tarta de zanahoria", 10, 40.0, 2, 10, [20]),
        ("Ana Torres", "Tarta de limón", 6, 24.0, 7, 24, []),
        ("Laura Ortega", "Tarta red velvet", 10, 45.0, 10, 20, [20]),
        ("Pablo Rubio", "Tarta de fresas", 8, 36.0, 12, 10, []),
        ("Marta Molina", "Tarta Sacher", 14, 62.0, 15, 30, []),
        ("Sergio Delgado", "Tarta de queso", 8, 32.0, 20, 10, []),
    ]
    for i, (cliente, tarta, raciones, precio, dias, senal, extras) in enumerate(ejemplos):
        e = crear_encargo(cliente, f"{cliente.split()[0].lower()}{i + 1}@example.com", tarta, raciones, precio,
                          hoy + timedelta(days=dias), senal, "bizum" if i % 2 else "efectivo", hoy - timedelta(days=6 - i % 5))
        for importe in extras:
            e = registrar_pago(e["id"], importe, "tarjeta", hoy - timedelta(days=2))
    # Movimientos de hoy, para que el cierre diario tenga algo que sumar
    registrar_pago(2, 15, "bizum")
    registrar_pago(6, 10, "efectivo")
    registrar_pago(7, 12, "tarjeta")


with db() as _con:
    _con.executescript(SCHEMA)
if os.getenv("SEED", "1") != "0" and not rows("SELECT 1 FROM encargos LIMIT 1"):
    seed()
