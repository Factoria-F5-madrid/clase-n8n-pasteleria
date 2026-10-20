"""Configuración y reglas del negocio.

Lo que cambia de un ordenador a otro (claves, direcciones) viene del archivo .env.
Las reglas de la pastelería (señal mínima, plazo de entrega...) están aquí, en un solo sitio.
"""

import os
from pathlib import Path

# --- Entorno (.env) ---
DB_PATH = os.getenv("DB_PATH", "pasteleria.db")
API_KEY = os.getenv("API_KEY", "")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "")
SEED = os.getenv("SEED", "1") != "0"
FRONTEND_DIR = Path(os.getenv("FRONTEND_DIR", Path(__file__).resolve().parent.parent / "frontend"))

# --- Reglas del negocio ---
SENAL_MINIMA = 10
MAX_DIAS_ENTREGA = 30
FORMAS_PAGO = ["efectivo", "tarjeta", "bizum", "transferencia"]
