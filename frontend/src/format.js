// format.js
// Formateadores compartidos. El backend puede devolver `null` en cualquier
// atributo opcional de una vivienda (precio, habitaciones, superficie...),
// así que ningún componente debe llamar directamente a `.toLocaleString()`
// sobre un valor de la API: eso rompía el render con
// "Cannot read properties of null".

export function formatPrice(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "Precio no disponible";
  }
  return `$${Number(value).toLocaleString("en-AU", { maximumFractionDigits: 0 })}`;
}

export function formatNumber(value, fallback = "n/d") {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return fallback;
  }
  return Number(value).toLocaleString("en-AU");
}

export function formatHours(minutes) {
  if (minutes === null || minutes === undefined || Number.isNaN(Number(minutes))) {
    return null;
  }
  return `${Math.round((Number(minutes) / 60) * 10) / 10} h`;
}
