"""Transform raw Algolia hits into flat product dictionaries."""

import re

from src.spec_parsing import findall_gb_tb, find_ram, find_storage, parse_os, parse_single_gb_tb

_PROC_PATTERN = re.compile(
    r"(Intel\s*(?:Core\s*)?(?:\w+\s*)*[\w\d-]+"
    r"|AMD\s+(?:Ryzen\s+)?[\w\d\s]*(?:AI\s+)?[\w\d-]+"
    r"|Qualcomm\s+[\w\d\s-]+"
    r"|Celeron\s+N?\d+"
    r"|MediaTek\s+[\w-]+(?:\s+[\w\d-]+)?"
    r"|Core\s*(?:\(TM\)|™|\s*TM\d*)?\s*(?:i\d+(?:[-\s]\w+)?|Ultra\s+\d+(?:\s+\w+)?|3\s+\w+|\d+\s+\w+)"
    r"|i[3-9][-\s]\w+"
    r"|Ryzen\s+(?:\d\s+[\w-]+|AI\s+[\w\d\s]+(?:PRO\s+)?[\w\d-]+)"
    r"|Ultra\s+\d+(?:\s+\w+)?"
    r"|IntelCore\w+\s+\d+\s+\w+"
    r"|Corei[3-9]\S*"
    r"|I[3-9]\s+\w+"
    r"|N\d{2,3}"
    r"|Ci[5-9]\s*\w+)",
    re.IGNORECASE,
)

_LABEL_TO_FIELD = {
    "memoria interna": "ram",
    "capacidad de disco duro": "disco_detalle",
    "sistema operativo instalado": "sistema_operativo",
    "diagonal de la pantalla": "pantalla",
    "familia de procesador": "procesador_familia",
    "modelo del procesador": "procesador_modelo",
}


