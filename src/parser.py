"""Transform raw Algolia hits into flat product dictionaries."""


def parse_hit(hit: dict) -> dict:
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

    return p


def parse_hits(hits: list[dict]) -> list[dict]:
    """Convert a list of API hits into flat product records."""
    return [parse_hit(h) for h in hits]
