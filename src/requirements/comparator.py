"""Orchestrator: loads scraped JSON, processes each product, writes comparison JSON."""

import json
from datetime import datetime
from pathlib import Path
from collections import Counter

from src.requirements.models import RequirementSet, ComparisonResult
from src.requirements.cpu_db import CPUDatabase
from src.requirements.extractor import extract_specs
from src.requirements.classifier import classify


DEFAULT_REQUIREMENTS = RequirementSet()


def compare_category(
    input_json: Path,
    output_json: Path,
    requirements: RequirementSet = DEFAULT_REQUIREMENTS,
    cpu_db: CPUDatabase | None = None,
) -> ComparisonResult:
    """Process one category JSON and write comparison result."""
    if cpu_db is None:
        cpu_db = CPUDatabase()
        cpu_db.load()

    with open(input_json, encoding="utf-8") as f:
        products = json.load(f)

    results = []
    counts = Counter()

    for p in products:
        spec = extract_specs(p, cpu_db)
        cls = classify(spec, requirements)
        counts[cls.nivel] += 1

        # Build description
        desc = (
            f"{spec.marca} {spec.clave}, {spec.procesador}, "
            f"{spec.ram_gb}GB RAM, {spec.storage_gb}GB {spec.storage_type}, {spec.os}"
        )

        results.append({
            "clave": spec.clave,
            "marca": spec.marca,
            "procesador": spec.procesador,
            "ram_gb": spec.ram_gb,
            "storage_gb": spec.storage_gb,
            "storage_type": spec.storage_type,
            "os": spec.os,
            "cpu_source": spec.cpu.source,
            "cpu_matched": spec.cpu.matched_model,
            "cpu_base_ghz": spec.cpu.base_ghz,
            "cpu_turbo_ghz": spec.cpu.turbo_ghz,
            "cpu_cores": spec.cpu.cores,
            "cpu_threads": spec.cpu.threads,
            "nivel": cls.nivel,
            "puede_correr": cls.puede_correr,
            "razones": cls.reasons,
            "score": cls.score,
            "descripcion": desc,
            "url": p.get("url", ""),
            "imagen": p.get("imagen", ""),
        })

    output = ComparisonResult(
        requisitos_usados=requirements,
        resultados=results,
        resumen=dict(counts),
    )

    # Write JSON
    output_json.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now().isoformat()
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump({
            "fecha_generacion": now,
            "requisitos_usados": output.requisitos_usados.to_dict(),
            "resultados": output.resultados,
            "resumen": output.resumen,
        }, f, ensure_ascii=False, indent=2)

    return output