"""
data_loader.py
----------------
Capa de acceso a datos del proyecto "Optimización de la ruta de visita a
propiedades residenciales en Perth, Australia".

Responsabilidad única: leer los archivos planos (CSV) del conjunto de datos
Perth House Prices (Syuzai, s. f.), normalizarlos, filtrarlos por suburbio y
devolver una estructura limpia y validada, lista para que la capa de
optimización (distances.py, exact_solver.py, heuristic_solver.py) la consuma.

No calcula distancias ni resuelve ningún modelo: esa separación de
responsabilidades es la que sustenta, en el documento de la Fase 3, la
afirmación de que el sistema desarrollado sigue un flujo de entrada -
transformación - salida propio de un sistema lineal de procesamiento de
datos.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = [
    "house_id", "address", "suburb", "price",
    "bedrooms", "bathrooms", "land_area", "floor_area",
    "latitude", "longitude",
]

# El orden de cada lista es el orden de prioridad: gana el primer alias
# presente en el CSV. (Antes se iteraba sobre un conjunto, por lo que la
# columna elegida era arbitraria cuando un dataset traía dos aliases.)
COLUMN_ALIASES = {
    "house_id": ["house_id", "property_id", "id"],
    "address": ["address", "street_address", "street_name", "street"],
    "suburb": ["suburb", "suburb_name", "locality", "municipality"],
    "price": ["price", "sale_price", "property_price"],
    "bedrooms": ["bedrooms", "beds"],
    "bathrooms": ["bathrooms", "baths"],
    "land_area": ["land_area", "lot_area", "land_size"],
    "floor_area": ["floor_area", "building_area", "house_area"],
    "latitude": ["latitude", "lat"],
    "longitude": ["longitude", "lon", "lng"],
}

NUMERIC_COLUMNS = [
    "price", "bedrooms", "bathrooms", "land_area", "floor_area",
    "latitude", "longitude",
]

# Caché en memoria del dataset consolidado. El CSV completo de Perth tiene
# ~33.600 filas: releerlo y re-normalizarlo en cada petición HTTP era el
# principal cuello de botella de la API.
_DATASET_CACHE: dict = {}


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza aliases comunes de columnas para aceptar datasets reales.

    Permite que CSVs reales de Perth o de portales inmobiliarios usen nombres
    ligeramente distintos a la estructura interna del proyecto e incluso en
    mayúsculas.
    """
    normalized = df.copy()
    normalized.columns = [str(c).strip().lower() for c in normalized.columns]

    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            alias = alias.lower()
            if alias in normalized.columns:
                if alias != canonical:
                    normalized[canonical] = normalized[alias]
                break

    if "house_id" not in normalized.columns:
        normalized["house_id"] = [f"H{i:04d}" for i in range(1, len(normalized) + 1)]
    if "address" not in normalized.columns:
        normalized["address"] = "Dirección no disponible"
    if "price" not in normalized.columns:
        normalized["price"] = 0

    for col in ["bedrooms", "bathrooms", "land_area", "floor_area"]:
        if col not in normalized.columns:
            normalized[col] = pd.NA

    for required in ["suburb", "latitude", "longitude"]:
        if required not in normalized.columns:
            normalized[required] = pd.NA

    return normalized


def _finalize_frame(df: pd.DataFrame, origin: str) -> pd.DataFrame:
    """Valida y limpia un DataFrame ya normalizado.

    Se aplica por igual a los CSV locales y a la fuente remota opcional
    (DATA_SOURCE_URL). Antes solo los locales pasaban por esta limpieza, así
    que un dataset remoto podía llegar a la capa de optimización con valores
    nulos o con coordenadas en formato texto.
    """
    missing = [c for c in ["suburb", "latitude", "longitude", "address"] if c not in df.columns]
    if missing:
        raise ValueError(f"Al dataset '{origin}' le faltan columnas requeridas: {missing}")

    df["suburb"] = df["suburb"].fillna("Desconocido").astype(str).str.strip()
    df["address"] = df["address"].fillna("Dirección no disponible").astype(str).str.strip()
    df["house_id"] = df["house_id"].astype(str).str.strip()

    # Las coordenadas y los campos numéricos deben serlo de verdad: un CSV
    # real puede traerlos como texto o con celdas vacías, y geopy fallaba
    # después con un error opaco.
    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def list_data_files(base_dir: str | Path | None = None) -> list[Path]:
    """Devuelve todos los CSV disponibles en la carpeta de datos.

    Si el proyecto crece con varios archivos por municipio, esta función
    permite cargar datos reales de distintas zonas sin depender de un solo
    CSV fijo.
    """
    if base_dir is None:
        base_dir = Path(__file__).resolve().parents[1] / "data"
    data_dir = Path(base_dir)
    if not data_dir.exists():
        return []
    return sorted(data_dir.glob("*.csv"))


