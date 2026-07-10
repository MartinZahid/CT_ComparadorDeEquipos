"""Heuristic CPU spec estimation for models not in database."""

import re

from src.requirements.models import CPUInfo


def heuristic_cpu_info(model: str) -> CPUInfo:
    """
    Estimate CPU specs based on model name.
    Option C: Parse tier from name.
    """
    if not model:
        return CPUInfo(
            model="",
            matched_model=None,
            base_ghz=None,
            turbo_ghz=None,
            cores=None,
            threads=None,
            source="none",
        )

    m = model.upper()

    # Tier: Ultra 9/7, Ryzen AI 9/7, Ryzen 9 HX/H -> recommended tier
    if any(x in m for x in [
        "ULTRA 9", "ULTRA 7",
        "RYZEN AI 9", "RYZEN AI 7",
        "RYZEN 9 HX", "RYZEN 9 H "
    ]):
        return CPUInfo(
            model=model,
            matched_model=None,
            base_ghz=3.6,
            turbo_ghz=5.0,
            cores=8,
            threads=16,
            source="heuristic",
        )

    # Tier: Ultra 5, Core 5/7, Ryzen AI 5/7, Ryzen 7 (non-HX) -> minimum tier
    if any(x in m for x in [
        "ULTRA 5",
        "CORE 5", "CORE 7",
        "RYZEN AI 5", "RYZEN AI 7",
        "RYZEN 7"
    ]):
        # HX/H suffix = mobile high perf
        if "HX" in m or re.search(r"\bH\b", m):
            return CPUInfo(
                model=model,
                matched_model=None,
                base_ghz=3.6,
                turbo_ghz=4.8,
                cores=6,
                threads=12,
                source="heuristic",
            )
        return CPUInfo(
            model=model,
            matched_model=None,
            base_ghz=2.5,
            turbo_ghz=4.3,
            cores=4,
            threads=8,
            source="heuristic",
        )

    # Core 3 / Core i3 / Ryzen 3 / Celeron / Pentium / N-series -> likely insufficient
    if any(x in m for x in [
        "CORE I3", "CORE 3", "RYZEN 3",
        "CELERON", "PENTIUM",
        "N100", "N200", "N300", "N305", "N95", "N97"
    ]):
        return CPUInfo(
            model=model,
            matched_model=None,
            base_ghz=1.0,
            turbo_ghz=3.0,
            cores=4,
            threads=4,
            source="heuristic",
        )

    # Core i5/i7 without generation info -> assume minimum
    if any(x in m for x in ["CORE I5", "CORE I7", "RYZEN 5", "RYZEN 7"]):
        return CPUInfo(
            model=model,
            matched_model=None,
            base_ghz=2.5,
            turbo_ghz=4.0,
            cores=4,
            threads=8,
            source="heuristic",
        )

    return CPUInfo(
        model=model,
        matched_model=None,
        base_ghz=None,
        turbo_ghz=None,
        cores=None,
        threads=None,
        source="none",
    )