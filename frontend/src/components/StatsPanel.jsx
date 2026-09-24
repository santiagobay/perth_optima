export default function StatsPanel({ result }) {
  if (!result) return null;

  const { suburb, mode, n_houses, total_distance_km, raw_result } = result;

  return (
    <div className="stats-panel">
      <div className="stats-panel__stat">
        <span className="stats-panel__value">{total_distance_km} km</span>
        <span className="stats-panel__label">distancia total del recorrido</span>
      </div>
      <div className="stats-panel__stat">
        <span className="stats-panel__value">{n_houses}</span>
        <span className="stats-panel__label">viviendas en {suburb}</span>
      </div>
      {mode === "heuristic" && raw_result?.estimated_time_minutes && (
        <div className="stats-panel__stat">
          <span className="stats-panel__value">
            {Math.round(raw_result.estimated_time_minutes / 60 * 10) / 10} h
          </span>
          <span className="stats-panel__label">tiempo estimado (con buffers)</span>
        </div>
      )}
      <div className="stats-panel__stat">
        <span className="stats-panel__value">
          {mode === "exact" ? "Óptimo exacto (MTZ)" : "Heurística NN + 2-opt"}
        </span>
        <span className="stats-panel__label">método de solución</span>
      </div>
    </div>
  );
}
