"""Data models for requirements comparison."""

from dataclasses import dataclass, asdict, field
from typing import Literal

LEVEL_RECOMMENDED = "recommended"
LEVEL_MINIMOS = "minimos"
LEVEL_CAPAZ = "capaz"
LEVEL_NO_CORRE = "no_corre"
LEVEL_SIN_CPU = "sin_datos_cpu"
CLASSIFICATION_LEVELS = (LEVEL_RECOMMENDED, LEVEL_MINIMOS, LEVEL_CAPAZ, LEVEL_NO_CORRE, LEVEL_SIN_CPU)
ClassificationLevel = Literal["recommended", "minimos", "capaz", "no_corre", "sin_datos_cpu"]


@dataclass
class CPURequirement:
    min_ghz: float = 3.6
    min_cores: int = 4
    rec_ghz: float = 3.6
    rec_cores: int = 4


@dataclass
class RequirementSet:
    name: str = "default"
    os_min: str = "Windows 10"
    os_rec: str = "Windows 11"
    cpu: CPURequirement = field(default_factory=CPURequirement)
    ram_min_gb: int = 8
    ram_rec_gb: int = 16
    disk_min_gb: int = 1
    disk_rec_gb: int = 1
    ssd_required_below_gb: int = 128
    dotnet_version: str = "4.6.2"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["cpu"] = asdict(self.cpu)
        return d


@dataclass
class CPUInfo:
    model: str
    matched_model: str | None
    base_ghz: float | None
    turbo_ghz: float | None
    cores: int | None
    threads: int | None
    source: Literal["intel_ark", "amd_specs", "heuristic", "none"]


@dataclass
class ProductSpec:
    marca: str
    clave: str
    procesador: str
    cpu: CPUInfo
    ram_gb: int
    storage_gb: int
    storage_type: Literal["SSD", "HDD", "UNKNOWN"]
    os: str


@dataclass
class Classification:
    nivel: ClassificationLevel
    puede_correr: bool
    reasons: list[str]
    score: int


@dataclass
class ComparisonResult:
    requisitos_usados: RequirementSet
    resultados: list[dict]
    resumen: dict[str, int]