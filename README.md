# Sesión 1 · Avisos al cliente y cierre de caja

> Estás en la rama **`sesion-1`**. La vista general de la clase está en `main`. Al terminar, pasa a la rama `sesion-2`.

**Duración:** ~1 h 45 min · **Pasos 1 a 5** · **Flujos 01 y 02**

**Antes de empezar:** Docker abierto, Git, y tu API key de Groq creada (ver `main`, apartado 2). Si no tienes el repositorio clonado:

```bash
git clone <url-de-este-repositorio> clase-n8n-pasteleria && cd clase-n8n-pasteleria && git switch sesion-1
```

**Qué vas a hacer:** levantar la pastelería y n8n, conectarlos y construir dos flujos: uno que **reacciona** cuando la app avisa (confirmar el encargo y mandar recibos) y otro que se **despierta solo** cada noche (el cierre de caja).

---

## Paso 1 — Levantar todo con Docker (10 min)

```bash
cd clase-guia-n8n-pasteleria
cp .env.example .env
docker compose up -d
```

Se levantan tres contenedores (la app tiene dos direcciones):

| Servicio | URL | Para qué |
|---|---|---|
| App de la pastelería | http://localhost:8000 | La pantalla de Marisa: encargos, pagos y descarga en Excel |
| API de la app | http://localhost:8000/docs | Lo que usará n8n, documentado en Swagger |
| n8n | http://localhost:5678 | Donde construimos los flujos |
| Mailpit | http://localhost:8025 | El buzón donde llegan todos los correos |

La primera vez que abras n8n te pide **crear una cuenta de propietario** (es local, solo para tu instancia). Pon lo que quieras. Después salen dos ventanas opcionales (un cuestionario y una oferta de licencia): cierra la primera con **Get started** sin responder y la segunda con **Skip**.

**Checkpoint:** las cuatro URLs abren. En Mailpit todavía no hay ningún correo.

---

## Paso 2 — Conocer la app (15 min)

La app es el **mostrador** de la pastelería: ahí se apuntan encargos y pagos. n8n no la sustituye, trabaja detrás.

**La pantalla** — http://localhost:8000

