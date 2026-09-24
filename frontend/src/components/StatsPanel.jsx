import { formatHours, formatKm, formatNumber, formatPercent } from "../format";

export default function StatsPanel({ result }) {
  if (!result) return null;

  const {
    suburb,
    mode,
    n_houses,
    n_houses_in_route,
    total_distance_km,
    estimated_time_minutes,
    exact_subset_used,
    optimality_gap_percent,
    heuristic_distance_km,
    message,
    raw_result,
  } = result;

  const isExact = mode === "exact";
  // El modo exacto puede resolverse sobre un subconjunto: la distancia
  // corresponde a las viviendas realmente recorridas, no al distrito entero.
  const routedHouses = n_houses_in_route ?? n_houses;
  const minutes = estimated_time_minutes ?? raw_result?.estimated_time_minutes;
  const hours = formatHours(minutes);
  const distance = formatKm(total_distance_km);
  const hasGap = optimality_gap_percent !== null && optimality_gap_percent !== undefined;

  return (
    <>
      <div className="stats-panel">
        <div className="stats-panel__stat">
          <span className="stats-panel__value">{distance}</span>
          <span className="stats-panel__label">
            {isExact && exact_subset_used
              ? `distancia del recorrido sobre ${routedHouses} viviendas`
              : "distancia total del recorrido"}
          </span>
        </div>

        <div className="stats-panel__stat">
          <span className="stats-panel__value">{formatNumber(routedHouses)}</span>
          <span className="stats-panel__label">
            {routedHouses === n_houses
              ? `viviendas en ${suburb}`
              : `viviendas en la ruta (de ${formatNumber(n_houses)} en ${suburb})`}
          </span>
        </div>

        {hours && (
          <div className="stats-panel__stat">
            <span className="stats-panel__value">{hours}</span>
            <span className="stats-panel__label">tiempo estimado (con buffers)</span>
          </div>
        )}

        {isExact && hasGap && (
          <div className="stats-panel__stat">
            <span className="stats-panel__value">{formatPercent(optimality_gap_percent)}</span>
            <span className="stats-panel__label">brecha de la heurística sobre el óptimo</span>
          </div>
        )}

        <div className="stats-panel__stat">
          <span className="stats-panel__value">
            {isExact ? "Óptimo exacto (MTZ)" : "Heurística NN + 2-opt"}
          </span>
          <span className="stats-panel__label">método de solución</span>
        </div>
      </div>

      {isExact && exact_subset_used && (
        <div className="stats-panel__note">
          <p>{message}</p>
          {/* Sin esta aclaración los dos modos parecen resolver el mismo
              problema con resultados dispares, cuando en realidad resuelven
              instancias de distinto tamaño. */}
          <p>
            <strong>Ojo al comparar con el modo heurístico:</strong> esos {distance}{" "}
            recorren {routedHouses} viviendas, mientras que la heurística recorre las{" "}
            {formatNumber(n_houses)} del distrito. Son rutas de distinto tamaño, así que
            sus distancias no son comparables entre sí.
          </p>
          {heuristic_distance_km != null && (
            <p>
              La comparación válida es sobre la <em>misma</em> instancia de{" "}
              {routedHouses} viviendas: el óptimo exacto da {distance} y la heurística{" "}
              {formatKm(heuristic_distance_km)}
              {hasGap
                ? `, es decir, un ${formatPercent(optimality_gap_percent)} por encima del óptimo.`
                : "."}
            </p>
          )}
        </div>
      )}
    </>
  );
}
