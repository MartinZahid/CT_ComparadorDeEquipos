"""CPU Database: downloads Intel/AMD CSVs, normalizes, fuzzy matches, caches."""

import csv
import pickle
import re
from pathlib import Path
from typing import Optional

import requests
from rapidfuzz import process, fuzz

from src.requirements.models import CPUInfo


INTEL_CSV_URL = "https://raw.githubusercontent.com/felixsteinke/cpu-spec-dataset/main/dataset/intel-cpus.csv"
AMD_CSV_URL = "https://raw.githubusercontent.com/felixsteinke/cpu-spec-dataset/main/dataset/amd-cpus.csv"

CACHE_DIR = Path("data/cpu_db")
RAW_DIR = CACHE_DIR / "raw"
NORMALIZED_CACHE = CACHE_DIR / "normalized.pkl"


def normalize_model(model: str) -> str:
    """Normalize CPU model for matching: lowercase, remove spaces, hyphens, prefixes."""
    if not model:
        return ""
    m = model.lower().strip()
    # Remove common prefixes
    for prefix in ("core ", "intel ", "amd ", "ryzen ", "processor "):
        if m.startswith(prefix):
            m = m[len(prefix):]
    # Remove spaces, hyphens, underscores, dots, parentheses
    m = re.sub(r"[\s\-_\.\(\)]+", "", m)
    return m


def parse_ghz(text: str) -> Optional[float]:
    """Extract GHz value from strings like '3.70 GHz' or '2.4GHz'."""
    if not text:
        return None
    m = re.search(r"([\d.]+)\s*GHz", text, re.I)
    return float(m.group(1)) if m else None


def parse_int(text: str) -> Optional[int]:
    """Extract integer from string."""
    if not text:
        return None
    m = re.search(r"(\d+)", text)
    return int(m.group(1)) if m else None


class CPUDatabase:
    def __init__(self, cache_dir: Path = CACHE_DIR):
        self.cache_dir = cache_dir
        self.raw_dir = RAW_DIR
        self.normalized_cache = NORMALIZED_CACHE
        self._cpus: dict[str, CPUInfo] = {}  # normalized_model -> CPUInfo
        self._choices: list[str] = []  # list of normalized models for fuzzy matching

    def load(self) -> None:
        """Load database: use cache if exists, otherwise download and build."""
        if self.normalized_cache.exists():
            with open(self.normalized_cache, "rb") as f:
                data = pickle.load(f)
                self._cpus = data["cpus"]
                self._choices = data["choices"]
            return

        self._build()
        self._save_cache()

    def _build(self) -> None:
        """Download CSVs, parse, normalize, build lookup dict."""
        self.raw_dir.mkdir(parents=True, exist_ok=True)

        # Download if needed
        intel_path = self.raw_dir / "intel-cpus.csv"
        amd_path = self.raw_dir / "amd-cpus.csv"

        if not intel_path.exists():
            self._download(INTEL_CSV_URL, intel_path)
        if not amd_path.exists():
            self._download(AMD_CSV_URL, amd_path)

        # Parse Intel
        with open(intel_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                model = row.get("ProcessorNumber", "").strip()
                if not model:
                    continue
                norm = normalize_model(model)
                if not norm:
                    continue
                cpu = CPUInfo(
                    model=model,
                    matched_model=model,
                    base_ghz=parse_ghz(row.get("ClockSpeed", "")),
                    turbo_ghz=parse_ghz(row.get("ClockSpeedMax", "")),
                    cores=parse_int(row.get("CoreCount", "")),
                    threads=parse_int(row.get("ThreadCount", "")),
                    source="intel_ark",
                )
                if norm not in self._cpus:  # keep first match
                    self._cpus[norm] = cpu

        # Parse AMD
        with open(amd_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                model = row.get("Model", "").strip()
                if not model:
                    continue
                norm = normalize_model(model)
                if not norm:
                    continue
                cpu = CPUInfo(
                    model=model,
                    matched_model=model,
                    base_ghz=parse_ghz(row.get("Base Clock", "")),
                    turbo_ghz=parse_ghz(row.get("Max. Boost Clock ¹ ²", "")),
                    cores=parse_int(row.get("# of CPU Cores", "")),
                    threads=parse_int(row.get("# of Threads", "")),
                    source="amd_specs",
                )
                if norm not in self._cpus:
                    self._cpus[norm] = cpu

        self._choices = list(self._cpus.keys())

    def _download(self, url: str, dest: Path) -> None:
        """Download CSV with progress."""
        print(f"  Descargando {url}...")
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        dest.write_bytes(resp.content)

    def _save_cache(self) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        with open(self.normalized_cache, "wb") as f:
            pickle.dump({"cpus": self._cpus, "choices": self._choices}, f)

    def lookup(self, model: str, threshold: int = 85) -> Optional[CPUInfo]:
        """
        Fuzzy match CPU model.
        Returns CPUInfo with matched_model set, or None if no match.
        """
        if not model:
            return None

        norm = normalize_model(model)

        # Exact match
        if norm in self._cpus:
            cpu = self._cpus[norm]
            return CPUInfo(
                model=model,
                matched_model=cpu.model,
                base_ghz=cpu.base_ghz,
                turbo_ghz=cpu.turbo_ghz,
                cores=cpu.cores,
                threads=cpu.threads,
                source=cpu.source,
            )

        # Fuzzy match
        if self._choices:
            result = process.extractOne(
                norm, self._choices, scorer=fuzz.ratio, score_cutoff=threshold
            )
            if result:
                matched_norm, score, _ = result
                cpu = self._cpus[matched_norm]
                return CPUInfo(
                    model=model,
                    matched_model=cpu.model,
                    base_ghz=cpu.base_ghz,
                    turbo_ghz=cpu.turbo_ghz,
                    cores=cpu.cores,
                    threads=cpu.threads,
                    source=cpu.source,
                )

        return None