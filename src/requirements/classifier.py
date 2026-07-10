"""Classification logic: compares ProductSpec against requirements."""

from src.requirements.models import ProductSpec, RequirementSet, Classification


# Requirement thresholds (from user's specs)
CPU_MIN_GHZ = 3.6
CPU_MIN_CORES = 4
CPU_REC_GHZ = 3.6
CPU_REC_CORES = 4
RAM_MIN_GB = 8
RAM_REC_GB = 16
DISK_MIN_GB = 1
DISK_REC_GB = 1
SSD_REQUIRED_BELOW_GB = 128
OS_MIN = "Windows 10"
OS_REC = "Windows 11"


def check_cpu(spec: ProductSpec) -> tuple[bool, bool, str]:
    """Returns (meets_min, meets_rec, reason)"""
    if spec.cpu.turbo_ghz is None or spec.cpu.cores is None:
        return False, False, "CPU sin datos técnicos (no está en BD ni heurística)"

    turbo = spec.cpu.turbo_ghz
    cores = spec.cpu.cores

    meets_min = turbo >= CPU_MIN_GHZ and cores >= CPU_MIN_CORES
    meets_rec = turbo >= CPU_REC_GHZ and cores >= CPU_REC_CORES

    if meets_rec:
        reason = f"CPU turbo {turbo}GHz >= {CPU_REC_GHZ}GHz, {cores} nucleos >= {CPU_REC_CORES}"
    elif meets_min:
        reason = f"CPU turbo {turbo}GHz >= {CPU_MIN_GHZ}GHz, {cores} nucleos >= {CPU_MIN_CORES}"
    else:
        reason = f"CPU turbo {turbo}GHz < {CPU_MIN_GHZ}GHz o {cores} nucleos < {CPU_MIN_CORES}"

    return meets_min, meets_rec, reason


def check_ram(spec: ProductSpec) -> tuple[bool, bool, str]:
    ram = spec.ram_gb
    meets_min = ram >= RAM_MIN_GB
    meets_rec = ram >= RAM_REC_GB

    if meets_rec:
        reason = f"RAM {ram}GB ≥ {RAM_REC_GB}GB (recomendado)"
    elif meets_min:
        reason = f"RAM {ram}GB ≥ {RAM_MIN_GB}GB (mínimo)"
    else:
        reason = f"RAM {ram}GB < {RAM_MIN_GB}GB (mínimo)"

    return meets_min, meets_rec, reason


def check_os(spec: ProductSpec) -> tuple[bool, bool, str]:
    os = spec.os
    meets_min = os.startswith("Windows 10") or os.startswith("Windows 11")
    meets_rec = os.startswith("Windows 11")

    if meets_rec:
        reason = "OS Windows 11 (recomendado)"
    elif meets_min:
        reason = "OS Windows 10 (mínimo)"
    else:
        reason = f"OS {os} no cumple (requiere Windows 10/11)"

    return meets_min, meets_rec, reason


def check_disk(spec: ProductSpec) -> tuple[bool, bool, str]:
    storage_gb = spec.storage_gb
    storage_type = spec.storage_type

    # SSD check for small drives
    ssd_ok = True
    if storage_gb <= SSD_REQUIRED_BELOW_GB and storage_type != "SSD":
        ssd_ok = False

    meets_min = storage_gb >= DISK_MIN_GB and ssd_ok
    meets_rec = storage_gb >= DISK_REC_GB and ssd_ok

    if not ssd_ok:
        reason = f"Disco {storage_gb}GB {storage_type} - requiere SSD para ≤{SSD_REQUIRED_BELOW_GB}GB"
    elif meets_rec:
        reason = f"Disco {storage_gb}GB {storage_type} OK"
    elif meets_min:
        reason = f"Disco {storage_gb}GB {storage_type} cumple mínimo"
    else:
        reason = f"Disco {storage_gb}GB < {DISK_MIN_GB}GB"

    return meets_min, meets_rec, reason


def classify(spec: ProductSpec, req: RequirementSet) -> Classification:
    """Classify product into one of 4 levels + bool puede_correr."""
    reasons = []

    # CPU
    cpu_min, cpu_rec, cpu_reason = check_cpu(spec)
    reasons.append(cpu_reason)

    # RAM
    ram_min, ram_rec, ram_reason = check_ram(spec)
    reasons.append(ram_reason)

    # OS
    os_min, os_rec, os_reason = check_os(spec)
    reasons.append(os_reason)

    # Disk
    disk_min, disk_rec, disk_reason = check_disk(spec)
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