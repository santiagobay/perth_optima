import { useState } from "react";

const tabs = [
  { id: "context", label: "ABP / escenario" },
  { id: "exact", label: "Modelo exacto (MTZ)" },
  { id: "heuristic", label: "Heurística" },
];

export default function HelpModal({ isOpen, onClose }) {
  const [activeTab, setActiveTab] = useState("context");

  if (!isOpen) return null;

  return (
    <div className="help-modal" onClick={onClose}>
      <div className="help-modal__content" onClick={(e) => e.stopPropagation()}>
        <div className="help-modal__header">
          <h2>Explicación de los modelos</h2>
          <button className="help-modal__close" onClick={onClose} aria-label="Cerrar ayuda">
            ×
          </button>
        </div>

        <div className="help-modal__tabs" role="tablist" aria-label="Secciones de ayuda">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={activeTab === tab.id}
              className={`help-modal__tab ${activeTab === tab.id ? "help-modal__tab--active" : ""}`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="help-modal__body">
          {activeTab === "context" && (
            <>
              <p>
                El problema que resuelve esta app encaja con el enfoque ABP: un estudiante o
                un comprador quiere visitar un conjunto de propiedades de un mismo distrito,
                empezando y terminando en la misma casa, sin repetir ninguna vivienda.
              </p>

              <p>
                En el escenario social planteado, el dataset de Perth tiene muchos suburbios y,
                en promedio, alrededor de 100 viviendas por distrito. Eso significa que el problema
                real no es “resolver todo Perth de una vez”, sino resolver un problema de rutas en
                un distrito concreto.
              </p>

              <p>
                La formulación correcta es un TSP (Traveling Salesman Problem): cada propiedad es un
                nodo y cada camino entre dos propiedades tiene un costo, que en este caso es la
                distancia geodésica entre coordenadas.
              </p>

              <p>
                <strong>¿Se resuelve totalmente?</strong> La respuesta es: <strong>sí para una instancia
                concreta de un suburbio</strong>, y <strong>no como una optimización global de todos los
                322 suburbios de Perth a la vez</strong>. El problema completo sería mucho más grande y
                tendría que plantearse como una variante de ruteo más compleja, no como un único TSP
                clásico de un solo agente.
              </p>
            </>
          )}

          {activeTab === "exact" && (
            <>
              <p>
                El modelo exacto se basa en la formulación MTZ (Miller, Tucker y Zemlin), una
                manera de representar el TSP como un modelo de programación lineal entera.
              </p>

              <p>
                Se define una variable binaria <strong>x<sub>ij</sub></strong> que vale 1 cuando el
                recorrido va de la vivienda i a la j. Además, se utilizan variables auxiliares
                <strong> u<sub>i</sub> </strong>para imponer un orden de visita y evitar subciclos.
              </p>

              <p>
                La función objetivo minimiza la distancia total recorrida. Las restricciones garantizan
                que cada vivienda sea visitada una sola vez y que no existan ciclos parciales aislados,
                lo que impide soluciones con varios recorridos separados.
              </p>

              <p>
                Esta opción es precisa, pero es costosa computacionalmente: el crecimiento es muy rápido
                según el número de viviendas. Por eso solo se usa en subconjuntos pequeños.
              </p>
            </>
          )}

          {activeTab === "heuristic" && (
            <>
              <p>
                La heurística es más práctica cuando el número de viviendas es grande. Empezamos con
                el algoritmo de vecino más cercano: desde una casa inicial, se va siempre a la no visitada
                más cercana.
              </p>

              <p>
                Después aplicamos una mejora local 2-opt, que intenta invertir tramos de la ruta para
                reducir la distancia total sin cambiar demasiado la estructura del recorrido.
              </p>

              <p>
                Esto no garantiza la solución óptima global, pero ofrece una ruta aceptable en poco tiempo,
                que es precisamente lo que hace útil a esta app para distritos con decenas o cientos de
                propiedades.
              </p>

              <p>
                En resumen: <strong>exacto = mejor calidad, más tiempo</strong>; <strong>heurística = buena
                solución, muy útil a escala real</strong>.
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
