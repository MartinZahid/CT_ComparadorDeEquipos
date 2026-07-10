"""Requirements comparison package."""

from src.requirements.models import (
    RequirementSet,
    CPURequirement,
    ProductSpec,
    CPUInfo,
    Classification,
    ComparisonResult,
)
from src.requirements.cpu_db import CPUDatabase
from src.requirements.extractor import extract_specs
from src.requirements.classifier import classify
from src.requirements.comparator import compare_category

__all__ = [
    "RequirementSet",
    "CPURequirement",
    "ProductSpec",
    "CPUInfo",
    "Classification",
    "ComparisonResult",
    "CPUDatabase",
    "extract_specs",
    "classify",
    "compare_category",
]