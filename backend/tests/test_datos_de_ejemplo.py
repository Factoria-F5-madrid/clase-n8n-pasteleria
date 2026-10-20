from datetime import date

import config
import database
import seed


def test_los_datos_de_ejemplo_cuadran_con_los_correos(cliente, monkeypatch, tmp_path):
    """data/correos/ cuenta con estos encargos concretos."""
    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "seed.db"))
    database.crear_tablas()
    seed.cargar()
    por_id = {e["id"]: e for e in cliente.get("/api/encargos").json()}
    assert por_id[1]["cliente"] == "Carmen Ruiz" and por_id[1]["pendiente"] == 12
    assert por_id[2]["pendiente"] == 18 and por_id[3]["pendiente"] == 10
    assert por_id[4]["estado"] == "pagado" and por_id[5]["pendiente"] == 5
    hoy = date.today().isoformat()
    assert len(cliente.get(f"/api/pagos?desde={hoy}&hasta={hoy}").json()) == 3  # el cierre diario tiene algo que sumar


def test_reset_vuelve_a_los_datos_de_ejemplo(cliente, anonimo):
    assert anonimo.post("/api/reset").status_code == 401
    assert cliente.post("/api/reset").json() == {"ok": True}
    assert len(cliente.get("/api/encargos").json()) == 8 and cliente.get("/api/encargos/1").json()["pendiente"] == 12
