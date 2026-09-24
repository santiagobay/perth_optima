// api.js
// Única puerta de entrada del frontend hacia el backend de Python.
// Mantener aquí, y solo aquí, las llamadas fetch mantiene a los
// componentes de React desacoplados de los detalles de la API.

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:5000";

export async function fetchSuburbs() {
  const res = await fetch(`${API_BASE}/api/suburbs`);
  if (!res.ok) throw new Error("No se pudieron cargar los suburbios.");
  const data = await res.json();
  return data.suburbs;
}

export async function fetchRoute(suburb, mode = "heuristic") {
  const params = new URLSearchParams({ suburb, mode });
  const res = await fetch(`${API_BASE}/api/route?${params}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || "No se pudo calcular la ruta.");
  }
  return res.json();
}
