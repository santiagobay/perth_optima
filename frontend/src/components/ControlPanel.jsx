export default function ControlPanel({
  suburbs, suburb, onSuburbChange,
  mode, onModeChange,
  onCalculate, loading, onOpenHelp,
}) {
  const ready = suburbs.length > 0;

  return (
    <div className="control-panel">
      <div className="control-panel__field">
        <label htmlFor="suburb">Distrito</label>
        <select
          id="suburb"
          value={suburb}
          disabled={!ready || loading}
          onChange={(e) => onSuburbChange(e.target.value)}
        >
          {/* Sin esta opción el <select> quedaba controlado con value=""
              mientras cargan los distritos, lo que desincroniza lo que se ve
              del estado real. */}
          {!ready && <option value="">Cargando distritos...</option>}
          {suburbs.map((s) => (
            <option key={s.name} value={s.name}>
              {s.n_houses ? `${s.name} (${s.n_houses} viviendas)` : s.name}
            </option>
          ))}
        </select>
      </div>

      <div className="control-panel__field">
        <label htmlFor="mode">Método de solución</label>
        <select
          id="mode"
          value={mode}
          disabled={loading}
          onChange={(e) => onModeChange(e.target.value)}
        >
          <option value="heuristic">Heurística (vecino más cercano + 2-opt)</option>
          <option value="exact">Modelo exacto (asignación con MTZ)</option>
        </select>
      </div>

      <div className="control-panel__actions">
        <button className="control-panel__help" onClick={onOpenHelp} type="button">
          ¿Cómo funciona?
        </button>
        <button
          className="control-panel__submit"
          onClick={onCalculate}
          type="button"
          disabled={loading || !suburb}
        >
          {loading ? "Calculando..." : "Calcular ruta óptima"}
        </button>
      </div>
    </div>
  );
}
