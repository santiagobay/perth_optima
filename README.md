# Ruta óptima de visita a propiedades residenciales en Perth

Este proyecto resuelve un problema real de optimización de rutas para visitar propiedades dentro de un mismo suburbio de Perth, Australia. A partir de un dataset real de viviendas, se filtra un distrito concreto, se calculan distancias entre propiedades usando sus coordenadas geográficas y se determina el orden de visita que minimiza la distancia total recorrida, partiendo y terminando en la misma vivienda sin repetir ninguna.

La solución combina dos enfoques:

- un modelo exacto basado en programación entera para subinstancias pequeñas,
- y una heurística rápida para distritos completos o grandes.

La aplicación es una demostración funcional del problema y se implementa con un backend en Python y un frontend en React.

## Problema que resuelve

El problema se puede interpretar como una variante del problema del agente viajero (TSP):

- cada vivienda es un nodo,
- cada par de viviendas tiene un costo asociado, dado por la distancia geodésica,
- la ruta debe empezar y terminar en la misma propiedad,
- cada vivienda debe visitarse exactamente una vez,
- la solución debe minimizar la distancia total recorrida.

Esto tiene sentido en escenarios reales de visitas a propiedades, inspecciones inmobiliarias, recorridos comerciales o planificación de visitas por zonas geográficas.

## Justificación metodológica

El comportamiento del sistema se fundamenta en dos ideas complementarias:

1. Modelo exacto: útil para subconjuntos pequeños donde se requiere la mejor solución posible.
2. Heurística: útil para instancias más grandes, donde el problema exacto se vuelve computacionalmente costoso.

El proyecto compara ambos enfoques para mostrar que el problema real no puede resolverse únicamente con un enfoque exacto en todos los casos, aunque la formulación exacta es importante para validar la calidad de la solución.

## Modelo matemático

Se define una matriz de costos C = [c_ij], donde cada c_ij representa la distancia geodésica entre la vivienda i y la vivienda j.

Las variables de decisión son:

- x_ij ∈ {0,1}
  - x_ij = 1 si el recorrido va directamente de la vivienda i a la j.
- u_i
  - variables auxiliares que representan el orden de visita de cada vivienda.

La función objetivo es:

min Σ_i Σ_j c_ij x_ij

sujeta a las restricciones:

- una sola salida por vivienda: Σ_j x_ij = 1, ∀i
- una sola entrada por vivienda: Σ_i x_ij = 1, ∀j
- eliminación de subtours mediante la formulación MTZ:

u_i - u_j + n x_ij ≤ n - 1

para cada i, j ∈ N \ {1}, con i ≠ j,

junto con:

- u_1 = 1
- 2 ≤ u_i ≤ n para toda vivienda i ≠ 1

La desigualdad MTZ es la pieza clave que evita la formación de ciclos parciales desconectados, garantizando que la solución sea una única ruta continua que recorra todas las viviendas.

## Enfoque exacto y heurístico

### 1) Modelo exacto MTZ

Se usa una formulación de programación entera para obtener la solución óptima en instancias pequeñas. Es muy útil para validación y comparación porque produce la mejor ruta posible para un subconjunto manejable de viviendas.

### 2) Heurística vecino más cercano + 2-opt

La heurística primero construye una ruta factible partiendo desde una vivienda inicial y eligiendo cada vez la casa no visitada más cercana. Luego aplica la mejora local 2-opt para invertir tramos de la ruta si eso reduce la distancia total.

El vecino más cercano es muy sensible al punto de partida, así que se repite la construcción desde varios arranques repartidos por el distrito, se mejora cada uno con 2-opt y se conserva el mejor recorrido; el tour resultante se rota para que la ruta que ve el usuario siga empezando y terminando en la misma vivienda (rotar un ciclo no cambia su longitud).

No garantiza optimalidad global, pero ofrece soluciones muy buenas en tiempos bajos y es apropiada para distritos con muchas propiedades.

### Notas de rendimiento

Tres decisiones mantienen la API utilizable sobre el dataset completo de Perth (~33.600 viviendas, 321 distritos, hasta 231 viviendas en el más grande):

