"""
app.py
-------
Capa de exposición de resultados (API). Es la única capa que conoce HTTP;
no calcula nada por sí misma, delega en optimization/*.

Endpoints:
    GET /api/suburbs
        Lista los suburbios disponibles en el dataset.
    GET /api/route?suburb=Nedlands&mode=heuristic|exact
        Calcula (o recupera desde caché en outputs/) la ruta óptima para
        el suburbio solicitado y la devuelve en JSON para que el frontend
        de React la dibuje sobre el mapa.

Ejecutar con:  python app.py   (sirve en http://localhost:5000)
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

load_dotenv()

from optimization.data_loader import (
    load_all_datasets,
    filter_by_suburb,
    houses_as_records,
)
from optimization.distances import build_distance_matrix
from optimization.exact_solver import solve_exact_tsp
from optimization.heuristic_solver import solve_heuristic_tsp

BASE_DIR = Path(__file__).parent
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
DATA_SOURCE_URL = os.getenv("DATA_SOURCE_URL")
MAX_EXACT_HOUSES = 15  # límite práctico del modelo MTZ exacto

app = Flask(__name__)
CORS(app)  # habilita que el frontend de React (otro puerto) consuma la API


def _prepare_exact_subset(houses: list[dict]) -> tuple[list[dict], bool]:
    """Devuelve un subconjunto manejable para el modelo exacto.

    El modelo MTZ es exacto pero combinatorial: su coste crece muy rápido con el
    número de viviendas. Para distritos grandes se trabaja con un subconjunto de
    hasta 15 viviendas y se mantiene la heurística para el conjunto completo.
    """
    if len(houses) <= MAX_EXACT_HOUSES:
        return houses, False
    return houses[:MAX_EXACT_HOUSES], True


@app.get("/api/suburbs")
def list_suburbs():
    df = load_all_datasets(DATA_DIR, source_url=DATA_SOURCE_URL)
    suburbs = sorted(df["suburb"].unique().tolist())
    return jsonify({"suburbs": suburbs})


@app.get("/api/route")
def get_route():
    suburb = request.args.get("suburb", "Nedlands")
    mode = request.args.get("mode", "heuristic")  # "heuristic" | "exact"

    df = load_all_datasets(DATA_DIR, source_url=DATA_SOURCE_URL)
    df_suburb = filter_by_suburb(df, suburb)
    houses = houses_as_records(df_suburb)

    if mode == "exact":
        exact_houses, used_subset = _prepare_exact_subset(houses)
        exact_matrix = build_distance_matrix(exact_houses)
        try:
            result = solve_exact_tsp(exact_matrix, solver_name="cbc")
        except RuntimeError as exc:
            return jsonify({"error": str(exc)}), 500

        ordered_houses = [exact_houses[i] for i in result["route_index"]]
        return jsonify({
            "suburb": suburb,
            "mode": mode,
            "n_houses": len(houses),
            "exact_subset_used": used_subset,
            "exact_subset_size": len(exact_houses),
            "message": (
                "El modelo exacto MTZ se aplica sobre un subconjunto de hasta "
                f"{MAX_EXACT_HOUSES} viviendas porque es un problema combinatorio. "
                "Para el distrito completo se usa la heurística."
            ) if used_subset else "Se resolvió el modelo exacto MTZ sobre el distrito completo.",
            "total_distance_km": result["total_distance_km"],
            "route": ordered_houses,
            "raw_result": result,
        })

    matrix = build_distance_matrix(houses)
    result = solve_heuristic_tsp(matrix)
    ordered_houses = [houses[i] for i in result["route_index"]]

    return jsonify({
        "suburb": suburb,
        "mode": mode,
        "n_houses": len(houses),
        "total_distance_km": result["total_distance_km"],
        "route": ordered_houses,
        "raw_result": result,
    })


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
