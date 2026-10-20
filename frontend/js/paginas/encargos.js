// Página «Encargos»: lista con pestañas por estado, buscador y paginación.

import { api } from "../api.js";
import { avisoDeLaDireccion, mostrarAviso, montarLayout } from "../layout.js";
import { esc, euros, etiquetaEstado, icono, paginacion, plazo } from "../ui.js";

const principal = montarLayout("encargos");
const params = new URLSearchParams(location.search);
const estado = params.get("estado") ?? "pendiente";
const q = params.get("q") ?? "";
const POR_PAGINA = 25;
let pagina = Number(params.get("pagina")) || 1;

const PESTANAS = [["pendiente", "Pendientes"], ["pagado", "Pagados"], ["", "Todos"]];

function fila(e) {
  return `<tr>
    <td class="muted">#${e.id}</td>
    <td><a class="row-link" href="/encargos/${e.id}">${esc(e.cliente)}</a>${e.email ? `<span class="sub">${esc(e.email)}</span>` : ""}</td>
    <td>${esc(e.tarta)}<span class="sub">${e.raciones} raciones</span></td>
    <td class="num">${euros(e.precio)}</td>
    <td class="num"><strong>${euros(e.pendiente)}</strong></td>
    <td>${esc(e.fecha_entrega)}<span class="sub">${plazo(e)}</span></td>
    <td>${etiquetaEstado(e.estado)}</td>
  </tr>`;
}

function vacio() {
  return q
    ? `No hay encargos que coincidan con «${esc(q)}». Prueba con otro nombre o <a href="/?estado=">busca en todos los estados</a>.`
    : 'Todavía no hay encargos aquí. <a href="/encargos/nuevo">Crea el primero</a>.';
}

async function pintar() {
  let { items, total } = await api.encargos({ estado, q, pagina, porPagina: POR_PAGINA });
  const paginas = Math.max(1, Math.ceil(total / POR_PAGINA));
  if (pagina > paginas) {
    pagina = paginas;
    ({ items, total } = await api.encargos({ estado, q, pagina, porPagina: POR_PAGINA }));
  }
  const resumen = await api.resumen();
  const base = `/?estado=${encodeURIComponent(estado)}${q ? `&q=${encodeURIComponent(q)}` : ""}&`;

  principal.innerHTML = `
    <div class="page-head">
      <h1>Encargos</h1>
      <a class="btn btn-primary" href="/encargos/nuevo">${icono("plus")} Nuevo encargo</a>
    </div>
    <section class="card" aria-label="Lista de encargos">
      <div class="toolbar">
        <nav class="tabs" aria-label="Filtrar por estado">
          ${PESTANAS.map(([valor, nombre]) => `<a href="/?estado=${valor}${q ? `&q=${encodeURIComponent(q)}` : ""}" ${valor === estado ? 'aria-current="page"' : ""}>
            ${nombre} <span class="count">${valor === "" ? resumen.total : resumen[valor]}</span></a>`).join("")}
        </nav>
        <form class="search" method="get" action="/" role="search">
          <input type="hidden" name="estado" value="${esc(estado)}">
          ${icono("search")}
          <label for="q" class="skip">Buscar encargo</label>
          <input id="q" name="q" type="search" value="${esc(q)}" placeholder="Buscar cliente, tarta o nº">
        </form>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Nº</th><th>Cliente</th><th>Tarta</th><th class="num">Precio</th><th class="num">Pendiente</th><th>Entrega</th><th>Estado</th></tr></thead>
          <tbody>${items.map(fila).join("")}</tbody>
        </table>
        ${items.length ? "" : `<div class="empty">${vacio()}</div>`}
      </div>
      ${paginacion(pagina, paginas, total, base)}
    </section>`;
  avisoDeLaDireccion();
}

pintar().catch((e) => mostrarAviso("error", e.message));
