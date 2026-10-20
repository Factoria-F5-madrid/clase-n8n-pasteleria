# Automatiza una pastelería con n8n: del encargo al cierre de caja

Clase práctica para aprender, paso a paso, a automatizar un negocio pequeño con n8n: desde encender n8n con Docker hasta tener flujos reales funcionando, con un agente de IA ayudando.

**Duración:** dos sesiones, unas 3 h 50 min en total.

---

## 0. Qué vamos a construir

**Pastelería La Cuchara** vende tartas por encargo. El cliente deja una **señal de al menos 10 €**, paga el resto antes de la entrega (máximo 30 días) y recoge su tarta. Hoy Marisa, la dueña, apunta todo a mano y revisa los avisos del banco para saber quién ha pagado.

Ya tiene una **app** (carpetas `backend/` y `frontend/`) que guarda los encargos y los pagos. Nosotros no la tocamos: construimos con n8n **todo lo que pasa alrededor**.

```
                  La app avisa a n8n cuando pasa algo
 App (8000)  ───────────────────────────────────────────▶  n8n (5678)
 encargos y pagos                                           │
     ▲                                                      ├─ ① Flujo 01: confirma el encargo y manda recibos
     │                                                      ├─ ② Flujo 02: cada noche, el cierre de caja
     │   n8n consulta y registra pagos con la API           ├─ ③ Flujo 03: lee los correos del banco con IA
     └──────────────────────────────────────────────────────┤        y registra el pago en el encargo
                                                            └─ ④ Flujo 00: si algo falla, avisa a Marisa

                         Todos los correos salen a Mailpit (8025), un buzón de pruebas
```

### La idea en una frase

> **n8n es un empleado que sigue recetas.** Cada **flujo** (workflow) es una receta: tiene algo que la **activa** (el timbre de la tienda o el reloj de la cocina), unos **pasos** (nodos) y un **resultado**. Lo que pasa de un paso al siguiente son los **ingredientes** (los datos, que n8n llama *items*).

| En n8n | En simple | En la pastelería |
|---|---|---|
| Flujo (*workflow*) | Una receta | "Cuando haya un encargo nuevo, avisa al cliente" |
| Disparador (*trigger*) | Lo que pone la receta en marcha | El timbre (un aviso de la app) o el reloj (las 21:00) |
| Nodo | Un paso de la receta | "Enviar correo", "Sumar importes" |
| Item | Un ingrediente que pasa de paso en paso | Un encargo, un pago |
| Credencial | La llave guardada para usar un servicio | La clave de la app o el acceso al correo |

### Los cuatro flujos que vas a construir

| Flujo | Qué hace | Sesión |
|---|---|---|
| **01** Eventos de la pastelería | Cuando la app avisa, manda al cliente la confirmación del encargo y los recibos de pago | 1 |
| **02** Cierre diario | Cada noche suma lo cobrado en el día y se lo manda a Marisa | 1 |
| **00** Avisar de errores | Si un flujo falla, avisa a Marisa con el motivo | 2 |
| **03** Pagos por correo | Lee los avisos del banco con IA y registra cada pago en su encargo | 2 |

---

## 1. Cómo está organizada la clase

Son **dos sesiones**, cada una en **su propia rama** de este repositorio. La rama trae la guía de esa sesión (en su `README.md`) y los archivos de referencia que necesita.

| Sesión | Rama | Pasos | Duración | Al terminar tienes funcionando |
|---|---|---|---|---|
| **1** | `sesion-1` | 1 a 5 | ~1 h 50 | Todo levantado y conectado, los **avisos al cliente** (flujo 01) y el **cierre de caja** (flujo 02) |
| **2** | `sesion-2` | 6 a 9 | ~2 h | **Aviso de errores** (flujo 00), **pagos por correo con IA** (flujo 03), un flujo hecho con el agente y todo subido a tu repositorio |

**Cómo empezar cada sesión:**

