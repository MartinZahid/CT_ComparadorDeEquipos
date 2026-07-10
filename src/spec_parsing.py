"""Unified text-parsing functions for RAM, storage, and OS extraction.

Single source of truth used by both parser.py (at scrape time) and
extractor.py (at compare time).
"""

import re

from src.constants import MAX_RAM_GB, MIN_STORAGE_GB, PREFERRED_RAM_VALUES


def findall_gb_tb(text: str) -> list[tuple[int, str, str]]:
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
        if unit == "GB" and val < 1:
            continue
        gb = int(val) if unit == "GB" else int(val * 1024)
        results.append((gb, unit, stype))
    return results


def find_ram(text: str) -> int:
    """Extract RAM GB from description text.

    Uses RAM-specific patterns first, then falls back to GB values
    in typical RAM range (4-128 GB), preferring common values.
    """
    if not text:
        return 0
    patterns = [
        r"RAM\s*(\d+(?:\.\d+)?)\s*GB",
        r"(\d+(?:\.\d+)?)\s*GB\s*RAM",
        r"(\d+(?:\.\d+)?)\s*GB\s*DDR[345]",
        r"(\d+(?:\.\d+)?)\s*GB\s*LPDDR[345]",
        r"Memoria\s*(\d+(?:\.\d+)?)\s*GB",
        r"(\d+(?:\.\d+)?)\s*[gG][bB]\s*(?:de\s*)?RAM",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.I)
        if m:
            val = float(m.group(1))
            if 1 <= val <= MAX_RAM_GB:
                return int(val)
    matches = re.findall(r"(\d+(?:\.\d+)?)\s*GB", text, re.I)
    vals = [int(float(x)) for x in matches]
    ram_vals = [v for v in vals if 4 <= v <= MAX_RAM_GB]
    if ram_vals:
        for preferred in PREFERRED_RAM_VALUES:
            if preferred in ram_vals:
                return preferred
        return max(ram_vals)
    return 0


def find_storage(text: str) -> tuple[int, str]:
    """Extract storage size (GB) and type from text.

    Returns (storage_gb, storage_type) where type is SSD, HDD, or UNKNOWN.
    """
    candidates = findall_gb_tb(text)
    typed = [c for c in candidates if c[2] != "UNKNOWN"]
    if typed:
        return max(typed, key=lambda c: c[0])[0], typed[-1][2]
    large = [c for c in candidates if c[0] >= MIN_STORAGE_GB]
    if large:
        best = max(large, key=lambda c: c[0])
        return best[0], "UNKNOWN"
    if candidates:
        best = max(candidates, key=lambda c: c[0])
        return best[0], "UNKNOWN"
    return 0, "UNKNOWN"


def parse_os(text: str) -> str:
    """Extract OS name from text.

    Handles: Win 11, W11, Windows 11, Win 10, W10, Windows 10,
    'W 11' (Dell), 'WINOWS 11' / 'WINDOWSL 11' (typos), ChromeOS.
    """
    if not text:
        return "Unknown"
    t = re.sub(r"\s+", " ", text)
    if re.search(r"Chrome\s*OS|ChromeOS|Chrome\s*Book", t, re.I):
        return "ChromeOS"
    t_upper = t.upper()
    if "WIN 11" in t_upper or "W11" in t_upper or "WINDOWS 11" in t_upper:
        return "Windows 11"
    if "W IN 11" in t_upper or "W 11 " in t_upper or t_upper.startswith("W 11 "):
        return "Windows 11"
    if re.search(r"WINOWS\s*11|WINDOWSL\s*11", t_upper):
        return "Windows 11"
    if "WIN 10" in t_upper or "W10" in t_upper or "WINDOWS 10" in t_upper:
        return "Windows 10"
    if "W 10 " in t_upper or t_upper.startswith("W 10 "):
        return "Windows 10"
    if re.search(r"WINOWS\s*10|WINDOWSL\s*10", t_upper):
        return "Windows 10"
    return "Unknown"


def parse_single_gb_tb(text: str) -> tuple[int, str]:
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


def is_screen_size(text: str) -> bool:
    return bool(re.search(r"pulgad|inch|\d[\.,]\d\s*(pulg|inch)", text, re.I))


def is_likely_ram(val: int, unit: str) -> bool:
    return unit == "GB" and val <= MAX_RAM_GB


def is_likely_storage(val: int, unit: str, stype: str) -> bool:
    if stype != "UNKNOWN":
        return True
    gb = val * 1024 if unit == "TB" else val
    return gb >= MIN_STORAGE_GB or unit == "TB"
