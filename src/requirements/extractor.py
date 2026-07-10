"""Extract ProductSpec from scraped product dict."""

import re
from typing import Literal

from src.requirements.models import ProductSpec, CPUInfo, MAX_RAM_GB, MIN_STORAGE_GB, PREFERRED_RAM_VALUES
from src.requirements.cpu_db import CPUDatabase
from src.requirements.heuristics import heuristic_cpu_info


def _findall_gb_tb(text: str) -> list[tuple[int, str, str]]:
    """Return all (gb, unit, storage_type) matches in text."""
    if not text:
        return []
    results = []
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*(TB|GB)\s*(SSD|HDD|NVMe|eMMC|M\.2)?", text, re.I):
        val = float(m.group(1))
        unit = m.group(2).upper()
        raw_type = m.group(3)
        stype = raw_type.upper() if raw_type else "UNKNOWN"
        if stype not in ("SSD", "HDD", "NVMe", "EMMC"):
            stype = "UNKNOWN"
        # Skip MB values (under 1GB) and CPU cache values like "30MB"
        if unit == "GB" and val < 1:
            continue
        gb = int(val) if unit == "GB" else int(val * 1024) if unit == "TB" else int(val)
        results.append((gb, unit, stype))
    return results


def _find_ram(desc: str) -> int:
    """Extract RAM GB from description, smarter than plain parse_gb.

    Strategy: look for RAM-specific hints first, then fallback to any GB
    value in the 4-128 range (excluding TB and values clearly being storage).
    Handles decimal values like "32.0GB".
    """
    if not desc:
        return 0
    # 1. Look for explicit RAM patterns (handle decimal values)
    patterns = [
        r"RAM\s*(\d+(?:\.\d+)?)\s*GB",
        r"(\d+(?:\.\d+)?)\s*GB\s*RAM",
        r"(\d+(?:\.\d+)?)\s*GB\s*DDR[345]",
        r"(\d+(?:\.\d+)?)\s*GB\s*LPDDR[345]",
        r"Memoria\s*(\d+(?:\.\d+)?)\s*GB",
        r"(\d+(?:\.\d+)?)\s*[gG][bB]\s*(?:de\s*)?RAM",
    ]
    for pat in patterns:
        m = re.search(pat, desc, re.I)
        if m:
            val = float(m.group(1))
            if 1 <= val <= MAX_RAM_GB:
                return int(val)

    # 2. Fallback: find ALL GB values, prefer values in typical RAM range
    matches = re.findall(r"(\d+(?:\.\d+)?)\s*GB", desc, re.I)
    vals = [int(float(x)) for x in matches]
    ram_vals = [v for v in vals if 4 <= v <= MAX_RAM_GB]
    if ram_vals:
        for preferred in PREFERRED_RAM_VALUES:
            if preferred in ram_vals:
                return preferred
        return max(ram_vals)

    return 0


def _find_storage(desc: str) -> tuple[int, Literal["SSD", "HDD", "UNKNOWN"]]:
    """Extract storage GB and type from description.

    Strategy: find ALL matches, prefer those with explicit SSD/HDD/eMMC type,
    then larger values >= 40GB (to exclude RAM values like 8/16/32GB).
    """
    candidates = _findall_gb_tb(desc)

    # 1. Prefer matches with explicit storage type
    typed = [c for c in candidates if c[2] != "UNKNOWN"]
    if typed:
        return max(typed, key=lambda c: c[0])[0], typed[-1][2]

    # 2. No explicit type: prefer larger values (>=40GB = storage, not RAM)
    large = [c for c in candidates if c[0] >= MIN_STORAGE_GB]
    if large:
        best = max(large, key=lambda c: c[0])
        return best[0], "UNKNOWN"

    # 3. Last resort: return largest of all
    if candidates:
        best = max(candidates, key=lambda c: c[0])
        return best[0], "UNKNOWN"

    return 0, "UNKNOWN"


