import { useEffect, useRef, useState } from "react";
import { fetchSuburbs, fetchRoute } from "./api";
import ControlPanel from "./components/ControlPanel";
import HelpModal from "./components/HelpModal";
import RouteMap from "./components/RouteMap";
import RouteList from "./components/RouteList";
import StatsPanel from "./components/StatsPanel";
import "./styles.css";

const HELP_SEEN_KEY = "perth-optima:help-seen";

function readHelpSeen() {
  try {
    return localStorage.getItem(HELP_SEEN_KEY);
  } catch {
    return null;
  }
}

function writeHelpSeen() {
  try {
    localStorage.setItem(HELP_SEEN_KEY, "1");
  } catch {
    /* almacenamiento no disponible: la ayuda volverá a abrirse, sin más */
  }
}

export default function App() {
  const [suburbs, setSuburbs] = useState([]);
  const [suburb, setSuburb] = useState("");
  const [mode, setMode] = useState("heuristic");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  // La ayuda se abre la primera vez y no vuelve a molestar en visitas
  // siguientes (el usuario puede reabrirla desde el panel de control).
  // El acceso va protegido porque localStorage lanza excepción en algunos
  // modos privados del navegador.
  const [helpOpen, setHelpOpen] = useState(() => readHelpSeen() !== "1");

  // Evita que la respuesta de un cálculo anterior pise a la del último
  // clic si el usuario cambia de distrito mientras uno está en curso.
  const requestId = useRef(0);

  useEffect(() => {
    fetchSuburbs()
      .then((list) => {
        setSuburbs(list);
        if (list.length === 0) return;
        const preferred = list.find((s) => s.name === "Nedlands") ?? list[0];
        setSuburb(preferred.name);
      })
      .catch((e) => setError(e.message));
  }, []);

  function closeHelp() {
    writeHelpSeen();
    setHelpOpen(false);
  }

  async function handleCalculate() {
    if (!suburb) return;
    const currentRequest = ++requestId.current;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRoute(suburb, mode);
      if (currentRequest !== requestId.current) return;
      setResult(data);
    } catch (e) {
      if (currentRequest !== requestId.current) return;
      setError(e.message);
      setResult(null);
    } finally {
      if (currentRequest === requestId.current) setLoading(false);
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

      <HelpModal isOpen={helpOpen} onClose={closeHelp} />

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
