"""
heuristic_solver.py
---------------------
Capa de optimización (parte 3): heurística constructiva de vecino más
cercano, mejorada con búsqueda local 2-opt, tal como se planteó en la
Alternativa 2 de la etapa de contextualización.

Este módulo es el que se usa en producción sobre el distrito completo
(hasta ~250 viviendas), mientras que exact_solver.py se reserva para
validar la calidad de esta heurística sobre subconjuntos pequeños
(Paso 5 del proceso metodológico: comparación y validación de resultados).

Además de la distancia, se incorpora un tiempo de "buffer" entre visitas
(15 minutos dentro del mismo sector, 45 minutos entre sectores lejanos),
criterio tomado de la práctica documentada por Zeo Route Planner (2026)
para agentes inmobiliarios reales.
"""

from __future__ import annotations

import numpy as np

BUFFER_NEAR_MIN = 15   # minutos, viviendas a menos de 1.5 km
BUFFER_FAR_MIN = 45    # minutos, viviendas a 1.5 km o más
NEAR_THRESHOLD_KM = 1.5
AVG_URBAN_SPEED_KMH = 30  # velocidad urbana promedio usada para estimar tiempo de viaje

DEFAULT_MULTI_STARTS = 8  # número máximo de puntos de arranque distintos
_EPS = 1e-12


def nearest_neighbor_route(distance_matrix: np.ndarray, start: int = 0) -> list[int]:
    """Construye una ruta inicial factible con la heurística de vecino
    más cercano: en cada paso visita la vivienda no visitada más cercana
    a la vivienda actual."""
    n = distance_matrix.shape[0]
    if n == 0:
        raise ValueError("La matriz de distancias está vacía.")
    if not 0 <= start < n:
        raise ValueError(f"El índice de inicio {start} está fuera de rango (n={n}).")

    unvisited = np.ones(n, dtype=bool)
    unvisited[start] = False
    route = [start]
    current = start

    for _ in range(n - 1):
        candidates = np.where(unvisited, distance_matrix[current], np.inf)
        nearest = int(np.argmin(candidates))
        route.append(nearest)
        unvisited[nearest] = False
        current = nearest

    route.append(start)
    return route


def route_length(route: list[int], distance_matrix: np.ndarray) -> float:
    return float(sum(distance_matrix[route[k]][route[k + 1]] for k in range(len(route) - 1)))


def two_opt(route: list[int], distance_matrix: np.ndarray, max_iterations: int = 200) -> list[int]:
    """Búsqueda local por intercambio de arcos (2-opt): mientras exista
    un intercambio que reduzca la distancia total, se aplica, hasta que
    no haya mejora o se alcance el número máximo de pasadas.

    La ganancia de cada intercambio se evalúa con los cuatro arcos que
    cambian en lugar de recalcular la longitud completa de la ruta
    candidata. Eso baja cada pasada de O(n^3) a O(n^2): para un distrito
    de ~230 viviendas la diferencia es de minutos a milisegundos.
    """
    best = list(route)
    m = len(best)
    improved = True
    iterations = 0

    while improved and iterations < max_iterations:
        improved = False
        iterations += 1
        for a in range(1, m - 2):
            for b in range(a + 1, m - 1):
                prev_a, node_a = best[a - 1], best[a]
                node_b, next_b = best[b], best[b + 1]
                # Invertir el tramo [a, b] sustituye los arcos
                # (prev_a, node_a) y (node_b, next_b) por
                # (prev_a, node_b) y (node_a, next_b).
                delta = (
                    distance_matrix[prev_a, node_b] + distance_matrix[node_a, next_b]
                    - distance_matrix[prev_a, node_a] - distance_matrix[node_b, next_b]
                )
                if delta < -_EPS:
                    best[a:b + 1] = best[a:b + 1][::-1]
                    improved = True

    return best


def rotate_to_start(tour: list[int], start: int) -> list[int]:
    """Rota un tour cerrado para que empiece (y termine) en `start`.

    Un tour es un ciclo: el nodo por el que se empieza a describirlo no
    cambia su longitud, pero sí la lectura de la ruta en el mapa.
    """
    cycle = tour[:-1] if len(tour) > 1 and tour[0] == tour[-1] else list(tour)
    if start not in cycle:
        raise ValueError(f"El nodo {start} no pertenece al tour.")
    pivot = cycle.index(start)
    rotated = cycle[pivot:] + cycle[:pivot]
    return rotated + [start]


def estimate_travel_time_minutes(route: list[int], distance_matrix: np.ndarray) -> float:
    """Estima el tiempo total del recorrido sumando tiempo de
    desplazamiento (a velocidad urbana promedio) más el tiempo de buffer
    por visita, según la distancia entre viviendas consecutivas."""
    total_minutes = 0.0
    for k in range(len(route) - 1):
        d = distance_matrix[route[k]][route[k + 1]]
        travel_minutes = (d / AVG_URBAN_SPEED_KMH) * 60
        buffer_minutes = BUFFER_NEAR_MIN if d < NEAR_THRESHOLD_KM else BUFFER_FAR_MIN
        total_minutes += travel_minutes + buffer_minutes
    return round(total_minutes, 1)


def solve_heuristic_tsp(
    distance_matrix: np.ndarray,
    start: int = 0,
    n_starts: int = DEFAULT_MULTI_STARTS,
) -> dict:
    """Orquesta la heurística completa: construcción + mejora 2-opt.

    Se prueban varios puntos de arranque para el vecino más cercano (la
    heurística es muy sensible al nodo inicial), se aplica 2-opt a cada uno
    y se conserva el mejor tour, rotándolo al final para que la ruta que ve
    el usuario siga empezando y terminando en `start`.
    """
    n = int(distance_matrix.shape[0])
    if n == 0:
        raise ValueError("La matriz de distancias está vacía.")
    if not 0 <= start < n:
        raise ValueError(f"El índice de inicio {start} está fuera de rango (n={n}).")

    if n == 1:
        return {
            "route_index": [start, start],
            "total_distance_km": 0.0,
            "initial_distance_km": 0.0,
            "estimated_time_minutes": 0.0,
            "n_houses": n,
            "n_starts_evaluated": 1,
        }

    initial_route = nearest_neighbor_route(distance_matrix, start)
    initial_length = route_length(initial_route, distance_matrix)

    # Puntos de arranque repartidos de forma uniforme, incluyendo siempre el
    # solicitado por quien llama.
    n_starts = max(1, min(int(n_starts), n))
    step = max(1, n // n_starts)
    starts = sorted({start, *[i % n for i in range(0, n, step)]})[:n_starts]
    if start not in starts:
        starts[0] = start

    best_tour = None
    best_length = float("inf")
    for s in starts:
        candidate = two_opt(nearest_neighbor_route(distance_matrix, s), distance_matrix)
        candidate_length = route_length(candidate, distance_matrix)
        if candidate_length < best_length:
            best_tour, best_length = candidate, candidate_length

    improved_route = rotate_to_start(best_tour, start)

    return {
        "route_index": improved_route,
        "total_distance_km": round(best_length, 3),
        "initial_distance_km": round(initial_length, 3),
        "estimated_time_minutes": estimate_travel_time_minutes(improved_route, distance_matrix),
        "n_houses": n,
        "n_starts_evaluated": len(starts),
    }
