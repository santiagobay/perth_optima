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
import numpy as np
import pandas as pd
from pathlib import Path
from geopy.distance import geodesic


def build_distance_matrix(houses: list[dict]) -> np.ndarray:
    """Calcula la matriz simétrica n x n de distancias geodésicas (km).

    Cada entrada D[i][j] es la distancia geodésica, en línea recta sobre
    la superficie terrestre, entre la vivienda i y la vivienda j, calculada
    con la fórmula de Vincenty/geodésica implementada en geopy.distance.
    Es precisamente esta matriz la que se usa como matriz de costos c_ij
    del modelo de asignación con eliminación de subtours (sección 3.3 del
    documento de la Fase 3).
    """
    n = len(houses)
    matrix = np.zeros((n, n))

    coords = [(h["latitude"], h["longitude"]) for h in houses]

    for i in range(n):
        for j in range(n):
            if i != j:
                matrix[i][j] = geodesic(coords[i], coords[j]).kilometers

    return matrix


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
