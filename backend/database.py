"""Conexión a la base de datos (SQLite) y creación de las tablas."""

import sqlite3

import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS encargos (
  id INTEGER PRIMARY KEY, fecha TEXT NOT NULL, cliente TEXT NOT NULL, email TEXT,
  tarta TEXT NOT NULL, raciones INTEGER NOT NULL, precio REAL NOT NULL, fecha_entrega TEXT NOT NULL,
  estado TEXT NOT NULL DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'pagado')));
CREATE TABLE IF NOT EXISTS pagos (
  id INTEGER PRIMARY KEY, encargo_id INTEGER NOT NULL REFERENCES encargos(id),
  fecha TEXT NOT NULL, importe REAL NOT NULL CHECK (importe > 0), forma_pago TEXT NOT NULL);
"""


def conectar():
    con = sqlite3.connect(config.DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def consultar(sql, *args):
    """Ejecuta un SELECT y devuelve una lista de diccionarios."""
    with conectar() as con:
        return [dict(fila) for fila in con.execute(sql, args)]


def crear_tablas():
    with conectar() as con:
        con.executescript(SCHEMA)


def vaciar():
    with conectar() as con:
        con.executescript("DROP TABLE IF EXISTS pagos; DROP TABLE IF EXISTS encargos;")
    crear_tablas()


def esta_vacia():
    return not consultar("SELECT 1 FROM encargos LIMIT 1")
