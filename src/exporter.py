"""Export product data to JSON and CSV."""

import json
from pathlib import Path

import pandas as pd


PRIORITY_COLS = [
    "marca", "clave", "num_parte", "descripcion",
    "modelo", "categoria", "precio", "moneda",
    "existencia", "procesador", "url", "imagen",
]


def save(products: list[dict], slug: str, output_dir: Path) -> tuple[Path, Path]:
    """Save products as JSON and CSV. Returns (json_path, csv_path)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    base = output_dir / f"ctonline-{slug}"

    json_path = base.with_suffix(".json")
    json_path.write_text(
        json.dumps(products, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    csv_path = base.with_suffix(".csv")
    df = pd.DataFrame(products)
    cols = PRIORITY_COLS + [c for c in df.columns if c not in PRIORITY_COLS]
    df = df[cols]
    df.to_csv(csv_path, index=False, encoding="utf-8")

    return json_path, csv_path
