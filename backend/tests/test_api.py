from datetime import date, timedelta

ENTREGA = (date.today() + timedelta(days=5)).isoformat()
NUEVO = {"cliente": "Carmen Ruiz", "email": "c@example.com", "tarta": "Tarta de queso", "raciones": 8,
         "precio": 32, "fecha_entrega": ENTREGA, "senal": 10, "forma_pago": "bizum"}


def test_la_api_exige_clave(anonimo):
    assert anonimo.get("/api/encargos").status_code == 401


def test_swagger_muestra_authorize(anonimo):
    esquemas = anonimo.get("/openapi.json").json()["components"]["securitySchemes"]
    assert any(e["type"] == "apiKey" and e["name"] == "X-API-Key" for e in esquemas.values())


def test_ciclo_hasta_pagado(cliente):
    e = cliente.post("/api/encargos", json=NUEVO).json()
    assert e["pendiente"] == 22 and e["estado"] == "pendiente"
    assert cliente.post(f"/api/encargos/{e['id']}/pagos", json={"importe": 100}).status_code == 422  # de más
    e = cliente.post(f"/api/encargos/{e['id']}/pagos", json={"importe": 22}).json()
    assert e["pendiente"] == 0 and e["estado"] == "pagado"
    assert cliente.post(f"/api/encargos/{e['id']}/pagos", json={"importe": 1}).status_code == 422


def test_reglas_de_creacion(cliente):
    assert cliente.post("/api/encargos", json=NUEVO | {"senal": 9}).status_code == 422
    assert cliente.post("/api/encargos", json=NUEVO | {"fecha_entrega": date.today().isoformat()}).status_code == 422
    lejos = (date.today() + timedelta(days=31)).isoformat()
    r = cliente.post("/api/encargos", json=NUEVO | {"fecha_entrega": lejos})
    assert r.status_code == 422 and "30 días" in r.json()["detail"]


def test_encargo_inexistente(cliente):
    assert cliente.get("/api/encargos/99999").status_code == 404


def test_lista_con_filtros_y_paginacion(cliente):
    for i in range(3):
        cliente.post("/api/encargos", json=NUEVO | {"cliente": f"Cliente {i}"})
    todos = cliente.get("/api/encargos")
    assert isinstance(todos.json(), list) and int(todos.headers["X-Total-Count"]) == len(todos.json())  # n8n recibe una lista
    pagina = cliente.get("/api/encargos?pagina=1&por_pagina=2")
    assert len(pagina.json()) == 2 and int(pagina.headers["X-Total-Count"]) >= 3
    assert len(cliente.get("/api/encargos?q=Cliente 1").json()) == 1
    resumen = cliente.get("/api/encargos/resumen").json()
    assert resumen["total"] == resumen["pendiente"] + resumen["pagado"]


def test_pagos_por_fecha_con_cliente(cliente):
    hoy = date.today().isoformat()
    pagos = cliente.get(f"/api/pagos?desde={hoy}&hasta={hoy}").json()
    assert pagos and "cliente" in pagos[0]
    desc = cliente.get("/api/pagos?orden=desc&pagina=1&por_pagina=2")
    assert len(desc.json()) == 2 and int(desc.headers["X-Total-Count"]) >= 2


def test_avisos_a_n8n_quedan_apuntados(cliente):
    from services import n8n

    cliente.post("/api/encargos", json=NUEVO)  # con N8N_WEBHOOK_URL vacío no se envía, pero queda apuntado
    assert n8n.AVISOS[0]["evento"] == "encargo.creado" and "vacío" in n8n.AVISOS[0]["resultado"]
    r = cliente.get("/api/avisos").json()
    assert r["avisos"][0]["evento"] == "encargo.creado" and "encargo.creado" in r["avisos"][0]["json_enviado"]


def test_excel_es_un_xlsx(cliente):
    assert cliente.get("/api/excel").content[:2] == b"PK"  # un xlsx es un zip
