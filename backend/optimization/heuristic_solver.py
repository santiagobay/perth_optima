"""
heuristic_solver.py
---------------------
Capa de optimización (parte 3): heurística constructiva de vecino más
cercano, mejorada con búsqueda local 2-opt, tal como se planteó en la
Alternativa 2 de la etapa de contextualización.

Este módulo es el que se usa en producción sobre el distrito completo
(hasta ~100 viviendas), mientras que exact_solver.py se reserva para
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


def nearest_neighbor_route(distance_matrix: np.ndarray, start: int = 0) -> list[int]:
    """Construye una ruta inicial factible con la heurística de vecino
    más cercano: en cada paso visita la vivienda no visitada más cercana
    a la vivienda actual."""
    n = distance_matrix.shape[0]
    visited = [False] * n
    route = [start]
    visited[start] = True
    current = start

    for _ in range(n - 1):
        nearest, best_dist = None, float("inf")
        for j in range(n):
            if not visited[j] and distance_matrix[current][j] < best_dist:
                nearest, best_dist = j, distance_matrix[current][j]
        route.append(nearest)
        visited[nearest] = True
        current = nearest

    route.append(start)
    return route


def route_length(route: list[int], distance_matrix: np.ndarray) -> float:
    return sum(distance_matrix[route[k]][route[k + 1]] for k in range(len(route) - 1))


def two_opt(route: list[int], distance_matrix: np.ndarray, max_iterations: int = 200) -> list[int]:
    """Búsqueda local por intercambio de arcos (2-opt): mientras exista
    un intercambio que reduzca la distancia total, se aplica, hasta que
    no haya mejora o se alcance el número máximo de iteraciones."""
    best = route[:]
    best_length = route_length(best, distance_matrix)
    improved = True
    iterations = 0

    while improved and iterations < max_iterations:
        improved = False
        iterations += 1
        for a in range(1, len(best) - 2):
            for b in range(a + 1, len(best) - 1):
                candidate = best[:a] + best[a:b + 1][::-1] + best[b + 1:]
                candidate_length = route_length(candidate, distance_matrix)
                if candidate_length < best_length:
                    best, best_length = candidate, candidate_length
                    improved = True
    return best


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


def solve_heuristic_tsp(distance_matrix: np.ndarray, start: int = 0) -> dict:
    """Orquesta la heurística completa: construcción + mejora 2-opt."""
    initial_route = nearest_neighbor_route(distance_matrix, start)
    improved_route = two_opt(initial_route, distance_matrix)

    return {
        "route_index": improved_route,
        "total_distance_km": round(route_length(improved_route, distance_matrix), 3),
        "initial_distance_km": round(route_length(initial_route, distance_matrix), 3),
        "estimated_time_minutes": estimate_travel_time_minutes(improved_route, distance_matrix),
        "n_houses": distance_matrix.shape[0],
    }