1. En **Encargos** verás los 8 de ejemplo, con lo **pagado** y lo **pendiente** de cada uno, y un aviso de color cuando la entrega está cerca. Prueba el buscador y las pestañas *Pendientes / Pagados / Todos*.
2. Abre un encargo (por ejemplo el #3): ves lo pagado, una barra de progreso y la lista de pagos.
3. En **Pagos** está el historial completo. **Descargar Excel** baja todos los datos en una hoja por tabla.
4. Pulsa **Nuevo encargo**, intenta guardarlo con una señal de **5 €** y mira cómo la app lo rechaza **sin perder lo que escribiste**. Luego créalo bien.

**Las reglas** que aplica la app (tú no las programas, las usas):

| Regla | Detalle |
|---|---|
| Señal | Mínimo **10 €** al crear el encargo |
| Entrega | Entre mañana y dentro de **30 días** |
| Pagos | Se puede pagar en partes, pero **nunca más de lo que falta** |
| Pagado | Cuando lo pendiente llega a 0 €, el encargo pasa a `pagado` |

**La API** — http://localhost:8000/docs

Es lo que usará n8n. Pulsa **Authorize** (arriba a la derecha) y escribe el valor de `API_KEY` de tu `.env` (`cambia-esta-clave`). Prueba `GET /api/encargos` (**Try it out → Execute**): los mismos encargos, pero como datos.

**El aviso a n8n.** Cada vez que se crea un encargo o se registra un pago, desde la pantalla **o** desde la API, la app envía un aviso (*webhook*) a n8n con este formato:

```json
{
  "evento": "pago.registrado",
  "datos": { "id": 3, "cliente": "Lucía Gómez", "email": "lucia3@example.com", "tarta": "Tarta de zanahoria",
             "precio": 40.0, "pagado": 30.0, "pendiente": 10.0, "estado": "pendiente",
             "fecha_entrega": "2026-10-21", "importe": 10.0 }
}
```

Hay **dos eventos**: `encargo.creado` y `pago.registrado`. Ahora mismo nadie los escucha: eso lo arreglamos en el Paso 4.

**Checkpoint:** has creado un encargo desde la pantalla, has visto la lista en Swagger y has entendido que la app avisa pero no envía correos.

---

## Paso 3 — Crear las credenciales (10 min)

Las **credenciales** son las llaves que n8n guarda cifradas para usar servicios. Así **nunca escribimos una clave dentro de un nodo** (y no acaba en GitHub).

En n8n: **menú lateral → Credentials → Create credential** (o *Create → Credential*). Crea estas tres:

| Tipo (búscalo por este nombre) | Nombre | Qué rellenar |
|---|---|---|
| **SMTP** | `Mailpit` | Host `mailpit` · Port `1025` (cambia el 465 que viene por defecto) · User y Password **vacíos** · **SSL/TLS desactivado** (viene activado) · deja *Disable STARTTLS* como está |
| **Header Auth** | `API Pastelería` | Name `X-API-Key` · Value: tu `API_KEY` del `.env` |
| **Groq** | `Groq` | Tu API key de Groq |

> **Ojo con `localhost`:** n8n corre dentro de Docker. Para él, `localhost` es **su propio contenedor**. Para hablar con otro contenedor usa su nombre: `mailpit`, `pasteleria`. Por eso el host es `mailpit` y más adelante la app será `http://pasteleria:8000`.

**Checkpoint:** las tres credenciales aparecen en la lista. (Si al guardar SMTP hay botón de *Test*, debe salir en verde.)

---

## Paso 4 — Flujo 01: confirmar encargos y mandar recibos (40 min)

**Objetivo:** cuando la app avise de un evento, enviar el correo adecuado al cliente.

```
 Webhook ──▶ Switch ──┬── encargo.creado ───▶ Correo: "Tu encargo está confirmado"
                      └── pago.registrado ──▶ IF ¿queda pagado? ──┬── sí ──▶ Correo: "Ya está pagado"
                                                                  └── no ──▶ Correo: "Recibo, te quedan X €"
```

### 4.1 Crear el flujo y el disparador

1. **Create workflow** (esquina superior). Ponle nombre arriba: `01 Eventos de la pastelería`.
2. **Add first step** → busca **Webhook** y añádelo. Configúralo:

| Campo | Valor |
|---|---|
| HTTP Method | `POST` |
| Path | `pasteleria` |
| Respond | `Immediately` |

Renombra el nodo a `Evento de la pastelería` (clic en el nombre o `F2`).

> **Dos URLs, una trampa.** El nodo muestra una **Test URL** (`/webhook-test/pasteleria`) y una **Production URL** (`/webhook/pasteleria`). La **Test URL** solo funciona unos segundos, cuando pulsas *Listen for test event* o *Execute workflow*. La **Production URL** solo funciona cuando el flujo está **publicado**. La app usa la de producción.

### 4.2 Probar con un evento de mentira

Para desarrollar sin tocar la app, simulamos el aviso con `curl`. En n8n, pulsa **Listen for test event** (o *Execute step*) en el nodo Webhook y **en los siguientes 2 minutos** ejecuta en tu terminal:

```bash
curl -X POST http://localhost:5678/webhook-test/pasteleria \
  -H "Content-Type: application/json" \
  -d '{"evento":"encargo.creado","datos":{"id":99,"cliente":"Ana Prueba","email":"ana@example.com","tarta":"Tarta de queso","raciones":8,"precio":32,"pagado":10,"pendiente":22,"estado":"pendiente","fecha_entrega":"2026-12-01"}}'
```

El nodo se llena con el aviso. Fíjate en la pestaña **Output**: los datos están en `body.evento` y `body.datos`. **Anota esto: el JSON que envía la app está dentro de `body`.**

### 4.3 Repartir según el evento (Switch)

1. Añade un nodo **Switch** conectado al Webhook. Renómbralo `Según el evento`.
2. **Mode:** `Rules`. Crea dos reglas:

| Regla | Value 1 (expresión) | Operador | Value 2 | Renombrar salida a |
|---|---|---|---|---|
| 1 | `{{ $json.body.evento }}` | String → is equal to | `encargo.creado` | `encargo.creado` |
| 2 | `{{ $json.body.evento }}` | String → is equal to | `pago.registrado` | `pago.registrado` |

> Para escribir una **expresión**, en el campo pulsa *Expression* (o escribe `{{`). Todo lo que va entre `{{ }}` es JavaScript que n8n calcula para cada item.

Pulsa **Execute step**: con el evento `encargo.creado` el item sale por la salida 1.

### 4.4 Correo de confirmación

En la salida `encargo.creado` añade el nodo **Send Email** (el de *Send email*, con el sobre). Renómbralo `Confirmar encargo`:

| Campo | Valor |
|---|---|
| Credential | `Mailpit` |
| From Email | `pasteleria@lacuchara.example` |
| To Email | `{{ $json.body.datos.email }}` |
| Subject | `Tu encargo #{{ $json.body.datos.id }} está confirmado` |
| Email Format | `Text` |
| Text | ver abajo |

```
Hola {{ $json.body.datos.cliente }},

Hemos apuntado tu encargo: {{ $json.body.datos.tarta }} para {{ $json.body.datos.raciones }} raciones.

Precio: {{ $json.body.datos.precio.toFixed(2) }} €
Pagado: {{ $json.body.datos.pagado.toFixed(2) }} €
Pendiente: {{ $json.body.datos.pendiente.toFixed(2) }} €
Entrega: {{ $json.body.datos.fecha_entrega }}

Pastelería La Cuchara
```

En **Options** (*Add option*) desactiva **Append n8n Attribution** para que no añada la firma de n8n.

Pulsa **Execute step** y abre **Mailpit** (http://localhost:8025): el correo debe estar allí.

> **Los importes los da la app, nunca los calculamos nosotros.** `toFixed(2)` solo los muestra con dos decimales.

### 4.5 Recibo de pago o "ya está pagado" (IF)

Conecta la salida `pago.registrado` del Switch a un nodo **IF** llamado `¿Queda pagado?`:

| Campo | Valor |
|---|---|
| Value 1 | `{{ $json.body.datos.estado }}` |
| Operador | String → is equal to |
| Value 2 | `pagado` |

Ahora **dos** nodos **Send Email** (credencial `Mailpit`, mismo remitente, `To` = `{{ $json.body.datos.email }}`):

- Salida **true** → `Tarta lista para recoger`
  - Subject: `Tu encargo #{{ $json.body.datos.id }} está pagado`
  - Text: `Hola {{ $json.body.datos.cliente }}, hemos recibido {{ $json.body.datos.importe.toFixed(2) }} € y tu encargo ya está pagado por completo. Te esperamos el {{ $json.body.datos.fecha_entrega }} para recoger tu {{ $json.body.datos.tarta }}.`
- Salida **false** → `Recibo de pago`
  - Subject: `Recibo de tu pago del encargo #{{ $json.body.datos.id }}`
  - Text: `Hola {{ $json.body.datos.cliente }}, hemos recibido {{ $json.body.datos.importe.toFixed(2) }} €. Te quedan por pagar {{ $json.body.datos.pendiente.toFixed(2) }} € antes de la entrega ({{ $json.body.datos.fecha_entrega }}).`

Prueba el IF con dos `curl` (con *Listen for test event* activo antes de cada uno): uno con `"evento":"pago.registrado"` y `"estado":"pagado"`, y otro con `"estado":"pendiente"`. Cada uno debe seguir una rama distinta. (Añade `"importe":10` dentro de `datos` en ambos.)

### 4.6 Publicar y probar con la app de verdad

1. Pulsa **Publish** (arriba a la derecha). Un flujo publicado escucha la **Production URL** sin que tengas que pulsar nada.
2. En la app (http://localhost:8000) pulsa **Nuevo encargo**. Pon tu nombre, un correo inventado (`tu@correo.example`), una tarta de 30 €, una fecha de entrega entre mañana y dentro de 30 días y una señal de 10 €.
3. En Mailpit llega **«Tu encargo #9 está confirmado»**.
4. En la ficha del encargo, **Registrar pago** de 10 €: llega el **recibo**. Registra otros 10 €: ahora faltan 10 € todavía. Registra los últimos 10 €: el encargo queda pagado y llega **«Tu encargo está pagado»**.
5. Mira la pestaña **Executions** del flujo: cada aviso es una ejecución, con sus datos.

**Checkpoint:** tres correos distintos en Mailpit y tres ejecuciones verdes. Este flujo es el 80 % de las historias HU-01 y HU-02.

---

## Paso 5 — Flujo 02: el cierre de caja de cada noche (30 min)

**Objetivo:** cada noche, sumar lo cobrado en el día por forma de pago y mandárselo a Marisa. Este flujo **no lo activa un aviso de la app**, sino el **reloj**.

```
 Cada noche 21:00 ──▶ HTTP: pagos de hoy ──▶ Code: sumar por forma de pago ──▶ Correo a Marisa
```

1. Nuevo flujo: `02 Cierre diario`.
2. **Schedule Trigger** → renómbralo `Cada noche a las 21:00`: Trigger Interval `Days`, Days Between Triggers `1`, Trigger at Hour `9pm`.
3. Nodo **HTTP Request** llamado `Pagos de hoy`:

| Campo | Valor |
|---|---|
| Method | `GET` |
| URL | `http://pasteleria:8000/api/pagos` |
| Authentication | `Generic Credential Type` → Generic Auth Type `Header Auth` → Credential `API Pastelería` |
| Send Query Parameters | activado |
| Query `desde` | `{{ $now.format('yyyy-MM-dd') }}` |
| Query `hasta` | `{{ $now.format('yyyy-MM-dd') }}` |

   En **Settings** del nodo (pestaña con el engranaje) activa **Always Output Data**. Sin esto, si hoy no hay ningún pago, el flujo se **para en seco** y Marisa no recibe ni el correo que dice "hoy no se cobró nada".

4. Pulsa **Execute step**: salen los pagos de hoy (3 en los datos de ejemplo), **un item por pago**.
5. Nodo **Code** llamado `Sumar por forma de pago`, **Mode:** `Run Once for All Items`, lenguaje JavaScript:

```javascript
const pagos = $input.all().map(i => i.json).filter(p => p.importe);
const porForma = {};
for (const p of pagos) porForma[p.forma_pago] = (porForma[p.forma_pago] || 0) + p.importe;
const total = pagos.reduce((s, p) => s + p.importe, 0);
const lineas = Object.entries(porForma).map(([forma, importe]) => `  ${forma}: ${importe.toFixed(2)} €`);
return [{ json: {
  fecha: $now.toFormat('dd/MM/yyyy'),
  total: total.toFixed(2),
  resumen: pagos.length ? lineas.join('\n') : '  (hoy no se ha cobrado nada)',
  n: pagos.length,
} }];
```

> **Qué hace:** junta todos los items en uno solo con el total y un resumen por forma de pago. El `.filter(p => p.importe)` descarta el item vacío que genera *Always Output Data* cuando no hay pagos.
> **Detalle que da guerra:** en un campo de n8n (expresión) se escribe `$now.format(...)`, pero **dentro de un nodo Code** es `$now.toFormat(...)`. Es el mismo dato (un fecha de la librería Luxon) con dos formas de usarlo.

6. Nodo **Send Email** `Enviar cierre a Marisa`: credencial `Mailpit`, To `marisa@lacuchara.example`, Subject `Cierre de caja del {{ $json.fecha }}`, Text:

```
Hola Marisa,

Hoy se han cobrado {{ $json.total }} € ({{ $json.n }} pagos):

{{ $json.resumen }}
```

7. **Execute workflow** (no hace falta esperar a las 21:00). El correo aparece en Mailpit con el total y el reparto.
8. **Comprueba que el total cuadra** con la app: en la pantalla **Pagos** (http://localhost:8000/pagos) suma a mano los de hoy.
9. Pulsa **Publish** para que se ejecute cada noche.

**Checkpoint:** correo de cierre con importes que coinciden con la app. Ya cubre HU-04.

---

## Cierre de la sesión 1 (10 min)

1. **Exporta tus dos flujos.** En cada uno: menú `···` → **Download** → guárdalo en `mis-flujos/` como `01-eventos.json` y `02-cierre.json`. Así tienes copia aunque borres n8n.
2. **Comprueba el checklist:**

| | |
|---|---|
| Las 4 URLs abren y los tres contenedores están en marcha | ☐ |
| Un encargo creado en la app genera el correo de confirmación en Mailpit | ☐ |
| Un pago genera el recibo, y el último pago genera «ya está pagado» | ☐ |
| El flujo 02 manda un cierre con importes que coinciden con la app | ☐ |
| Los flujos 01 y 02 están **publicados** | ☐ |

3. **Para la sesión 2:**
   - Ten lista tu **API key de Groq**.
   - **No ejecutes `docker compose down -v`**: borraría tus flujos y tus credenciales. Para apagar todo sin perder nada, `docker compose down` (sin `-v`) o `docker compose stop`.
   - Cuando empiece la sesión 2: `git switch sesion-2`.

---

## Errores típicos de esta sesión

| Síntoma | Causa | Solución |
|---|---|---|
| La app crea el encargo pero no llega ningún correo | El flujo 01 no está **publicado** (la app usa la Production URL) | Pulsa **Publish** |
| `The requested webhook ... is not registered` | Igual que el anterior, o has usado `/webhook-test/` fuera de *Listen for test event* | Publicar, o pulsar *Listen for test event* antes del `curl` |
| `ECONNREFUSED 127.0.0.1` o `localhost` no responde (SMTP o API) | Estás usando `localhost` dentro de n8n | Usa `mailpit` y `http://pasteleria:8000` |
| `401 Unauthorized` al llamar a la app | La credencial `API Pastelería` no tiene la clave de tu `.env` | Revisa Name `X-API-Key` y el valor |
| `No recipients defined` o `Cannot read properties of undefined` | La expresión no encuentra el dato. En el webhook los datos están en `body.datos`, no en `datos` | Usa `$json.body.datos...` en el flujo del webhook |
| El flujo se para y no llega el cierre cuando no hay pagos | Falta **Always Output Data** en el HTTP Request | Actívalo en Settings del nodo |
| `$now.format is not a function` | Dentro de un nodo **Code** hay que usar `toFormat` | `$now.toFormat('dd/MM/yyyy')` |
| Error 422 al crear un encargo | La app aplica sus reglas (señal ≥ 10 €, entrega en 30 días) | Lee el motivo que devuelve |
