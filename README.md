# Automatiza una pastelería con n8n: del encargo al cierre de caja

Clase práctica para aprender, paso a paso, a hacer lo que pide el **nivel esencial** del proyecto de la zapatería. Aquí se construye con un caso parecido (una pastelería con encargos de tartas) para que, cuando llegue el proyecto, ya hayas hecho cada pieza una vez.

**Duración:** dos sesiones, unas 3 h 50 min en total.

---

## 0. Qué vamos a construir

**Pastelería La Cuchara** vende tartas por encargo. El cliente deja una **señal de al menos 10 €**, paga el resto antes de la entrega (máximo 30 días) y recoge su tarta. Hoy Marisa, la dueña, apunta todo a mano y revisa los avisos del banco para saber quién ha pagado.

Ya tiene una **app** (carpeta `app/`) que guarda los encargos y los pagos. Nosotros no la tocamos: construimos con n8n **todo lo que pasa alrededor**.

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

### Cómo se conecta con el proyecto de la zapatería

| Aquí (pastelería) | En el proyecto (zapatería) | Historia de usuario |
|---|---|---|
| Flujo 01 · confirmar encargo y recibos | Flujos 1 y 2 · confirmación de apartado y recibo de abono | HU-01 y HU-02 |
| Flujo 03 · pagos por correo con IA | Flujo 3 · abonos a distancia | HU-03 |
| Flujo 02 · cierre diario | Flujo 5 · cierre diario | HU-04 |
| Flujo 00 · avisar de errores | Flujo 8 · Error Workflow | HU-05 |

La estructura es idéntica y cambian los nombres: un *encargo* es un *apartado*, un *pago* es un *abono* y "pagado" es "liquidado".

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

## Estructura de este repositorio

```
clase-n8n-pasteleria/
├── README.md              ← esta página (vista general)
├── docker-compose.yml     ← app + n8n + Mailpit
├── .env.example           ← copia a .env
├── app/                   ← la app de la pastelería, con pantallas (no hace falta tocarla)
├── data/correos/          ← los 7 correos de ejemplo de la sesión 2
├── mis-flujos/            ← aquí guardas tus exportaciones de n8n
├── (sesion-1) referencia/ ← flujos 01 y 02 terminados
└── (sesion-2) referencia/ ← flujos 00, 01, 02 y 03 terminados
```