def load_dataset(csv_path: str | Path) -> pd.DataFrame:
    """Carga un CSV y valida que contenga la estructura mínima necesaria.

    Acepta tanto datasets locales como datasets reales con columnas similares.
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo de datos: {csv_path}")

    df = _normalize_columns(pd.read_csv(csv_path))
    return _finalize_frame(df, origin=csv_path.name)


def _cache_signature(files: list[Path], source_url: str | None) -> tuple:
    stamps = []
    for path in files:
        stat = path.stat()
        stamps.append((str(path), stat.st_mtime_ns, stat.st_size))
    return (tuple(stamps), source_url)


def load_all_datasets(
    base_dir: str | Path | None = None,
    source_url: str | None = None,
    use_cache: bool = True,
) -> pd.DataFrame:
    """Carga y concatena todos los CSVs de la carpeta de datos y, opcionalmente,
    añade una fuente remota configurada por URL.

    El resultado se cachea en memoria y se invalida solo si cambia el tamaño o
    la fecha de modificación de algún CSV. El DataFrame devuelto debe tratarse
    como de solo lectura: los consumidores (filter_by_suburb) trabajan sobre
    una copia.
    """
    files = list_data_files(base_dir)

    signature = None
    if use_cache and files:
        signature = _cache_signature(files, source_url)
        cached = _DATASET_CACHE.get(signature)
        if cached is not None:
            return cached

    frames = [load_dataset(path) for path in files]

    if source_url:
        remote_df = _normalize_columns(pd.read_csv(source_url))
        frames.append(_finalize_frame(remote_df, origin=source_url))

    if not frames:
        raise FileNotFoundError(
            "No se encontraron datasets CSV en la carpeta data/ ni una fuente remota configurada."
        )

    merged = pd.concat(frames, ignore_index=True)

    if signature is not None:
        _DATASET_CACHE.clear()  # solo se conserva la última versión del dataset
        _DATASET_CACHE[signature] = merged

    return merged


def clear_dataset_cache() -> None:
    """Invalida la caché en memoria (útil en tests y al recargar datos)."""
    _DATASET_CACHE.clear()


def available_suburbs(df: pd.DataFrame) -> list[dict]:
    """Devuelve los suburbios con coordenadas utilizables y cuántas viviendas
    aporta cada uno, para que el frontend pueda mostrar el tamaño de la
    instancia antes de lanzar el cálculo."""
    usable = df.dropna(subset=["latitude", "longitude"])
    usable = usable.drop_duplicates(subset=["suburb", "latitude", "longitude"])
    counts = usable["suburb"].value_counts().sort_index()
    return [{"name": str(name), "n_houses": int(count)} for name, count in counts.items()]


def filter_by_suburb(df: pd.DataFrame, suburb: str) -> pd.DataFrame:
    """Filtra el dataset por un distrito (suburbio) específico.

    Además de filtrar, elimina registros con coordenadas nulas, fuera de rango
    o duplicadas, tal como se describió en el Paso 1 del proceso metodológico
    de la etapa de profundización.
    """
    subset = df[df["suburb"].astype(str).str.lower() == str(suburb).strip().lower()].copy()

    subset = subset.dropna(subset=["latitude", "longitude"])
    subset = subset[
        subset["latitude"].between(-90, 90) & subset["longitude"].between(-180, 180)
    ]
    subset = subset.drop_duplicates(subset=["latitude", "longitude"])
    subset = subset.reset_index(drop=True)

    if subset.empty:
        raise ValueError(f"No se encontraron viviendas para el suburbio '{suburb}'.")

    return subset


def _json_safe(value):
    """Convierte NaN/NA y tipos de numpy en valores serializables por JSON.

    Sin esto, un dataset con celdas vacías producía ``NaN`` (JSON inválido:
    ``response.json()`` falla en el navegador) o ``pd.NA`` (error 500 al
    serializar la respuesta).
    """
    if value is None or value is pd.NA:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, np.generic):
        value = value.item()
        if isinstance(value, float) and math.isnan(value):
            return None
        return value
    return value


def houses_as_records(df: pd.DataFrame) -> list[dict]:
    """Convierte el DataFrame filtrado en una lista de diccionarios
    (formato que consumirá tanto la API de Flask como el frontend de React).
    """
    df = df.copy()

    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            if col == "house_id":
                df[col] = [f"H{i:04d}" for i in range(1, len(df) + 1)]
            elif col == "address":
                df[col] = "Dirección no disponible"
            else:
                df[col] = pd.NA

    records = df[REQUIRED_COLUMNS].to_dict(orient="records")
    return [{k: _json_safe(v) for k, v in record.items()} for record in records]