def _parse_os(text: str) -> str:
    """Extract OS from description.

    Handles: Win 11, W11, Windows 11, Win 10, W10, Windows 10,
    "W 11" (Dell), "WINOWS 11" / "WINDOWSL 11" (typos), ChromeOS.
    """
    if not text:
        return "Unknown"
    t = re.sub(r"\s+", " ", text)

    # Detect ChromeOS / Chrome OS
    if re.search(r"Chrome\s*OS|ChromeOS|Chrome\s*Book", t, re.I):
        return "ChromeOS"

    t_upper = t.upper()
    if "WIN 11" in t_upper or "W11" in t_upper or "WINDOWS 11" in t_upper:
        return "Windows 11"
    if "W IN 11" in t_upper or "W 11 " in t_upper or t_upper.startswith("W 11 "):
        return "Windows 11"
    # Handle typos: WINOWS, WINDOWSL
    if re.search(r"WINOWS\s*11|WINDOWSL\s*11", t_upper):
        return "Windows 11"

    if "WIN 10" in t_upper or "W10" in t_upper or "WINDOWS 10" in t_upper:
        return "Windows 10"
    if "W 10 " in t_upper or t_upper.startswith("W 10 "):
        return "Windows 10"
    if re.search(r"WINOWS\s*10|WINDOWSL\s*10", t_upper):
        return "Windows 10"

    return "Unknown"


def _parse_single_gb_tb(text: str) -> tuple[int, str]:
    """Parse a single value like '8 GB', '1 TB' returning (gb, unit).

    Returns (0, '') if no match.
    """
    if not text:
        return 0, ""
    m = re.search(r"(\d+(?:\.\d+)?)\s*(TB|GB)", text, re.I)
    if not m:
        return 0, ""
    val = float(m.group(1))
    unit = m.group(2).upper()
    gb = int(val * 1024) if unit == "TB" else int(val)
    return gb, unit


def _is_screen_size(text: str) -> bool:
    return bool(re.search(r"pulgad|inch|\d[\.,]\d\s*(pulg|inch)", text, re.I))


def _is_likely_ram(val: int, unit: str) -> bool:
    return unit == "GB" and val <= MAX_RAM_GB


def _is_likely_storage(val: int, unit: str, stype: str) -> bool:
    if stype != "UNKNOWN":
        return True
    gb = val * 1024 if unit == "TB" else val
    return gb >= MIN_STORAGE_GB or unit == "TB"


def _extract_cpu(product: dict, cpu_db: CPUDatabase) -> tuple[str, CPUInfo]:
    proc_raw = (product.get("procesador") or "").strip()
    cpu_info = cpu_db.lookup(proc_raw) if proc_raw else None
    if cpu_info is None and proc_raw:
        cpu_info = heuristic_cpu_info(proc_raw)
    if cpu_info is None:
        cpu_info = CPUInfo(
            model=proc_raw, matched_model=None,
            base_ghz=None, turbo_ghz=None,
            cores=None, threads=None, source="none",
        )
    return proc_raw, cpu_info


def _extract_ram(product: dict, desc: str, ice_ve: str, ice_v: str) -> int:
    parser_ram = product.get("ram", "")
    if parser_ram:
        gb, unit = _parse_single_gb_tb(parser_ram)
        if _is_likely_ram(gb, unit):
            return gb
    if ice_ve and _is_likely_ram(*_parse_single_gb_tb(ice_ve)):
        return _parse_single_gb_tb(ice_ve)[0]
    if ice_v and _is_likely_ram(*_parse_single_gb_tb(ice_v)):
        return _parse_single_gb_tb(ice_v)[0]
    return _find_ram(desc)


def _extract_storage(product: dict, desc: str, ice_v: str) -> tuple[int, str]:
    if product.get("disco_detalle"):
        return _find_storage(product["disco_detalle"])
    if product.get("disco"):
        return _find_storage(product["disco"])
    if ice_v and not _is_screen_size(ice_v):
        candidates = _findall_gb_tb(ice_v)
        storage_candidates = [c for c in candidates if _is_likely_storage(*c)]
        if storage_candidates:
            best = max(storage_candidates, key=lambda c: c[0])
            return best[0], best[2]
    return _find_storage(desc)


def _extract_os(product: dict, desc: str) -> str:
    os_val = product.get("sistema_operativo", "")
    if os_val and os_val != "Unknown":
        return os_val
    return _parse_os(desc)


def extract_specs(product: dict, cpu_db: CPUDatabase) -> ProductSpec:
    proc_raw, cpu_info = _extract_cpu(product, cpu_db)
    desc = product.get("descripcion", "")
    ice_ve = product.get("ice_valorEditar", "")
    ice_v = product.get("ice_valor", "")

    storage_gb, storage_type = _extract_storage(product, desc, ice_v)

    return ProductSpec(
        marca=product.get("marca", ""),
        clave=product.get("clave", ""),
        procesador=proc_raw,
        cpu=cpu_info,
        ram_gb=_extract_ram(product, desc, ice_ve, ice_v),
        storage_gb=storage_gb,
        storage_type=storage_type,
        os=_extract_os(product, desc),
    )