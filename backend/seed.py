"""Datos de ejemplo: encargos con fechas relativas a hoy, para que siempre haya algo que mostrar y sumar."""

from datetime import date, timedelta

from models import encargo, pago

# (cliente, tarta, raciones, precio, días desde hoy hasta la entrega, señal, pagos extra)
EJEMPLOS = [
    ("Carmen Ruiz", "Tarta de queso", 8, 32.0, 3, 10, [10]),
    ("Jorge Martín", "Tarta de chocolate", 12, 48.0, 5, 15, []),
    ("Lucía Gómez", "Tarta de zanahoria", 10, 40.0, 2, 10, [20]),
    ("Ana Torres", "Tarta de limón", 6, 24.0, 7, 24, []),
    ("Laura Ortega", "Tarta red velvet", 10, 45.0, 10, 20, [20]),
    ("Pablo Rubio", "Tarta de fresas", 8, 36.0, 12, 10, []),
    ("Marta Molina", "Tarta Sacher", 14, 62.0, 15, 30, []),
    ("Sergio Delgado", "Tarta de queso", 8, 32.0, 20, 10, []),
]


def cargar():
    hoy = date.today()
    for i, (cliente, tarta, raciones, precio, dias, senal, extras) in enumerate(EJEMPLOS):
        nuevo = encargo.crear(cliente, f"{cliente.split()[0].lower()}{i + 1}@example.com", tarta, raciones, precio,
                              hoy + timedelta(days=dias), senal, "bizum" if i % 2 else "efectivo",
                              hoy - timedelta(days=6 - i % 5))
        for importe in extras:
            pago.registrar(nuevo["id"], importe, "tarjeta", hoy - timedelta(days=2))
    # Movimientos de hoy, para que el cierre diario tenga algo que sumar
    pago.registrar(2, 15, "bizum")
    pago.registrar(6, 10, "efectivo")
    pago.registrar(7, 12, "tarjeta")