- **Dataset memoizado**: los CSV se leen y normalizan una sola vez; la caché se invalida sola si cambia la fecha o el tamaño de algún archivo.
- **Matriz de distancias simétrica y memoizada**: `d(i,j) = d(j,i)`, así que solo se calcula el triángulo superior (la mitad de llamadas a geopy) y el resultado se reutiliza entre peticiones del mismo distrito.
- **2-opt con evaluación incremental**: cada intercambio se valora con los cuatro arcos que cambian en lugar de recalcular la ruta completa, lo que baja cada pasada de O(n³) a O(n²).

## Stack tecnológico

### Backend
- Python
- Flask
- Pyomo
- CBC (solver exacto externo)
- pandas
- geopy

### Frontend
- React
- Vite
- Leaflet + OpenStreetMap

## Estructura del repositorio

```text
project_perth_ruta_optima/
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   ├── run_demo.py
│   ├── data/
│   │   ├── all_perth_310121.csv
│   │   ├── perth_houses_claremont.csv
│   │   ├── perth_houses_nedlands.csv
│   │   └── perth_houses_subiaco.csv
│   ├── optimization/
│   │   ├── __init__.py
│   │   ├── data_loader.py
│   │   ├── distances.py
│   │   ├── exact_solver.py
│   │   └── heuristic_solver.py
│   ├── tests/
│   │   ├── test_exact_solver.py
│   │   ├── test_exact_subset_mode.py
│   │   ├── test_heuristic_solver.py
│   │   └── test_real_dataset_columns.py
│   └── outputs/
│       ├── distance_matrix.csv
│       ├── execution_log.txt
│       └── route_result.json
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   ├── public/
│   └── src/
│       ├── api.js
│       ├── App.jsx
│       ├── format.js
│       ├── main.jsx
│       ├── index.css
│       ├── styles.css
│       ├── components/
│       │   ├── ControlPanel.jsx
│       │   ├── RouteList.jsx
│       │   ├── RouteMap.jsx
│       │   ├── StatsPanel.jsx
│       │   └── HelpModal.jsx
├── README.md
└── .gitignore
```

## Requisitos previos

### Python
- Python 3.10 o superior recomendado.

### Solver exacto
El modelo exacto usa CBC. CBC no se instala como paquete de Python; es un ejecutable del sistema operativo.

En Windows, puedes instalarlo con:

```powershell
winget install --id COIN-OR.CBC -e
```

En Linux/macOS:

```bash
sudo apt-get install coinor-cbc
# o
brew install cbc
```

## Instalación y ejecución

### 1) Clonar el repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd project_perth_ruta_optima
```

### 2) Backend

En Windows PowerShell:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

La API quedará disponible en:

- http://127.0.0.1:5000

### 3) Frontend

En otra terminal:

```powershell
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

La interfaz queda en:

- http://localhost:5173

## Verificación rápida

### Validar backend

```powershell
curl http://127.0.0.1:5000/api/health
curl http://127.0.0.1:5000/api/suburbs
```

`/api/health` responde `{"status": "ok", ...}` y `/api/suburbs` devuelve la lista de
distritos disponibles junto con cuántas viviendas aporta cada uno:

```json
{
  "suburbs": ["Alexander Heights", "..."],
  "details": [{ "name": "Alexander Heights", "n_houses": 96 }]
}
```

### Validar ruta

```powershell
curl "http://127.0.0.1:5000/api/route?suburb=Claremont&mode=heuristic"
```

Errores previstos de la API (siempre en JSON, nunca como traza HTML):

| Situación | Código | Cuerpo |
|---|---|---|
| Suburbio inexistente o sin coordenadas | 404 | `{"error": "No se encontraron viviendas para el suburbio '...'."}` |
| `mode` distinto de `heuristic`/`exact` | 400 | `{"error": "Modo de solución no válido: '...'"}` |
| CBC no instalado y `mode=exact` | 503 | `{"error": "No se encontró el ejecutable CBC..."}` |

### Validar exactamente el modelo exacto sobre un subconjunto pequeño

Se puede ejecutar el script:

