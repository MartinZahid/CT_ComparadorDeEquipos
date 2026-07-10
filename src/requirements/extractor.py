"""Extract ProductSpec from scraped product dict."""

from src.requirements.models import ProductSpec, CPUInfo
from src.requirements.cpu_db import CPUDatabase
from src.requirements.heuristics import heuristic_cpu_info
from src.spec_parsing import (
    findall_gb_tb, find_ram, find_storage, parse_os,
    parse_single_gb_tb, is_screen_size, is_likely_ram, is_likely_storage,
)


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
        gb, unit = parse_single_gb_tb(parser_ram)
        if is_likely_ram(gb, unit):
            return gb
    if ice_ve and is_likely_ram(*parse_single_gb_tb(ice_ve)):
        return parse_single_gb_tb(ice_ve)[0]
    if ice_v and is_likely_ram(*parse_single_gb_tb(ice_v)):
        return parse_single_gb_tb(ice_v)[0]
    return find_ram(desc)


def _extract_storage(product: dict, desc: str, ice_v: str) -> tuple[int, str]:
    if product.get("disco_detalle"):
        return find_storage(product["disco_detalle"])
    if product.get("disco"):
        return find_storage(product["disco"])
    if ice_v and not is_screen_size(ice_v):
        candidates = findall_gb_tb(ice_v)
        storage_candidates = [c for c in candidates if is_likely_storage(*c)]
        if storage_candidates:
            best = max(storage_candidates, key=lambda c: c[0])
            return best[0], best[2]
    return find_storage(desc)


def _extract_os(product: dict, desc: str) -> str:
    os_val = product.get("sistema_operativo", "")
    if os_val:
        return parse_os(os_val)
    return parse_os(desc)


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