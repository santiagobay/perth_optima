export default function ControlPanel({
  suburbs, suburb, onSuburbChange,
  mode, onModeChange,
  onCalculate, loading, onOpenHelp,
}) {
  return (
    <div className="control-panel">
      <div className="control-panel__field">
        <label htmlFor="suburb">Distrito</label>
        <select id="suburb" value={suburb} onChange={(e) => onSuburbChange(e.target.value)}>
          {suburbs.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>

      <div className="control-panel__field">
        <label htmlFor="mode">Método de solución</label>
        <select id="mode" value={mode} onChange={(e) => onModeChange(e.target.value)}>
          <option value="heuristic">Heurística (vecino más cercano + 2-opt)</option>
          <option value="exact">Modelo exacto (asignación con MTZ)</option>
        </select>
      </div>

      <div className="control-panel__actions">
        <button className="control-panel__help" onClick={onOpenHelp} type="button">
          ¿Cómo funciona?
        </button>
        <button className="control-panel__submit" onClick={onCalculate} disabled={loading}>
          {loading ? "Calculando..." : "Calcular ruta óptima"}
        </button>
      </div>
    </div>
  );
}
