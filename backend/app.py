"""
app.py
-------
Capa de exposición de resultados (API). Es la única capa que conoce HTTP;
no calcula nada por sí misma, delega en optimization/*.

Endpoints:
    GET /api/health
        Comprobación de vida del servicio (útil para Render/Railway).
    GET /api/suburbs
        Lista los suburbios disponibles en el dataset y cuántas viviendas
        aporta cada uno.
    GET /api/route?suburb=Nedlands&mode=heuristic|exact
        Calcula la ruta óptima para el suburbio solicitado y la devuelve en
        JSON para que el frontend de React la dibuje sobre el mapa. El
        dataset y las matrices de distancias se memoizan en memoria.

Ejecutar con:  python app.py   (sirve en http://localhost:5000)
En producción:  gunicorn -w 2 -b 0.0.0.0:5000 app:app
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

load_dotenv()

from optimization.data_loader import (
    available_suburbs,
    filter_by_suburb,
    houses_as_records,
    load_all_datasets,
)
from optimization.distances import build_distance_matrix_cached, select_central_subset
from optimization.exact_solver import solve_exact_tsp
from optimization.heuristic_solver import estimate_travel_time_minutes, solve_heuristic_tsp

BASE_DIR = Path(__file__).parent
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
DATA_SOURCE_URL = os.getenv("DATA_SOURCE_URL")
MAX_EXACT_HOUSES = int(os.getenv("MAX_EXACT_HOUSES", "15"))  # límite práctico del MTZ exacto
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
VALID_MODES = ("heuristic", "exact")

app = Flask(__name__)
# Habilita que el frontend de React (otro puerto/dominio) consuma la API.
# En producción conviene restringirlo con CORS_ORIGINS=https://tu-app.vercel.app
CORS(app, resources={r"/api/*": {"origins": CORS_ORIGINS}})


class ApiError(Exception):
    """Error de negocio que la API traduce a una respuesta JSON."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@app.errorhandler(ApiError)
def handle_api_error(exc: ApiError):
    return jsonify({"error": exc.message}), exc.status_code


@app.errorhandler(404)
def handle_not_found(_exc):
    return jsonify({"error": "Recurso no encontrado."}), 404


def _load_dataset():
    try:
        return load_all_datasets(DATA_DIR, source_url=DATA_SOURCE_URL)
    except FileNotFoundError as exc:
        raise ApiError(str(exc), 503) from exc
    except ValueError as exc:
        raise ApiError(str(exc), 500) from exc


def _houses_for(suburb: str) -> list[dict]:
    df = _load_dataset()
    try:
        df_suburb = filter_by_suburb(df, suburb)
    except ValueError as exc:
        # Suburbio inexistente o sin coordenadas utilizables: es un 404,
        # no un error interno con traza HTML.
        raise ApiError(str(exc), 404) from exc
    return houses_as_records(df_suburb)


def _prepare_exact_subset(houses: list[dict]) -> tuple[list[dict], bool]:
    """Devuelve un subconjunto manejable para el modelo exacto.

    El modelo MTZ es exacto pero combinatorial: su coste crece muy rápido con el
    número de viviendas. Para distritos grandes se trabaja con las
    MAX_EXACT_HOUSES viviendas más cercanas al centro del distrito (un núcleo
    geográficamente coherente) y se mantiene la heurística para el conjunto
    completo.
    """
    if len(houses) <= MAX_EXACT_HOUSES:
        return houses, False
    return select_central_subset(houses, MAX_EXACT_HOUSES), True


@app.get("/")
@app.get("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "perth-optima-api",
        "endpoints": ["/api/health", "/api/suburbs", "/api/route"],
    })


@app.get("/api/suburbs")
def list_suburbs():
    df = _load_dataset()
    details = available_suburbs(df)
    return jsonify({
        "suburbs": [item["name"] for item in details],  # compatibilidad hacia atrás
        "details": details,
    })


@app.get("/api/route")
def get_route():
    suburb = request.args.get("suburb", "Nedlands")
    mode = request.args.get("mode", "heuristic")  # "heuristic" | "exact"

    if mode not in VALID_MODES:
        raise ApiError(
            f"Modo de solución no válido: '{mode}'. Usa uno de: {', '.join(VALID_MODES)}.",
            400,
        )

    houses = _houses_for(suburb)

    if mode == "exact":
        exact_houses, used_subset = _prepare_exact_subset(houses)
        exact_matrix = build_distance_matrix_cached(exact_houses)
        try:
            result = solve_exact_tsp(exact_matrix)
        except RuntimeError as exc:
            raise ApiError(str(exc), 503) from exc

        # Validación de la calidad de la heurística sobre la misma instancia
        # (Paso 5 del proceso metodológico).
        heuristic_on_subset = solve_heuristic_tsp(exact_matrix)
        optimal_km = result["total_distance_km"]
        gap = None
        if optimal_km > 0:
            gap = round(
                (heuristic_on_subset["total_distance_km"] - optimal_km) / optimal_km * 100, 2
            )

        ordered_houses = [exact_houses[i] for i in result["route_index"]]
        return jsonify({
            "suburb": suburb,
            "mode": mode,
            "n_houses": len(houses),
            "n_houses_in_route": len(exact_houses),
            "exact_subset_used": used_subset,
            "exact_subset_size": len(exact_houses),
            "message": (
                "El modelo exacto MTZ se aplica sobre un subconjunto de hasta "
                f"{MAX_EXACT_HOUSES} viviendas (las más céntricas del distrito) porque es un "
                "problema combinatorio. Para el distrito completo se usa la heurística."
            ) if used_subset else "Se resolvió el modelo exacto MTZ sobre el distrito completo.",
            "total_distance_km": optimal_km,
            "estimated_time_minutes": estimate_travel_time_minutes(
                result["route_index"], exact_matrix
            ),
            "heuristic_distance_km": heuristic_on_subset["total_distance_km"],
            "optimality_gap_percent": gap,
            "route": ordered_houses,
            "raw_result": result,
        })

    matrix = build_distance_matrix_cached(houses)
    result = solve_heuristic_tsp(matrix)
    ordered_houses = [houses[i] for i in result["route_index"]]

    return jsonify({
        "suburb": suburb,
        "mode": mode,
        "n_houses": len(houses),
        "n_houses_in_route": len(houses),
        "total_distance_km": result["total_distance_km"],
        "estimated_time_minutes": result["estimated_time_minutes"],
        "route": ordered_houses,
        "raw_result": result,
    })


if __name__ == "__main__":
    # El modo debug de Flask expone la consola interactiva de Werkzeug, que
    # permite ejecutar código arbitrario: nunca debe quedar activo en el
    # despliegue. Por eso se controla con una variable de entorno y viene
    # apagado por defecto.
    debug = os.getenv("FLASK_DEBUG", "0").lower() in ("1", "true", "yes", "on")
    port = int(os.getenv("PORT", "5000"))
    app.run(debug=debug, host="0.0.0.0", port=port)
