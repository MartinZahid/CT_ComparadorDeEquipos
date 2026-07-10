"""Classification logic: compares ProductSpec against requirements."""

from src.requirements.models import ProductSpec, RequirementSet, Classification


def check_cpu(spec: ProductSpec, req: RequirementSet) -> tuple[bool, bool, str]:
    """Returns (meets_min, meets_rec, reason)"""
    if spec.cpu.turbo_ghz is None or spec.cpu.cores is None:
        return False, False, "CPU sin datos técnicos (no está en BD ni heurística)"

    turbo = spec.cpu.turbo_ghz
    cores = spec.cpu.cores

    meets_min = turbo >= req.cpu.min_ghz and cores >= req.cpu.min_cores
    meets_rec = turbo >= req.cpu.rec_ghz and cores >= req.cpu.rec_cores

    if meets_rec:
        reason = f"CPU turbo {turbo}GHz >= {req.cpu.rec_ghz}GHz, {cores} nucleos >= {req.cpu.rec_cores}"
    elif meets_min:
        reason = f"CPU turbo {turbo}GHz >= {req.cpu.min_ghz}GHz, {cores} nucleos >= {req.cpu.min_cores}"
    else:
        reason = f"CPU turbo {turbo}GHz < {req.cpu.min_ghz}GHz o {cores} nucleos < {req.cpu.min_cores}"

    return meets_min, meets_rec, reason


def check_ram(spec: ProductSpec, req: RequirementSet) -> tuple[bool, bool, str]:
    ram = spec.ram_gb
    meets_min = ram >= req.ram_min_gb
    meets_rec = ram >= req.ram_rec_gb

    if meets_rec:
        reason = f"RAM {ram}GB ≥ {req.ram_rec_gb}GB (recomendado)"
    elif meets_min:
        reason = f"RAM {ram}GB ≥ {req.ram_min_gb}GB (mínimo)"
    else:
        reason = f"RAM {ram}GB < {req.ram_min_gb}GB (mínimo)"

    return meets_min, meets_rec, reason


def check_os(spec: ProductSpec, req: RequirementSet) -> tuple[bool, bool, str]:
    os = spec.os
    meets_min = os.startswith(req.os_min) or os.startswith(req.os_rec)
    meets_rec = os.startswith(req.os_rec)

    if meets_rec:
        reason = f"OS {req.os_rec} (recomendado)"
    elif meets_min:
        reason = f"OS {req.os_min} (mínimo)"
    else:
        reason = f"OS {os} no cumple (requiere {req.os_min}/{req.os_rec})"

    return meets_min, meets_rec, reason


def check_disk(spec: ProductSpec, req: RequirementSet) -> tuple[bool, bool, str]:
    storage_gb = spec.storage_gb
    storage_type = spec.storage_type

    # SSD check for small drives
    ssd_ok = True
    if storage_gb <= req.ssd_required_below_gb and storage_type != "SSD":
        ssd_ok = False

    meets_min = storage_gb >= req.disk_min_gb and ssd_ok
    meets_rec = storage_gb >= req.disk_rec_gb and ssd_ok

    if not ssd_ok:
        reason = f"Disco {storage_gb}GB {storage_type} - requiere SSD para ≤{req.ssd_required_below_gb}GB"
    elif meets_rec:
        reason = f"Disco {storage_gb}GB {storage_type} OK"
    elif meets_min:
        reason = f"Disco {storage_gb}GB {storage_type} cumple mínimo"
    else:
        reason = f"Disco {storage_gb}GB < {req.disk_min_gb}GB"

    return meets_min, meets_rec, reason


def classify(spec: ProductSpec, req: RequirementSet) -> Classification:
    """Classify product into one of 4 levels + bool puede_correr."""
    reasons = []

    # CPU
    cpu_min, cpu_rec, cpu_reason = check_cpu(spec, req)
    reasons.append(cpu_reason)

    # RAM
    ram_min, ram_rec, ram_reason = check_ram(spec, req)
    reasons.append(ram_reason)

    # OS
    os_min, os_rec, os_reason = check_os(spec, req)
    reasons.append(os_reason)

    # Disk
    disk_min, disk_rec, disk_reason = check_disk(spec, req)
    reasons.append(disk_reason)

    # No CPU data at all
    if spec.cpu.source == "none" or spec.cpu.turbo_ghz is None:
        return Classification(
            nivel="sin_datos_cpu",
            puede_correr=False,
            reasons=reasons,
            score=0,
        )

    all_rec = cpu_rec and ram_rec and os_rec and disk_rec
    all_min = cpu_min and ram_min and os_min and disk_min
    cpu_ram_min = cpu_min and ram_min

    if all_rec:
        return Classification("recommended", True, reasons, 100)
    if all_min:
        return Classification("minimos", True, reasons, 70)
    if cpu_ram_min:
        return Classification("capaz", True, reasons, 50)
    return Classification("no_corre", False, reasons, 10)