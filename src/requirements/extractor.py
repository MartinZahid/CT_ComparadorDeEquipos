"""Extract ProductSpec from scraped product dict."""

import re
from typing import Literal

from src.requirements.models import ProductSpec, CPUInfo
from src.requirements.cpu_db import CPUDatabase
from src.requirements.heuristics import heuristic_cpu_info


def parse_gb(text: str) -> int:
    """Extract GB from strings like '16 GB', '8GB DDR5', '32 GB'."""
    if not text:
        return 0
    m = re.search(r"(\d+)\s*GB", text, re.I)
    return int(m.group(1)) if m else 0


def parse_storage(text: str) -> tuple[int, Literal["SSD", "HDD", "UNKNOWN"]]:
    """Extract storage GB and type from strings like '512 GB SSD', '1 TB HDD'."""
    if not text:
        return 0, "UNKNOWN"
    # Skip if it's screen size
    if re.search(r"pulgad|inch", text, re.I):
        return 0, "UNKNOWN"
    m = re.search(r"(\d+(?:\.\d+)?)\s*(TB|GB)\s*(SSD|HDD)?", text, re.I)
    if not m:
        return 0, "UNKNOWN"
    val = float(m.group(1))
    unit = m.group(2).upper()
    stype = m.group(3).upper() if m.group(3) else "UNKNOWN"
    gb = int(val * 1024) if unit == "TB" else int(val)
    if stype not in ("SSD", "HDD"):
        stype = "UNKNOWN"
    return gb, stype


def parse_os(text: str) -> str:
    """Extract OS from description: Win 11, W11, Windows 11, Win 10, W10, Windows 10."""
    if not text:
        return "Unknown"
    t = text.upper()
    if "WIN 11" in t or "W11" in t or "WINDOWS 11" in t:
        return "Windows 11"
    if "WIN 10" in t or "W10" in t or "WINDOWS 10" in t:
        return "Windows 10"
    return "Unknown"


def extract_specs(product: dict, cpu_db: CPUDatabase) -> ProductSpec:
    """Convert scraped product dict to ProductSpec with CPU lookup."""
    # CPU
    proc_raw = (product.get("procesador") or "").strip()
    cpu_info = cpu_db.lookup(proc_raw) if proc_raw else None
    if cpu_info is None and proc_raw:
        cpu_info = heuristic_cpu_info(proc_raw)
    if cpu_info is None:
        cpu_info = CPUInfo(
            model=proc_raw,
            matched_model=None,
            base_ghz=None,
            turbo_ghz=None,
            cores=None,
            threads=None,
            source="none",
        )

    # RAM: try ice_valorEditar, fallback to descripcion
    ram_src = product.get("ice_valorEditar", "") or product.get("descripcion", "")
    ram_gb = parse_gb(ram_src)

    # Storage: try ice_valor, but skip screen size; fallback to descripcion
    storage_src = product.get("ice_valor", "")
    if re.search(r"pulgad|inch", storage_src, re.I):
        storage_src = ""
    if not storage_src:
        storage_src = product.get("descripcion", "")
    storage_gb, storage_type = parse_storage(storage_src)

    # OS
    os = parse_os(product.get("descripcion", ""))

    return ProductSpec(
        marca=product.get("marca", ""),
        clave=product.get("clave", ""),
        procesador=proc_raw,
        cpu=cpu_info,
        ram_gb=ram_gb,
        storage_gb=storage_gb,
        storage_type=storage_type,
        os=os,
    )