"""
data_loader.py
----------------
Capa de acceso a datos del proyecto "Optimización de la ruta de visita a
propiedades residenciales en Perth, Australia".

Responsabilidad única: leer el archivo plano (CSV) del conjunto de datos
Perth House Prices (Syuzai, s. f.), filtrarlo por suburbio y devolver una
estructura limpia y validada, lista para que la capa de optimización
(distances.py, exact_solver.py, heuristic_solver.py) la consuma.

No calcula distancias ni resuelve ningún modelo: esa separación de
responsabilidades es la que sustenta, en el documento de la Fase 3, la
afirmación de que el sistema desarrollado sigue un flujo de entrada -
transformación - salida propio de un sistema lineal de procesamiento de
datos.
"""

from __future__ import annotations
import os
from pathlib import Path
import pandas as pd

REQUIRED_COLUMNS = [
    "house_id", "address", "suburb", "price",
    "bedrooms", "bathrooms", "land_area", "floor_area",
    "latitude", "longitude",
]

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


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza aliases comunes de columnas para aceptar datasets reales.

    Permite que CSVs reales de Perth o de portales inmobiliarios usen nombres
    ligeramente distintos a la estructura interna del proyecto e incluso en
    mayúsculas.
    """
    normalized = df.copy()
    normalized.columns = [str(c).strip().lower() for c in normalized.columns]

    for canonical, aliases in COLUMN_ALIASES.items():
        alias_candidates = {a.lower() for a in aliases}
        for alias in alias_candidates:
            if alias in normalized.columns:
                normalized[canonical] = normalized[alias]
                break

    if "house_id" not in normalized.columns:
        normalized["house_id"] = [f"H{i:04d}" for i in range(1, len(normalized) + 1)]
    if "address" not in normalized.columns:
        normalized["address"] = normalized.get("street_address", "Dirección no disponible")
    if "price" not in normalized.columns:
        normalized["price"] = 0

    for col in ["bedrooms", "bathrooms", "land_area", "floor_area"]:
        if col not in normalized.columns:
            normalized[col] = pd.NA

    for required in ["suburb", "latitude", "longitude"]:
        if required not in normalized.columns:
            normalized[required] = pd.NA

    return normalized


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

    df = pd.read_csv(csv_path)
    df = _normalize_columns(df)

    missing = [c for c in ["suburb", "latitude", "longitude", "address"] if c not in df.columns]
    if missing:
        raise ValueError(f"Al dataset le faltan columnas requeridas: {missing}")

    # Normaliza también valores de texto para que no haya entradas nulas o en
    # formato inconsistente en datasets reales.
    df["suburb"] = df["suburb"].fillna("Desconocido").astype(str).str.strip()
    df["address"] = df["address"].fillna("Dirección no disponible").astype(str).str.strip()
    return df


def load_all_datasets(base_dir: str | Path | None = None, source_url: str | None = None) -> pd.DataFrame:
    """Carga y concatena todos los CSVs de la carpeta de datos y, opcionalmente,
    añade una fuente remota configurada por URL.

    Esto permite conectar la app a un dataset real de Perth sin dejar de soportar
    un conjunto local de CSVs por municipio.
    """
    files = list_data_files(base_dir)
    frames = []

    for path in files:
        frames.append(load_dataset(path))

    if source_url:
        remote_df = pd.read_csv(source_url)
        frames.append(_normalize_columns(remote_df))

    if not frames:
        raise FileNotFoundError("No se encontraron datasets CSV en la carpeta data/ ni una fuente remota configurada.")

    merged = pd.concat(frames, ignore_index=True)
    return merged


def filter_by_suburb(df: pd.DataFrame, suburb: str) -> pd.DataFrame:
    """Filtra el dataset por un distrito (suburbio) específico.

    Además de filtrar, elimina registros con coordenadas nulas o
    duplicadas, tal como se describió en el Paso 1 del proceso
    metodológico de la etapa de profundización.
    """
    subset = df[df["suburb"].astype(str).str.lower() == suburb.lower()].copy()

    subset = subset.dropna(subset=["latitude", "longitude"])
    subset = subset.drop_duplicates(subset=["latitude", "longitude"])
    subset = subset.reset_index(drop=True)

    if subset.empty:
        raise ValueError(f"No se encontraron viviendas para el suburbio '{suburb}'.")

    return subset


def houses_as_records(df: pd.DataFrame) -> list[dict]:
    """Convierte el DataFrame filtrado en una lista de diccionarios
    (formato que consumirá tanto la API de Flask como el frontend de React).
    """
    for col in ["house_id", "address", "suburb", "price", "bedrooms",
                "bathrooms", "land_area", "floor_area", "latitude", "longitude"]:
        if col not in df.columns:
            if col == "house_id":
                df[col] = [f"H{i:04d}" for i in range(1, len(df) + 1)]
            elif col == "address":
                df[col] = "Dirección no disponible"
            else:
                df[col] = pd.NA

    cols = ["house_id", "address", "suburb", "price", "bedrooms",
            "bathrooms", "land_area", "floor_area", "latitude", "longitude"]
    return df[cols].to_dict(orient="records")
