// Página de un encargo: resumen, barra de progreso, lista de pagos y formulario para registrar otro pago.

import { api } from "../api.js";
import { avisoDeLaDireccion, mostrarAviso, montarLayout } from "../layout.js";
import { FORMAS_PAGO, esc, euros, etiquetaEstado, icono, opcionesFormaPago, plazo } from "../ui.js";

const principal = montarLayout("encargos");
const id = location.pathname.split("/").pop();

function formularioPago(e) {
  if (e.estado !== "pendiente") return "";
  return `<form id="formulario-pago" class="card card-body stack" aria-label="Registrar pago">
    <h2>Registrar pago</h2>
    <div><label for="importe">Importe (€)</label>
      <input id="importe" name="importe" type="number" step="0.01" min="0.01" max="${e.pendiente}" required autofocus aria-describedby="importe-hint">
      <span class="hint" id="importe-hint">Faltan ${euros(e.pendiente)}.</span></div>
    <div><label for="forma_pago">Forma de pago</label>
      <select id="forma_pago" name="forma_pago">${opcionesFormaPago(FORMAS_PAGO)}</select></div>
    <button class="btn btn-primary" type="submit">Registrar pago</button>
  </form>`;
}

async function pintar() {
  const e = await api.encargo(id);
  const pagos = [...e.pagos].reverse(); // el más reciente primero
  const porcentaje = Math.round((e.pagado / e.precio) * 100);
  document.title = `Encargo #${e.id} · La Cuchara`;
  principal.innerHTML = `
    <div class="page-head">
      <div>
        <a href="/" class="muted">${icono("back", 16)} Encargos</a>
        <h1 style="margin-top:8px">Encargo #${e.id} ${etiquetaEstado(e.estado)}</h1>
      </div>
    </div>
    <div class="layout-2">
      <div class="stack">
        <section class="card card-body stack" aria-label="Resumen">
          <div>
            <h2>${esc(e.cliente)}</h2>
            <p class="muted" style="margin:4px 0 0">${esc(e.email || "Sin correo")}</p>
          </div>
          <p style="margin:0"><strong>${esc(e.tarta)}</strong> · ${e.raciones} raciones</p>
          <div class="stats">
            <div class="stat"><div class="label">Precio</div><div class="value">${euros(e.precio)}</div></div>
            <div class="stat"><div class="label">Pagado</div><div class="value">${euros(e.pagado)}</div></div>
            <div class="stat"><div class="label">Pendiente</div><div class="value">${euros(e.pendiente)}</div></div>
          </div>
          <div>
            <div class="progress" role="progressbar" aria-valuenow="${porcentaje}" aria-valuemin="0" aria-valuemax="100" aria-label="Pagado"><span style="width: ${porcentaje}%"></span></div>
            <p class="muted" style="margin:6px 0 0">${porcentaje}% pagado · Encargado el ${esc(e.fecha)} · Entrega el ${esc(e.fecha_entrega)} ${plazo(e)}</p>
          </div>
        </section>
        <section class="card" aria-label="Pagos">
          <div class="card-body" style="padding-bottom:0"><h2>Pagos</h2></div>
          <div class="table-wrap">
            <table>
              <thead><tr><th>Fecha</th><th>Forma de pago</th><th class="num">Importe</th></tr></thead>
              <tbody>${pagos.map((p) => `<tr><td>${esc(p.fecha)}</td><td>${esc(p.forma_pago.charAt(0).toUpperCase() + p.forma_pago.slice(1))}</td><td class="num">${euros(p.importe)}</td></tr>`).join("")}</tbody>
            </table>
          </div>
        </section>
      </div>
      ${formularioPago(e)}
    </div>`;
  document.getElementById("formulario-pago")?.addEventListener("submit", registrar);
  avisoDeLaDireccion();
}

async function registrar(evento) {
  evento.preventDefault();
  const f = new FormData(evento.target);
  const boton = evento.target.querySelector("button[type=submit]");
  boton.disabled = true;
  try {
    const actualizado = await api.registrarPago(id, { importe: Number(f.get("importe")), forma_pago: f.get("forma_pago") });
    const mensaje = actualizado.estado === "pagado" ? "Encargo pagado: ya puede recoger su tarta" : "Pago registrado";
    location.href = `/encargos/${id}?ok=${encodeURIComponent(mensaje)}`;
  } catch (e) {
    mostrarAviso("error", e.message);
    boton.disabled = false;
  }
}

pintar().catch((e) => mostrarAviso("error", e.message));