def _extract_processor(text: str) -> str:
    normalized = text.replace("\u2122", " ").replace("(TM)", " ")
    normalized = re.sub(r"(\d)([a-zA-Z])\s*,\s*", r"\1\2, ", normalized)
    normalized = re.sub(r"(?i)(\b(?:Core|Intel|AMD|Ryzen)\S*\s+\w+-\s+)", lambda m: m.group(1).replace("- ", "-"), normalized)
    normalized = re.sub(r"(?i)(\b(?:Intel|Core|Ultra|Ryzen|AMD|MediaTek|Celeron|Ryzen)\b)\s*,\s*", r"\1 ", normalized)
    normalized = re.sub(r"(?i)(\b(?:Ultra)\s+\d+)\s*,\s+(\d+[a-z][a-z0-9]*)", r"\1 \2", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    matches = _PROC_PATTERN.findall(normalized)
    if not matches:
        return ""
    cleaned = [m.strip() for m in matches]
    prefer = [m for m in cleaned if re.search(r"(?:-\w+|(?<!\d)\d{2,}\w*)", m)]
    prefer = [m for m in prefer if not re.match(r"Ryzen\s+\d\s+\d{2,3}$", m, re.I)]
    if prefer:
        return max(prefer, key=len)
    if cleaned:
        return max(cleaned, key=len)
    return ""


def _fetch_title(url: str, scraper) -> str:
    try:
        r = scraper.get(url, timeout=15)
        m = re.search(r"<title>(.*?)</title>", r.text, re.DOTALL)
        return m.group(1) if m else ""
    except Exception:
        return ""


def _parse_specs_from_html(html: str) -> dict:
    """Extract ram, disco_detalle, sistema_operativo from ct-specifics + features."""
    result = {}

    # Helper to find all GB/TB values (excluding MB) — reuses findall_gb_tb
    def _find_all_storage(text):
        return [(gb, stype) for gb, unit, stype in findall_gb_tb(text)]

    # Helper to find RAM in features text — reuses find_ram
    def _find_ram_in_text(text):
        gb = find_ram(text)
        return f"{gb} GB" if gb else ""

    # 1. Parse .ct-specifics sidebar rows
    specifics = re.findall(
        r'<div\s+class="row">\s*<div\s+class="col-xs-6">(.*?)</div>\s*<div\s+class="col-xs-6">(.*?)</div>',
        html,
        re.DOTALL,
    )
    for label, value in specifics:
        label_clean = re.sub(r"<[^>]+>", "", label).strip().lower()
        value_clean = re.sub(r"<[^>]+>", "", value).strip()
        field = _LABEL_TO_FIELD.get(label_clean)
        if field and value_clean and field not in result:
            result[field] = value_clean

    # 2. Parse #ct_features panel-body for RAM and storage (often missing from sidebar)
    feat_m = re.search(
        r'<div[^>]*id="ct_features"[^>]*>.*?<div\s+class="panel-body">\s*<p>(.*?)</p>',
        html,
        re.DOTALL,
    )
    feat_text = ""
    if feat_m:
        feat_text = re.sub(r"<[^>]+>", "", feat_m.group(1)).strip()

    if feat_text:
        # RAM from features (if not in sidebar)
        if "ram" not in result:
            ram = _find_ram_in_text(feat_text)
            if ram:
                result["ram"] = ram

        # Storage from features (if not in sidebar)
        if "disco_detalle" not in result:
            candidates = _find_all_storage(feat_text)
            if candidates:
                # Prefer typed (SSD/HDD) matches
                typed = [(g, t) for g, t in candidates if t in ("SSD", "HDD")]
                if typed:
                    best = max(typed, key=lambda x: x[0])
                else:
                    best = max(candidates, key=lambda x: x[0])
                label = f"{best[0]} GB"
                if best[1] in ("SSD", "HDD"):
                    label += f" {best[1]}"
                result["disco_detalle"] = label

        # Processor from features (if not in sidebar)
        if "procesador_familia" not in result and "procesador_modelo" not in result:
            m = re.search(r"Procesador[:\s]+([^,;]+)", feat_text, re.I)
            if m:
                result["procesador_familia"] = m.group(1).strip()

    return result


def _fetch_specs_from_page(url: str, scraper) -> dict:
    """Fetch individual product page and extract specs from HTML."""
    try:
        r = scraper.get(url, timeout=15)
        return _parse_specs_from_html(r.text)
    except Exception:
        return {}


def _extract_ram_from_desc(desc: str) -> str:
    """Extract RAM like '8 GB', '16 GB' from description."""
    gb = find_ram(desc)
    return f"{gb} GB" if gb else ""


def _extract_os_from_desc(desc: str) -> str:
    """Extract OS string from description."""
    result = parse_os(desc)
    return result if result != "Unknown" else ""


def _extract_storage_from_desc(desc: str) -> str:
    """Extract storage like '512 GB SSD', '1 TB' from description."""
    gb, stype = find_storage(desc)
    if not gb:
        return ""
    return f"{gb} GB {stype}" if stype != "UNKNOWN" else f"{gb} GB"


def parse_hit(hit: dict, scraper) -> dict:
    """Convert a single API hit into a flat product record."""
    desc = hit.get("descripcion", "")
    p = {
        "marca": hit.get("marca", ""),
        "clave": hit.get("clave", ""),
        "num_parte": hit.get("numParte", ""),
        "descripcion": desc,
        "modelo": hit.get("modelo", ""),
        "categoria": hit.get("categoria", ""),
        "precio": hit.get("precio", 0),
        "moneda": hit.get("moneda", ""),
        "existencia": hit.get("existencia_total", 0),
        "url": hit.get("url", ""),
        "imagen": hit.get("imagen_url", ""),
    }

    # ficha_tecnica (dict)
    ft = hit.get("ficha_tecnica")
    if isinstance(ft, dict):
        for k, v in ft.items():
            if v:
                p[f"ft_{k}"] = str(v).strip()

    # icecat (list of dicts)
    icecat = hit.get("icecat")
    if isinstance(icecat, list):
        for item in icecat:
            if isinstance(item, dict):
                for k, v in item.items():
                    key = f"ice_{k}"
                    if v and key not in p:
                        p[key] = str(v).strip()

    # procesador: descripcion -> icecat -> pagina individual
    proc = _extract_processor(desc)
    if not proc:
        proc = " ".join(
            v
            for k in ("Familia de procesador", "Modelo del procesador")
            if (v := p.get(f"ice_{k}"))
        )
    if not proc and p.get("url"):
        title = _fetch_title(p["url"], scraper)
        if title:
            proc = _extract_processor(title)
    if proc:
        p["procesador"] = proc

    # ---- ram, sistema_operativo, disco_detalle ----
    # Try ice_valorEditar for RAM first, then description
    ice_ve = p.get("ice_valorEditar", "")
    if ice_ve and re.search(r"^\d+\s*GB$", ice_ve.strip(), re.I):
        p["ram"] = ice_ve.strip()
    else:
        ram = _extract_ram_from_desc(desc)
        if ram:
            p["ram"] = ram

    # OS from description
    os_val = _extract_os_from_desc(desc)
    if os_val:
        p["sistema_operativo"] = os_val

    # Storage from ice_valor (if not screen size) then description
    ice_v = p.get("ice_valor", "")
    if ice_v and not re.search(r"pulgad|inch", ice_v, re.I):
        storage_m = re.search(r"(\d+(?:\.\d+)?)\s*(TB|GB)\s*(SSD|HDD|NVMe)?", ice_v, re.I)
        if storage_m:
            val = float(storage_m.group(1))
            unit = storage_m.group(2).upper()
            stype = storage_m.group(3).upper() if storage_m.group(3) else ""
            gb = int(val * 1024) if unit == "TB" else int(val)
            if gb >= 40:
                p["disco_detalle"] = ice_v.strip()
    if "disco_detalle" not in p:
        storage = _extract_storage_from_desc(desc)
        if storage:
            p["disco_detalle"] = storage

    # ---- page-level fetch for missing data ----
    need_page = False
    if "ram" not in p or "sistema_operativo" not in p or "disco_detalle" not in p or not p.get("procesador"):
        need_page = True

    if need_page and p.get("url"):
        page_specs = _fetch_specs_from_page(p["url"], scraper)
        if "ram" not in p and page_specs.get("ram"):
            p["ram"] = page_specs["ram"]
        if "sistema_operativo" not in p and page_specs.get("sistema_operativo"):
            p["sistema_operativo"] = page_specs["sistema_operativo"]
        if "disco_detalle" not in p and page_specs.get("disco_detalle"):
            p["disco_detalle"] = page_specs["disco_detalle"]

        # CPU from page if still missing (combine familia + modelo)
        if not p.get("procesador"):
            familia = page_specs.get("procesador_familia", "")
            modelo = page_specs.get("procesador_modelo", "")
            if familia and modelo:
                p["procesador"] = _extract_processor(f"{familia} {modelo}")
            elif familia:
                p["procesador"] = _extract_processor(familia)

    return p


def parse_hits(hits: list[dict], scraper) -> list[dict]:
    """Convert a list of API hits into flat product records."""
    return [parse_hit(h, scraper) for h in hits]
