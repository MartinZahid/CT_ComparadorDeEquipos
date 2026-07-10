"""Transform raw Algolia hits into flat product dictionaries."""

import re

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


def _extract_processor(text: str) -> str:
    normalized = text.replace("\u2122", " ").replace("(TM)", " ")
    normalized = re.sub(r"(\d)([a-zA-Z])\s*,\s*", r"\1\2, ", normalized)
    normalized = re.sub(r"(?i)(\b(?:Core|Intel|AMD|Ryzen)\S*\s+\w+-\s+)", lambda m: m.group(1).replace("- ", "-"), normalized)
    normalized = re.sub(r"(?i)(\b(?:Intel|Core|Ultra|Ryzen|AMD|MediaTek|Celeron|Ryzen)\b)\s*,\s*", r"\1 ", normalized)
    normalized = re.sub(r"(?i)(\b(?:Ultra)\s+\d+)\s*,\s*(?=\d)", r"\1 ", normalized)
    normalized = re.sub(r"(?i)(\b(?:Ultra)\s+\d+)\s*,\s+(\d+)", r"\1 \2", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    matches = _PROC_PATTERN.findall(normalized)
    if not matches:
        return ""
    cleaned = [m.strip() for m in matches]
    prefer = [m for m in cleaned if re.search(r"(?:-\w+|(?<!\d)\d{2,}\w*)", m)]
    prefer = [m for m in prefer if not re.match(r"Ryzen\s+\d\s+\d{2,3}$", m, re.I)]
    if prefer:
        return max(prefer, key=len)
    return ""


def _fetch_title(url: str, scraper) -> str:
    try:
        r = scraper.get(url, timeout=15)
        m = re.search(r"<title>(.*?)</title>", r.text, re.DOTALL)
        return m.group(1) if m else ""
    except Exception:
        return ""


def parse_hit(hit: dict, scraper) -> dict:
    """Convert a single API hit into a flat product record."""
    p = {
        "marca": hit.get("marca", ""),
        "clave": hit.get("clave", ""),
        "num_parte": hit.get("numParte", ""),
        "descripcion": hit.get("descripcion", ""),
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
    proc = _extract_processor(p["descripcion"])
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

    return p


def parse_hits(hits: list[dict], scraper) -> list[dict]:
    """Convert a list of API hits into flat product records."""
    return [parse_hit(h, scraper) for h in hits]
