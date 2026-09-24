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
        <p className="app__eyebrow">Perth House Prices · Modelamiento y Optimización</p>
        <h1>Ruta óptima de visita a propiedades</h1>
        <p className="app__subtitle">
          Calcula, para un distrito de Perth, el orden de visita que minimiza la distancia
          total recorrida entre viviendas, comparando un modelo exacto de asignación con
          eliminación de subtours (MTZ) y una heurística de vecino más cercano con mejora 2-opt.
        </p>
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
