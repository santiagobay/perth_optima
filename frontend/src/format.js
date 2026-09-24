// format.js
// Formateadores compartidos.
//
// Dos motivos para centralizarlos aquí:
//
// 1. El backend puede devolver `null` en cualquier atributo opcional de una
//    vivienda (precio, habitaciones, superficie...), así que ningún componente
//    debe llamar directamente a `.toLocaleString()` sobre un valor de la API:
//    eso rompía el render con "Cannot read properties of null".
//
// 2. La interfaz está en español, pero los números se formateaban en inglés.
//    Una distancia de 1,824 km se imprimía como "1.824 km", que en español se
//    lee como mil ochocientos veinticuatro kilómetros. Con el locale español
//    el punto es siempre separador de miles y la coma siempre decimal, sin
//    ambigüedad posible.

const LOCALE = "es-ES";

function toFiniteNumber(value) {
  if (value === null || value === undefined || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

/** Distancias en kilómetros: "12,35 km", "1,82 km". */
export function formatKm(value, fallback = "n/d") {
  const km = toFiniteNumber(value);
  if (km === null) return fallback;
  return `${km.toLocaleString(LOCALE, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })} km`;
}

/** Porcentajes: "0,88 %". */
export function formatPercent(value, fallback = "n/d") {
  const percent = toFiniteNumber(value);
  if (percent === null) return fallback;
  return `${percent.toLocaleString(LOCALE, { maximumFractionDigits: 2 })} %`;
}

/** Precios en dólares australianos, agrupados a la española: "$1.103.888". */
export function formatPrice(value) {
  const price = toFiniteNumber(value);
  if (price === null) return "Precio no disponible";
  return `$${price.toLocaleString(LOCALE, { maximumFractionDigits: 0 })}`;
}

export function formatNumber(value, fallback = "n/d") {
  const number = toFiniteNumber(value);
  if (number === null) return fallback;
  return number.toLocaleString(LOCALE);
}

/** Duración a partir de minutos: "33,4 h". */
export function formatHours(minutes) {
  const total = toFiniteNumber(minutes);
  if (total === null) return null;
  const hours = Math.round((total / 60) * 10) / 10;
  return `${hours.toLocaleString(LOCALE, { maximumFractionDigits: 1 })} h`;
}
