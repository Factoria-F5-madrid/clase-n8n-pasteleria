// Página «Pagos»: historial de todos los pagos, del más reciente al más antiguo.

import { api } from "../api.js";
import { mostrarAviso, montarLayout } from "../layout.js";
import { esc, euros, paginacion } from "../ui.js";

const principal = montarLayout("pagos");
const POR_PAGINA = 25;
let pagina = Number(new URLSearchParams(location.search).get("pagina")) || 1;

async function pintar() {
  let { items, total } = await api.pagos({ pagina, porPagina: POR_PAGINA });
  const paginas = Math.max(1, Math.ceil(total / POR_PAGINA));
  if (pagina > paginas) {
    pagina = paginas;
    ({ items, total } = await api.pagos({ pagina, porPagina: POR_PAGINA }));
  }
  principal.innerHTML = `
    <div class="page-head"><h1>Pagos</h1></div>
    <section class="card" aria-label="Historial de pagos">
      <div class="table-wrap">
        <table>
          <thead><tr><th>Fecha</th><th>Encargo</th><th>Forma de pago</th><th class="num">Importe</th></tr></thead>
          <tbody>${items.map((p) => `<tr>
            <td>${esc(p.fecha)}</td>
            <td><a class="row-link" href="/encargos/${p.encargo_id}">#${p.encargo_id} · ${esc(p.cliente)}</a></td>
            <td>${esc(p.forma_pago.charAt(0).toUpperCase() + p.forma_pago.slice(1))}</td>
            <td class="num">${euros(p.importe)}</td></tr>`).join("")}</tbody>
        </table>
        ${items.length ? "" : '<div class="empty">Todavía no hay pagos.</div>'}
      </div>
      ${paginacion(pagina, paginas, total, "/pagos?")}
    </section>`;
}

pintar().catch((e) => mostrarAviso("error", e.message));
