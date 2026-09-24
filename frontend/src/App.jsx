import { useEffect, useState } from "react";
import { fetchSuburbs, fetchRoute } from "./api";
import ControlPanel from "./components/ControlPanel";
import HelpModal from "./components/HelpModal";
import RouteMap from "./components/RouteMap";
import RouteList from "./components/RouteList";
import StatsPanel from "./components/StatsPanel";
import "./styles.css";

export default function App() {
  const [suburbs, setSuburbs] = useState([]);
  const [suburb, setSuburb] = useState("");
  const [mode, setMode] = useState("heuristic");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [helpOpen, setHelpOpen] = useState(true);

  useEffect(() => {
    fetchSuburbs()
      .then((list) => {
        setSuburbs(list);
        if (list.length > 0) setSuburb(list[0]);
      })
      .catch((e) => setError(e.message));
  }, []);

  async function handleCalculate() {
    if (!suburb) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRoute(suburb, mode);
      setResult(data);
    } catch (e) {
      setError(e.message);
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <header className="app__header">
        <div className="app__hero">
          <div className="app__brand">
            <span className="app__brand-mark">P</span>
            <div>
              <p className="app__eyebrow">Perth Optima</p>
              <strong>Optimización de rutas urbanas</strong>
            </div>
          </div>

          <div className="app__chip-row">
            <span>Exact MTZ</span>
            <span>Heurística 2-opt</span>
            <span>Geo data</span>
          </div>

          <h1>Ruta óptima de visita a propiedades en Perth</h1>
          <p className="app__subtitle">
            Compara modelos de optimización para minimizar la distancia total recorrida,
            visualizar el recorrido y entender cómo cada método resuelve un problema de
            rutas con restricciones reales.
          </p>
        </div>
      </header>

      <ControlPanel
        suburbs={suburbs}
        suburb={suburb}
        onSuburbChange={setSuburb}
        mode={mode}
        onModeChange={setMode}
        onCalculate={handleCalculate}
        loading={loading}
        onOpenHelp={() => setHelpOpen(true)}
      />

      <HelpModal isOpen={helpOpen} onClose={() => setHelpOpen(false)} />

      {error && <p className="app__error">{error}</p>}

      {result && (
        <>
          <StatsPanel result={result} />
          <div className="app__body">
            <RouteMap route={result.route} />
            <RouteList route={result.route} />
          </div>
        </>
      )}

      {!result && !error && (
        <p className="app__hint">Elige un distrito y presiona “Calcular ruta óptima”.</p>
      )}
    </div>
  );
}
