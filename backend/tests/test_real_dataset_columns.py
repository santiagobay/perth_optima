import math
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from optimization.data_loader import (
    _normalize_columns,
    available_suburbs,
    filter_by_suburb,
    houses_as_records,
    load_dataset,
)


class TestRealDatasetColumns(unittest.TestCase):
    def test_uppercase_real_world_columns_are_normalized(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "real_perth.csv"
            pd.DataFrame([
                {
                    "ADDRESS": "1 Example Street",
                    "SUBURB": "Nedlands",
                    "PRICE": 500000,
                    "BEDROOMS": 3,
                    "BATHROOMS": 2,
                    "LAND_AREA": 600,
                    "FLOOR_AREA": 200,
                    "LATITUDE": -31.98,
                    "LONGITUDE": 115.79,
                }
            ]).to_csv(csv_path, index=False)

            df = load_dataset(csv_path)
            self.assertEqual(df["suburb"].iloc[0], "Nedlands")
            self.assertEqual(df["address"].iloc[0], "1 Example Street")
            self.assertAlmostEqual(float(df["latitude"].iloc[0]), -31.98)
            self.assertAlmostEqual(float(df["longitude"].iloc[0]), 115.79)

    def test_alias_priority_is_deterministic(self):
        """El alias canónico gana siempre sobre los secundarios.

        Antes los aliases se recorrían en un conjunto, así que con un CSV que
        traía 'address' y 'street_name' la columna elegida era arbitraria.
        """
        frame = pd.DataFrame([{
            "address": "1 Canonical St",
            "street_name": "Otro nombre",
            "suburb": "Subiaco",
            "latitude": -31.94,
            "longitude": 115.82,
        }])

        for _ in range(10):
            normalized = _normalize_columns(frame)
            self.assertEqual(normalized["address"].iloc[0], "1 Canonical St")

    def test_text_coordinates_are_coerced_and_invalid_rows_dropped(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "mixed.csv"
            pd.DataFrame([
                {"ADDRESS": "1 Good St", "SUBURB": "Subiaco",
                 "LATITUDE": "-31.9466", "LONGITUDE": "115.8275"},
                {"ADDRESS": "2 Bad St", "SUBURB": "Subiaco",
                 "LATITUDE": "sin dato", "LONGITUDE": "115.8291"},
                {"ADDRESS": "3 Out Of Range St", "SUBURB": "Subiaco",
                 "LATITUDE": "999", "LONGITUDE": "115.8300"},
            ]).to_csv(csv_path, index=False)

            df = load_dataset(csv_path)
            subset = filter_by_suburb(df, "subiaco")  # también case-insensitive

            self.assertEqual(len(subset), 1)
            self.assertEqual(subset["address"].iloc[0], "1 Good St")
            self.assertIsInstance(float(subset["latitude"].iloc[0]), float)

    def test_records_are_json_safe(self):
        """Ningún registro debe contener NaN ni pd.NA: romperían el JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "gaps.csv"
            pd.DataFrame([
                {"ADDRESS": "1 Gap St", "SUBURB": "Subiaco", "PRICE": None,
                 "LATITUDE": -31.9466, "LONGITUDE": 115.8275},
            ]).to_csv(csv_path, index=False)

            records = houses_as_records(filter_by_suburb(load_dataset(csv_path), "Subiaco"))

            self.assertEqual(len(records), 1)
            for key, value in records[0].items():
                self.assertFalse(
                    isinstance(value, float) and math.isnan(value),
                    f"El campo '{key}' llegó como NaN al JSON",
                )
            self.assertIsNone(records[0]["price"])

    def test_available_suburbs_reports_usable_house_counts(self):
        frame = pd.DataFrame([
            {"house_id": "A", "address": "1 St", "suburb": "Subiaco",
             "latitude": -31.94, "longitude": 115.82},
            {"house_id": "B", "address": "2 St", "suburb": "Subiaco",
             "latitude": -31.95, "longitude": 115.83},
            {"house_id": "C", "address": "3 St", "suburb": "Claremont",
             "latitude": None, "longitude": None},
        ])

        self.assertEqual(
            available_suburbs(frame), [{"name": "Subiaco", "n_houses": 2}]
        )


if __name__ == "__main__":
    unittest.main()