```bash
git clone https://github.com/Factoria-F5-madrid/clase-n8n-pasteleria.git clase-n8n-pasteleria
cd clase-n8n-pasteleria
git switch sesion-1          # y en la segunda sesión: git switch sesion-2
```

Después abre el `README.md` de tu rama y sigue los pasos.

**Tres cosas que conviene saber:**

| Tema | Cómo funciona |
|---|---|
| **Tus flujos** | Viven dentro de n8n (en su volumen de Docker), **no en la rama**. Cambiar de rama no los toca. Lo que **sí** los borra es `docker compose down -v` |
| **Tus exportaciones** | Guárdalas en la carpeta `mis-flujos/`. Es tuya: las ramas no la modifican |
| **Si te atascas o faltaste a la sesión 1** | La carpeta `referencia/` de cada rama trae los flujos terminados para importarlos y seguir |

---

## 2. Antes de empezar

- [ ] **Docker Desktop** instalado y abierto (`docker --version`).
- [ ] **Git** instalado (`git --version`).
- [ ] Una cuenta gratuita en **[console.groq.com](https://console.groq.com)** y una **API key** creada (*API Keys → Create API Key*). Se usa en el Paso 3 (credencial) y se aprovecha en la sesión 2.
- [ ] Un editor (VS Code) y, opcional, **OpenCode** para el Paso 8.

> **No necesitas** cuenta de Gmail, de Slack ni de Telegram. Los correos van a **Mailpit**, un buzón de pruebas que corre en tu ordenador y que te deja ver cada correo que manda n8n.

---

## Cómo está hecha la app (por si tienes curiosidad)

No tienes que tocarla, pero conviene entenderla porque **n8n va a hablar con ella**. Sigue el patrón **MVC**, que separa tres responsabilidades. Piensa en un restaurante:

| Pieza | Carpeta | En el restaurante | Qué hace |
|---|---|---|---|
| **M**odelo | `backend/models/`, `backend/database.py` | La cocina | Guarda los datos y aplica las reglas (señal mínima de 10 €, entrega en 30 días...) |
| Schemas | `backend/schemas/` | La comanda | La forma exacta de los datos que entran y salen (con Pydantic) |
| **C**ontrolador | `backend/controllers/` | El camarero | Recibe la petición HTTP, se la pasa a la cocina y devuelve la respuesta |
| **V**ista | `frontend/` | El comedor y la carta | Lo que ve y usa la dependienta: HTML, CSS y JavaScript |
| `main.py` | `backend/main.py` | El encargado | Solo junta las piezas, no tiene lógica |

La idea clave: **la interfaz no tiene reglas ni toca la base de datos**. Pide todo a la API, igual que lo hará n8n. Es como si la pantalla y n8n fueran dos clientes del mismo camarero:

```
 Pantalla (frontend/) ─┐
                       ├──▶ API (controllers/) ──▶ models/ ──▶ base de datos
 n8n ──────────────────┘
```

Por eso la carpeta se llama `frontend/` y no `templates/`: no son plantillas que rellena el servidor, es una interfaz que **consulta la API**.

---

## Estructura de este repositorio

```
clase-n8n-pasteleria/
├── README.md              ← esta página (vista general)
├── docker-compose.yml     ← app + n8n + Mailpit
├── .env.example           ← copia a .env
├── backend/               ← la lógica de la app (no hace falta tocarla)
│   ├── main.py            ← junta las piezas
│   ├── models/            ← M: datos y reglas del negocio
│   ├── schemas/           ← la forma de los datos (Pydantic)
│   ├── controllers/       ← C: las rutas de la API
│   ├── services/          ← los avisos a n8n
│   └── tests/
├── frontend/              ← V: la interfaz (HTML, CSS y JavaScript)
├── Dockerfile             ← construye backend + frontend en una sola imagen
├── data/correos/          ← los 7 correos de ejemplo de la sesión 2
├── mis-flujos/            ← aquí guardas tus exportaciones de n8n
├── (sesion-1) referencia/ ← flujos 01 y 02 terminados
└── (sesion-2) referencia/ ← flujos 00, 01, 02 y 03 terminados
```