```powershell
cd backend
python run_demo.py
```

Genera `outputs/route_result.json` y `outputs/execution_log.txt`.

### Pruebas automatizadas

```powershell
cd backend
python -m unittest discover -s tests -t .
```

Las pruebas del modelo exacto se omiten automáticamente (`skip`) si CBC no está
instalado, de modo que la suite pasa entera tanto con solver como sin él.

## Evidencia de ejecución real

La ejecución del script de demostración generó resultados reales, por ejemplo:

```text
[Paso 3] Modelo exacto (MTZ) resuelto sobre 9 viviendas en 0.161 s
          Estado del solver: optimal
          Distancia óptima: 3.289 km

[Paso 4] Heurística NN + 2-opt resuelta sobre 14 viviendas en 0.001 s
          Distancia ruta mejorada (2-opt): 3.891 km
          Tiempo estimado de recorrido (con buffers): 217.8 min

[Paso 5] Validación sobre el mismo subconjunto de 9 viviendas:
          Óptimo exacto (MTZ):        3.289 km
          Heurística (NN + 2-opt):    3.289 km
          Brecha de optimalidad:      0.00 %
```

Esto demuestra que:

- el modelo exacto funciona sobre instancias pequeñas,
- la heurística reproduce el óptimo en el conjunto validado,
- y la solución tiene sentido desde el punto de vista práctico.

## Despliegue

### Frontend en Vercel

1. Crear un repositorio en GitHub.
2. Importar el proyecto en Vercel.
3. Configurar el proyecto frontend como una app Vite.
4. Seleccionar la carpeta `frontend` como directorio raíz.
5. Build command: `npm install && npm run build`
6. Output directory: `dist`
7. Variable de entorno: `VITE_API_BASE=https://<tu-api>.onrender.com`

### Backend en Render / Railway / PythonAnywhere

El backend Python con CBC debe desplegarse en una plataforma que permita ejecutar un proceso backend nativo con dependencias del sistema.

Se recomienda:

- Render
- Railway
- PythonAnywhere

Para este caso, la parte visual se despliega en Vercel y la API en una plataforma con soporte para Python.

El `Dockerfile` del backend instala CBC y arranca la API con **gunicorn**:

```bash
gunicorn -w 2 -t 120 -b 0.0.0.0:$PORT app:app
```

El servidor de desarrollo de Flask (`python app.py`) es solo para trabajar en local.
Su modo debug expone la consola interactiva de Werkzeug, que permite ejecutar código
arbitrario en el servidor; por eso viene apagado por defecto y solo se activa con
`FLASK_DEBUG=1`.

### Variables de entorno del backend

| Variable | Por defecto | Para qué sirve |
|---|---|---|
| `DATA_DIR` | `./data` | Carpeta de CSVs que se cargan y concatenan. |
| `DATA_SOURCE_URL` | — | CSV remoto opcional que se añade al dataset local. |
| `MAX_EXACT_HOUSES` | `15` | Tamaño máximo de la instancia del modelo exacto. |
| `CORS_ORIGINS` | `*` | Orígenes permitidos; en producción, el dominio del frontend. |
| `FLASK_DEBUG` | `0` | Modo debug del servidor de desarrollo. Nunca activarlo en producción. |
| `PORT` | `5000` | Puerto de escucha. |

## GitHub y publicación

### Generar el repositorio local

```bash
git init
git add .
git commit -m "Initial commit"
```

### Conectar con GitHub

```bash
git branch -M main
git remote add origin <URL_DEL_REPOSITORIO_GITHUB>
git push -u origin main
```

## Conclusión

Este proyecto demuestra la aplicación práctica de la optimización en un problema real con datos geográficos de Perth. La solución combina rigor matemático con escalabilidad operativa: usa un modelo exacto para certificar la ruta óptima en instancias pequeñas y una heurística para resolver distribucciones más grandes de forma eficiente.

La combinación entre programación entera, cálculos geodésicos, Python, Pyomo, Flask, React y Leaflet convierte este proyecto en una demostración clara de cómo la optimización puede resolver problemas del mundo real con un impacto tangible.
