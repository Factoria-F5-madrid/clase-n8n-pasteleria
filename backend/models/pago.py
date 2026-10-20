"""MODELO · Pago: los pagos de cada encargo y las reglas para registrarlos."""

from datetime import date

import config
import database
from models import encargo
from models.errores import ReglaDeNegocio


def de_encargo(encargo_id):
    return database.consultar("SELECT * FROM pagos WHERE encargo_id = ? ORDER BY fecha, id", encargo_id)


def listar(desde=None, hasta=None, descendente=False, limite=None, desplazamiento=0):
    """Devuelve (pagos, total) entre dos fechas (incluidas), con el nombre del cliente."""
    args = [str(desde or "0000-01-01"), str(hasta or "9999-12-31")]
    total = database.consultar("SELECT COUNT(*) AS n FROM pagos WHERE fecha BETWEEN ? AND ?", *args)[0]["n"]
    sql = ("SELECT p.*, e.cliente FROM pagos p JOIN encargos e ON e.id = p.encargo_id WHERE p.fecha BETWEEN ? AND ? "
           f"ORDER BY p.fecha {'DESC' if descendente else 'ASC'}, p.id {'DESC' if descendente else 'ASC'}")
    if limite:
        sql += " LIMIT ? OFFSET ?"
        args += [limite, desplazamiento]
    return database.consultar(sql, *args), total


def registrar(encargo_id, importe, forma_pago, hoy=None):
    hoy = hoy or date.today()
    actual = encargo.obtener(encargo_id)
    if actual["estado"] == "pagado":
        raise ReglaDeNegocio("El encargo ya está pagado")
    if importe <= 0:
        raise ReglaDeNegocio("El importe debe ser mayor que 0")
    if importe > actual["pendiente"]:
        raise ReglaDeNegocio(f"El importe supera lo pendiente ({actual['pendiente']} €)")
    if forma_pago not in config.FORMAS_PAGO:
        raise ReglaDeNegocio(f"Forma de pago no válida: {forma_pago}")
    with database.conectar() as con:
        con.execute("INSERT INTO pagos (encargo_id, fecha, importe, forma_pago) VALUES (?, ?, ?, ?)",
                    (encargo_id, hoy.isoformat(), importe, forma_pago))
        if round(actual["pendiente"] - importe, 2) == 0:
            con.execute("UPDATE encargos SET estado = 'pagado' WHERE id = ?", (encargo_id,))
    return encargo.obtener(encargo_id)
