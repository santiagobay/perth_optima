"""
run_demo.py
-------------
Script de demostración de extremo a extremo. Ejecuta el pipeline completo
descrito en el proceso metodológico (sección 3.3) sobre el suburbio de
Nedlands (Perth, WA):

  Paso 1: extracción y limpieza de datos           -> data_loader.py
  Paso 2: construcción de la matriz de distancias   -> distances.py
  Paso 3: modelo exacto (MTZ) sobre un subconjunto  -> exact_solver.py
  Paso 4: heurística vecino más cercano + 2-opt     -> heuristic_solver.py
  Paso 5: comparación y cálculo de la brecha        -> este script
  Paso 6: persistencia de resultados en archivos    -> outputs/

Ejecutar con:  python run_demo.py
"""

import json
import time
from pathlib import Path

from optimization.data_loader import filter_by_suburb, houses_as_records, load_dataset
from optimization.distances import build_distance_matrix, save_distance_matrix
from optimization.exact_solver import solve_exact_tsp
from optimization.heuristic_solver import solve_heuristic_tsp

BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "data" / "perth_houses_nedlands.csv"
OUT_DIR = BASE_DIR / "outputs"
OUT_DIR.mkdir(exist_ok=True)

SUBURB = "Nedlands"
EXACT_SUBSET_SIZE = 9  # tamaño manejable para el modelo exacto (Alternativa 1)

_LOG_LINES: list[str] = []


def log(message: str = "") -> None:
    """Imprime por consola y acumula la línea para persistir el log completo.

    Antes outputs/execution_log.txt había que capturarlo a mano redirigiendo
    la salida; ahora el Paso 6 lo escribe como parte de la ejecución.
    """
    print(message)
    _LOG_LINES.append(message)


def main():
    log("=" * 70)
    log("PIPELINE DE OPTIMIZACIÓN DE RUTA — Perth House Prices")
    log(f"Suburbio seleccionado: {SUBURB}")
    log("=" * 70)

    # Paso 1 — Extracción y limpieza de datos
    df_raw = load_dataset(DATA_PATH)
    df_suburb = filter_by_suburb(df_raw, SUBURB)
    houses = houses_as_records(df_suburb)
    log(f"\n[Paso 1] Viviendas cargadas para '{SUBURB}': {len(houses)}")
    for h in houses:
        price = "n/d" if h["price"] is None else f"${h['price']:,.0f}"
        log(f"   {h['house_id']}  {h['address']:<20} "
            f"(lat={h['latitude']:.4f}, lon={h['longitude']:.4f})  {price}")

    # Paso 2 — Matriz de distancias
    t0 = time.time()
    matrix = build_distance_matrix(houses)
    save_distance_matrix(matrix, houses, OUT_DIR / "distance_matrix.csv")
    log(f"\n[Paso 2] Matriz de distancias {matrix.shape[0]}x{matrix.shape[1]} "
        f"calculada en {time.time() - t0:.3f} s")
    log(f"          Distancia máxima entre dos viviendas: {matrix.max():.3f} km")
    log(f"          Guardada en: {OUT_DIR / 'distance_matrix.csv'}")

    # Paso 3 — Modelo exacto (MTZ) sobre un subconjunto pequeño
    subset_houses = houses[:EXACT_SUBSET_SIZE]
    subset_matrix = build_distance_matrix(subset_houses)
    exact_result = None
    exact_route_ids: list[str] = []
    exact_time = 0.0
    try:
        t0 = time.time()
        exact_result = solve_exact_tsp(subset_matrix, solver_name="cbc")
        exact_time = time.time() - t0
    except RuntimeError as exc:
        # Sin CBC instalado el resto del pipeline sigue siendo demostrable.
        log(f"\n[Paso 3] Modelo exacto omitido: {exc}")

    if exact_result is not None:
        log(f"\n[Paso 3] Modelo exacto (MTZ) resuelto sobre {EXACT_SUBSET_SIZE} viviendas "
            f"en {exact_time:.3f} s")
        log(f"          Estado del solver: {exact_result['status']}")
        log(f"          Distancia óptima: {exact_result['total_distance_km']} km")
        exact_route_ids = [subset_houses[i]["house_id"] for i in exact_result["route_index"]]
        log(f"          Ruta óptima: {' -> '.join(exact_route_ids)}")

    # Paso 4 — Heurística vecino más cercano + 2-opt (distrito completo)
    t0 = time.time()
    heuristic_result = solve_heuristic_tsp(matrix, start=0)
    heuristic_time = time.time() - t0
    log(f"\n[Paso 4] Heurística NN + 2-opt resuelta sobre {len(houses)} viviendas "
        f"en {heuristic_time:.3f} s")
    log(f"          Distancia ruta inicial (vecino más cercano): "
        f"{heuristic_result['initial_distance_km']} km")
    log(f"          Distancia ruta mejorada (2-opt, "
        f"{heuristic_result['n_starts_evaluated']} arranques): "
        f"{heuristic_result['total_distance_km']} km")
    log(f"          Tiempo estimado de recorrido (con buffers): "
        f"{heuristic_result['estimated_time_minutes']} min")
    heuristic_route_ids = [houses[i]["house_id"] for i in heuristic_result["route_index"]]
    log(f"          Ruta heurística: {' -> '.join(heuristic_route_ids)}")

    # Paso 5 — Comparación y brecha de optimalidad (sobre el mismo subconjunto)
    heuristic_on_subset = solve_heuristic_tsp(subset_matrix, start=0)
    gap = None
    if exact_result is not None and exact_result["total_distance_km"] > 0:
        gap = (
            (heuristic_on_subset["total_distance_km"] - exact_result["total_distance_km"])
            / exact_result["total_distance_km"] * 100
        )
        log(f"\n[Paso 5] Validación sobre el mismo subconjunto de {EXACT_SUBSET_SIZE} viviendas:")
        log(f"          Óptimo exacto (MTZ):        {exact_result['total_distance_km']} km")
        log(f"          Heurística (NN + 2-opt):    {heuristic_on_subset['total_distance_km']} km")
        log(f"          Brecha de optimalidad:      {gap:.2f} %")
    else:
        log("\n[Paso 5] Validación omitida: no hay solución exacta con la que comparar.")

    # Paso 6 — Persistencia de resultados (JSON + log, consumidos luego por la API/React)
    output = {
        "suburb": SUBURB,
        "n_houses": len(houses),
        "houses": houses,
        "exact_solution": None if exact_result is None else {
            **exact_result,
            "route_house_ids": exact_route_ids,
            "subset_size": EXACT_SUBSET_SIZE,
            "solve_time_seconds": round(exact_time, 4),
        },
        "heuristic_solution": {
            **heuristic_result,
            "route_house_ids": heuristic_route_ids,
            "solve_time_seconds": round(heuristic_time, 4),
        },
        "validation_gap_percent": None if gap is None else round(gap, 2),
    }
    out_json = OUT_DIR / "route_result.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    log(f"\n[Paso 6] Resultados completos guardados en: {out_json}")
    log("=" * 70)
    log("EJECUCIÓN FINALIZADA CORRECTAMENTE")
    log("=" * 70)

    out_log = OUT_DIR / "execution_log.txt"
    out_log.write_text("\n".join(_LOG_LINES) + "\n", encoding="utf-8")
    print(f"Log de ejecución guardado en: {out_log}")


if __name__ == "__main__":
    main()
