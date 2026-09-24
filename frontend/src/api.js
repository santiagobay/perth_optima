// api.js
// Única puerta de entrada del frontend hacia el backend de Python.
// Mantener aquí, y solo aquí, las llamadas fetch mantiene a los
// componentes de React desacoplados de los detalles de la API.

const API_BASE = (import.meta.env.VITE_API_BASE || "http://127.0.0.1:5000").replace(/\/+$/, "");

async function readError(res, fallback) {
  const payload = await res.json().catch(() => ({}));
  return new Error(payload.error || fallback);
}

/**
 * Devuelve los distritos disponibles como [{ name, n_houses }].
 * Se acepta también la forma antigua (lista de strings) por compatibilidad.
 */
export async function fetchSuburbs() {
  const res = await fetch(`${API_BASE}/api/suburbs`);
  if (!res.ok) throw await readError(res, "No se pudieron cargar los suburbios.");

  const data = await res.json();
  if (Array.isArray(data.details)) return data.details;
  return (data.suburbs || []).map((name) => ({ name, n_houses: null }));
}

export async function fetchRoute(suburb, mode = "heuristic") {
  const params = new URLSearchParams({ suburb, mode });
  const res = await fetch(`${API_BASE}/api/route?${params}`);
  if (!res.ok) throw await readError(res, "No se pudo calcular la ruta.");
  return res.json();
}
