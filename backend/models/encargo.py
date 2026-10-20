"""MODELO · Encargo: los datos de un encargo de tarta y las reglas para crearlo."""

from datetime import date, timedelta

import config
import database
from models.errores import NoEncontrado, ReglaDeNegocio

# Cada encargo con lo pagado y lo pendiente, calculados a partir de sus pagos.
SELECT = """
SELECT e.*, ROUND(COALESCE(SUM(p.importe), 0), 2) AS pagado,
       ROUND(e.precio - COALESCE(SUM(p.importe), 0), 2) AS pendiente
FROM encargos e LEFT JOIN pagos p ON p.encargo_id = e.id
"""


def obtener(encargo_id):
    encontrados = database.consultar(SELECT + " WHERE e.id = ? GROUP BY e.id", encargo_id)
    if not encontrados:
        raise NoEncontrado("Encargo no encontrado")
    return encontrados[0]


def listar(estado=None, q="", limite=None, desplazamiento=0):
    """Devuelve (encargos, total). `q` busca por cliente, tarta o número de encargo."""
    condiciones, args = [], []
    if estado:
        condiciones.append("e.estado = ?")
        args.append(estado)
    if q.strip():
        condiciones.append("(e.cliente LIKE ? OR e.tarta LIKE ? OR CAST(e.id AS TEXT) = ?)")
        args += [f"%{q.strip()}%"] * 2 + [q.strip().lstrip("#")]
    filtro = (" WHERE " + " AND ".join(condiciones)) if condiciones else ""
    total = database.consultar("SELECT COUNT(*) AS n FROM encargos e" + filtro, *args)[0]["n"]
    sql = SELECT + filtro + " GROUP BY e.id ORDER BY e.fecha_entrega"
    if limite:
        sql += " LIMIT ? OFFSET ?"
        args += [limite, desplazamiento]
    return database.consultar(sql, *args), total


def contar_por_estado():
    cuentas = {f["estado"]: f["n"] for f in database.consultar("SELECT estado, COUNT(*) AS n FROM encargos GROUP BY estado")}
    return {"pendiente": cuentas.get("pendiente", 0), "pagado": cuentas.get("pagado", 0), "total": sum(cuentas.values())}


def crear(cliente, email, tarta, raciones, precio, fecha_entrega, senal, forma_pago, hoy=None):
    hoy = hoy or date.today()
    if senal < config.SENAL_MINIMA:
        raise ReglaDeNegocio(f"La señal mínima es de {config.SENAL_MINIMA} €")
    if senal > precio:
        raise ReglaDeNegocio("La señal no puede superar el precio")
    if forma_pago not in config.FORMAS_PAGO:
        raise ReglaDeNegocio(f"Forma de pago no válida: {forma_pago}")
    if not hoy < fecha_entrega <= hoy + timedelta(days=config.MAX_DIAS_ENTREGA):
        raise ReglaDeNegocio(f"La entrega tiene que ser en los próximos {config.MAX_DIAS_ENTREGA} días")
    with database.conectar() as con:
        cur = con.execute(
            "INSERT INTO encargos (fecha, cliente, email, tarta, raciones, precio, fecha_entrega)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (hoy.isoformat(), cliente.strip(), email, tarta.strip(), raciones, precio, fecha_entrega.isoformat()))
        con.execute("INSERT INTO pagos (encargo_id, fecha, importe, forma_pago) VALUES (?, ?, ?, ?)",
                    (cur.lastrowid, hoy.isoformat(), senal, forma_pago))
        if senal == precio:
            con.execute("UPDATE encargos SET estado = 'pagado' WHERE id = ?", (cur.lastrowid,))
    return obtener(cur.lastrowid)
