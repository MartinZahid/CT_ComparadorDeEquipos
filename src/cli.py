"""CLI entry point."""

import argparse
from datetime import datetime
from pathlib import Path

from src.client import CTClient
from src.api import CTAPI
from src.parser import parse_hits
from src.exporter import save


DEFAULT_CAT = "All in One"


def build_filter(category: str) -> dict:
    return {"categoria": [category]} if category else {}


def run(category: str, all_pages: bool, output_dir: Path) -> int:
    """Run the scraper. Returns product count."""
    client = CTClient()

    print("[*] Resolviendo Cloudflare...", end=" ", flush=True)
    if not client.resolve_cloudflare():
        print("fallo")
        return 0
    print("ok")

    api = CTAPI(client)
    filt = build_filter(category)

    if all_pages:
        print(f"[*] Categoria: {category} ({'todas las paginas'})")
        hits = api.fetch_all(filters=filt)
    else:
        meta = api.get_meta(filters=filt)
        total = meta.get("nbHits", 0)
        print(f"[*] Categoria: {category} ({total} productos, solo primera pagina)")
        hits = api.fetch_first_page(filters=filt)

    if not hits:
        print("[!] No se encontraron productos")
        return 0

    products = parse_hits(hits)

    fecha = datetime.now().strftime("%Y-%m-%d")
    slug = f"{category.lower().replace(' ', '-')}-{fecha}"
    jp, cp = save(products, slug, output_dir)

    print(f"\n[+] TOTAL: {len(products)} equipos")
    print(f"[+] {jp}")
    print(f"[+] {cp}")
    return len(products)


def main():
    parser = argparse.ArgumentParser(description="CTOnline Scraper")
    parser.add_argument("--cat", "--categoria", default=DEFAULT_CAT, help="Categoria")
    parser.add_argument("--all", action="store_true", help="Todas las paginas")
    parser.add_argument("--output", "-o", default="./output", help="Carpeta de salida")
    parser.add_argument("--meta", action="store_true", help="Solo mostrar metadatos (conteo, facetas)")
    args = parser.parse_args()

    print("=" * 50)
    print("  CTOnline Scraper")
    print("=" * 50)

    if args.meta:
        client = CTClient()
        if not client.resolve_cloudflare():
            print("[!] Cloudflare fallo")
            return
        api = CTAPI(client)
        filt = build_filter(args.cat)
        meta = api.get_meta(filters=filt)
        print(f"\nCategoria: {args.cat}")
        print(f"Productos: {meta.get('nbHits', 0)}")
        print(f"Paginas:   {meta.get('nbPages', 0)}")
        print(f"Facetas:   {list(meta.get('facets', {}).keys())[:10]}...")
        return

    run(category=args.cat, all_pages=args.all, output_dir=Path(args.output))


if __name__ == "__main__":
    main()
