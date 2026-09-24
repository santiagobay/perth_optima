import { formatHours } from "../format";

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
    message,
    raw_result,
  } = result;

  const isExact = mode === "exact";
  // El modo exacto puede resolverse sobre un subconjunto: la distancia
  // corresponde a las viviendas realmente recorridas, no al distrito entero.
  const routedHouses = n_houses_in_route ?? n_houses;
  const minutes = estimated_time_minutes ?? raw_result?.estimated_time_minutes;
  const hours = formatHours(minutes);

  return (
    <>
      <div className="stats-panel">
        <div className="stats-panel__stat">
          <span className="stats-panel__value">{total_distance_km} km</span>
          <span className="stats-panel__label">distancia total del recorrido</span>
        </div>

        <div className="stats-panel__stat">
          <span className="stats-panel__value">{routedHouses}</span>
          <span className="stats-panel__label">
            {routedHouses === n_houses
              ? `viviendas en ${suburb}`
              : `viviendas en la ruta (de ${n_houses} en ${suburb})`}
          </span>
        </div>

        {hours && (
          <div className="stats-panel__stat">
            <span className="stats-panel__value">{hours}</span>
            <span className="stats-panel__label">tiempo estimado (con buffers)</span>
          </div>
        )}

        {isExact && optimality_gap_percent !== null && optimality_gap_percent !== undefined && (
          <div className="stats-panel__stat">
            <span className="stats-panel__value">{optimality_gap_percent} %</span>
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

      {isExact && exact_subset_used && message && (
        <p className="stats-panel__note">{message}</p>
      )}
    </>
  );
}
