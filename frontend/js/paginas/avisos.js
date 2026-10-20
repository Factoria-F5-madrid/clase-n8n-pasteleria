// Página «Avisos a n8n»: los últimos avisos que la app ha enviado y si n8n los recibió.

import { api } from "../api.js";
import { mostrarAviso, montarLayout } from "../layout.js";
import { esc } from "../ui.js";

const principal = montarLayout("avisos");

async function pintar() {
  const { url, avisos } = await api.avisos();
  principal.innerHTML = `
    <div class="page-head"><h1>Avisos a n8n</h1></div>
    <div class="card card-body stack" style="margin-bottom:16px">
      <p style="margin:0">Cada vez que se crea un encargo o se registra un pago, la app envía un <strong>aviso</strong> (un <em>webhook</em>) a n8n. Aquí ves los últimos 20 y si n8n los recibió.</p>
      <p class="muted" style="margin:0">Dirección a la que avisa: <code>${esc(url) || "(vacía)"}</code></p>
    </div>
    <section class="card" aria-label="Últimos avisos">
      <div class="table-wrap">
        <table>
          <thead><tr><th>Hora</th><th>Evento</th><th>Resultado</th><th>Contenido</th></tr></thead>
          <tbody>${avisos.map((a) => `<tr>
            <td>${esc(a.hora)}</td>
            <td><code>${esc(a.evento)}</code></td>
            <td><span class="badge ${a.ok ? "badge-pagado" : "badge-warn"}">${esc(a.resultado)}</span></td>
            <td><details class="aviso"><summary>Ver JSON</summary><pre class="json">${esc(a.json_enviado)}</pre></details></td></tr>`).join("")}</tbody>
        </table>
        ${avisos.length ? "" : '<div class="empty">Todavía no se ha enviado ningún aviso. Crea un encargo o registra un pago y vuelve aquí.</div>'}
      </div>
    </section>`;
}

pintar().catch((e) => mostrarAviso("error", e.message));
