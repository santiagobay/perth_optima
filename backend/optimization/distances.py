"""
distances.py
-------------
Capa de optimización (parte 1): construcción de la matriz de costos.

Usa geopy.distance para calcular la distancia geodésica (en kilómetros)
entre cada par de viviendas de un mismo suburbio, tal como lo exige el
enunciado del escenario social (Kaggle, dataset Perth House Prices).

La matriz resultante se guarda en un archivo de texto plano (CSV), lo cual
cumple con el criterio del curso de "utilizar flujos de datos de entrada
y salida para almacenar y recuperar información en archivos de texto
plano y binarios".
"""

from __future__ import annotations

from collections import OrderedDict
from pathlib import Path

import numpy as np
import pandas as pd
from geopy.distance import geodesic

# Caché de matrices ya calculadas, indexada por las coordenadas del conjunto
# de viviendas. Recalcular una matriz de 230x230 implica ~26.000 llamadas a
# geopy, así que repetir el mismo suburbio no debe volver a pagarlo.
_MATRIX_CACHE: "OrderedDict[tuple, np.ndarray]" = OrderedDict()
_MATRIX_CACHE_MAX_ENTRIES = 16


def _coords_of(houses: list[dict]) -> list[tuple[float, float]]:
    return [(float(h["latitude"]), float(h["longitude"])) for h in houses]


def build_distance_matrix(houses: list[dict]) -> np.ndarray:
    """Calcula la matriz simétrica n x n de distancias geodésicas (km).

    Cada entrada D[i][j] es la distancia geodésica, en línea recta sobre
    la superficie terrestre, entre la vivienda i y la vivienda j, calculada
    con la fórmula geodésica implementada en geopy.distance. Es precisamente
    esta matriz la que se usa como matriz de costos c_ij del modelo de
    asignación con eliminación de subtours (sección 3.3 del documento de la
    Fase 3).

    Como la distancia geodésica es simétrica, solo se calcula el triángulo
    superior y se refleja: la mitad de llamadas a geopy que antes.
    """
    coords = _coords_of(houses)
    n = len(coords)
    matrix = np.zeros((n, n))

    for i in range(n):
        for j in range(i + 1, n):
            d = geodesic(coords[i], coords[j]).kilometers
            matrix[i, j] = d
            matrix[j, i] = d

    return matrix


def build_distance_matrix_cached(houses: list[dict]) -> np.ndarray:
    """Igual que build_distance_matrix, pero memoiza por conjunto de
    coordenadas. Pensada para la API, donde el mismo distrito se consulta
    muchas veces."""
    key = tuple(_coords_of(houses))
    cached = _MATRIX_CACHE.get(key)
    if cached is not None:
        _MATRIX_CACHE.move_to_end(key)
        return cached

    matrix = build_distance_matrix(houses)
    _MATRIX_CACHE[key] = matrix
    while len(_MATRIX_CACHE) > _MATRIX_CACHE_MAX_ENTRIES:
        _MATRIX_CACHE.popitem(last=False)
    return matrix


def clear_matrix_cache() -> None:
    """Vacía la caché de matrices (útil en tests)."""
    _MATRIX_CACHE.clear()


def select_central_subset(houses: list[dict], k: int) -> list[dict]:
    """Devuelve las k viviendas más cercanas al centroide del distrito.

    El modelo exacto solo puede resolverse sobre un subconjunto pequeño.
    Tomar simplemente las k primeras filas del CSV daba un subconjunto
    arbitrario y geográficamente disperso; tomar el núcleo del distrito
    produce una instancia representativa y una ruta que tiene sentido al
    dibujarla en el mapa.
    """
    if k >= len(houses):
        return list(houses)

    coords = _coords_of(houses)
    centroid = (
        sum(c[0] for c in coords) / len(coords),
        sum(c[1] for c in coords) / len(coords),
    )
    order = sorted(
        range(len(houses)),
        key=lambda i: geodesic(centroid, coords[i]).kilometers,
    )
    keep = sorted(order[:k])  # se conserva el orden original del dataset
    return [houses[i] for i in keep]


def save_distance_matrix(matrix: np.ndarray, houses: list[dict], out_path: str | Path) -> None:
    """Persiste la matriz de distancias en un archivo CSV legible,
    usando los house_id como encabezados de fila y columna."""
    ids = [h["house_id"] for h in houses]
    df = pd.DataFrame(matrix, index=ids, columns=ids)
    df.to_csv(out_path)


def load_distance_matrix(path: str | Path) -> np.ndarray:
    """Recupera una matriz de distancias previamente calculada, evitando
    tener que volver a invocar geopy en cada ejecución (persistencia)."""
    df = pd.read_csv(path, index_col=0)
    return df.to_numpy()
