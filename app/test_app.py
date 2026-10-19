import os
import tempfile
from datetime import date, timedelta

os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ["API_KEY"] = "test"
os.environ["N8N_WEBHOOK_URL"] = ""

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402

c = TestClient(app, headers={"X-API-Key": "test"})
MANANA = (date.today() + timedelta(days=5)).isoformat()
NUEVO = {"cliente": "Test Cliente", "email": "t@example.com", "tarta": "Tarta de queso", "raciones": 8, "precio": 32,
         "fecha_entrega": MANANA, "senal": 10, "forma_pago": "bizum"}


def test_requiere_api_key():
    assert TestClient(app).get("/api/encargos").status_code == 401


def test_ciclo_hasta_pagado():
    e = c.post("/api/encargos", json=NUEVO).json()
    assert e["pendiente"] == 22 and e["estado"] == "pendiente"
    assert c.post(f"/api/encargos/{e['id']}/pagos", json={"importe": 100}).status_code == 422  # de más
    e = c.post(f"/api/encargos/{e['id']}/pagos", json={"importe": 22}).json()
    assert e["pendiente"] == 0 and e["estado"] == "pagado"
    assert c.post(f"/api/encargos/{e['id']}/pagos", json={"importe": 1}).status_code == 422


def test_reglas_de_creacion():
    assert c.post("/api/encargos", json=NUEVO | {"senal": 9}).status_code == 422
    assert c.post("/api/encargos", json=NUEVO | {"fecha_entrega": date.today().isoformat()}).status_code == 422
    lejos = (date.today() + timedelta(days=31)).isoformat()
    assert c.post("/api/encargos", json=NUEVO | {"fecha_entrega": lejos}).status_code == 422


def test_pagos_por_fecha():
    hoy = date.today().isoformat()
    assert len(c.get(f"/api/pagos?desde={hoy}&hasta={hoy}").json()) >= 1


def test_pantallas():
    assert c.get("/").status_code == 200
    assert c.get("/encargos/nuevo").status_code == 200
    r = c.post("/encargos", data={k: str(v) for k, v in NUEVO.items()} | {"senal": "2"})
    assert r.status_code == 422 and "señal mínima" in r.text and "Test Cliente" in r.text  # no se pierde lo escrito
    r = c.post("/encargos", data={k: str(v) for k, v in NUEVO.items()}, follow_redirects=True)
    assert r.status_code == 200 and "Encargo creado" in r.text
    assert c.get("/?estado=&q=Test&pagina=99").status_code == 200
    assert c.get("/pagos").status_code == 200 and c.get("/excel").content[:2] == b"PK"  # xlsx es un zip


def test_datos_de_ejemplo():
    import main

    main.DB_PATH = os.path.join(tempfile.mkdtemp(), "seed.db")
    with main.db() as con:
        con.executescript(main.SCHEMA)
    main.seed()
    por_id = {e["id"]: e for e in c.get("/api/encargos").json()}
    # Los correos de data/correos/ cuentan con estos encargos
    assert por_id[1]["cliente"] == "Carmen Ruiz" and por_id[1]["pendiente"] == 12
    assert por_id[2]["pendiente"] == 18 and por_id[3]["pendiente"] == 10
    assert por_id[4]["estado"] == "pagado" and por_id[5]["pendiente"] == 5
    hoy = date.today().isoformat()
    assert len(c.get(f"/api/pagos?desde={hoy}&hasta={hoy}").json()) == 3  # el cierre diario tiene algo que sumar


def test_reset_vuelve_a_los_datos_de_ejemplo():
    assert TestClient(app).post("/api/reset").status_code == 401
    assert c.post("/api/reset").json() == {"ok": True}
    assert len(c.get("/api/encargos").json()) == 8 and c.get("/api/encargos/1").json()["pendiente"] == 12
