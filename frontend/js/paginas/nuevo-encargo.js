// Página «Nuevo encargo»: formulario que envía los datos a la API.
// Si la API los rechaza, el formulario sigue como estaba (no se pierde lo escrito).

import { api } from "../api.js";
import { mostrarAviso, montarLayout } from "../layout.js";
import { FORMAS_PAGO, icono, opcionesFormaPago } from "../ui.js";

const principal = montarLayout("encargos");

principal.innerHTML = `
  <div class="page-head">
    <div>
      <a href="/" class="muted">${icono("back", 16)} Encargos</a>
      <h1 style="margin-top:8px">Nuevo encargo</h1>
    </div>
  </div>
  <form id="formulario" class="card card-body">
    <fieldset>
      <legend>Cliente</legend>
      <div class="grid">
        <div><label for="cliente">Nombre <span class="req" aria-hidden="true">*</span></label>
          <input id="cliente" name="cliente" required autocomplete="name" autofocus></div>
        <div><label for="email">Correo</label>
          <input id="email" name="email" type="email" autocomplete="email">
          <span class="hint">Para enviarle la confirmación y los recibos.</span></div>
      </div>
    </fieldset>
    <fieldset>
      <legend>Tarta</legend>
      <div class="grid">
        <div><label for="tarta">Tarta <span class="req" aria-hidden="true">*</span></label>
          <input id="tarta" name="tarta" required placeholder="Tarta de queso"></div>
        <div><label for="raciones">Raciones <span class="req" aria-hidden="true">*</span></label>
          <input id="raciones" name="raciones" type="number" min="1" required></div>
        <div><label for="precio">Precio (€) <span class="req" aria-hidden="true">*</span></label>
          <input id="precio" name="precio" type="number" step="0.01" min="0.01" required></div>
        <div><label for="fecha_entrega">Fecha de entrega <span class="req" aria-hidden="true">*</span></label>
          <input id="fecha_entrega" name="fecha_entrega" type="date" required aria-describedby="entrega-hint">
          <span class="hint" id="entrega-hint">Entre mañana y dentro de 30 días.</span></div>
      </div>
    </fieldset>
    <fieldset>
      <legend>Señal</legend>
      <div class="grid">
        <div><label for="senal">Señal (€) <span class="req" aria-hidden="true">*</span></label>
          <input id="senal" name="senal" type="number" step="0.01" min="10" required aria-describedby="senal-hint">
          <span class="hint" id="senal-hint">Mínimo 10 €. El resto se paga antes de la entrega.</span></div>
        <div><label for="forma_pago">Forma de pago</label>
          <select id="forma_pago" name="forma_pago">${opcionesFormaPago(FORMAS_PAGO)}</select></div>
      </div>
    </fieldset>
    <div class="actions">
      <button class="btn btn-primary" type="submit">${icono("plus")} Guardar encargo</button>
      <a class="btn btn-ghost" href="/">Cancelar</a>
    </div>
  </form>`;

document.getElementById("formulario").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const f = new FormData(evento.target);
  const boton = evento.target.querySelector("button[type=submit]");
  boton.disabled = true;
  try {
    const nuevo = await api.crearEncargo({
      cliente: f.get("cliente"),
      email: f.get("email") || null,
      tarta: f.get("tarta"),
      raciones: Number(f.get("raciones")),
      precio: Number(f.get("precio")),
      fecha_entrega: f.get("fecha_entrega"),
      senal: Number(f.get("senal")),
      forma_pago: f.get("forma_pago"),
    });
    location.href = `/encargos/${nuevo.id}?ok=${encodeURIComponent("Encargo creado")}`;
  } catch (e) {
    mostrarAviso("error", e.message);
    boton.disabled = false;
  }
});
