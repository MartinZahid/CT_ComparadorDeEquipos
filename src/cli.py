"""CLI entry point – default: All in One, opcional --cat."""

import argparse
from datetime import datetime
from pathlib import Path

from src.client import CTClient
from src.api import CTAPI
from src.parser import parse_hits
from src.exporter import save


DEFAULT_CAT = "All in One"


def run(category: str, output_dir: Path) -> int:
    """Run the scraper for one category, all pages."""
    client = CTClient()

    print("[*] Resolviendo Cloudflare...", end=" ", flush=True)
    if not client.resolve_cloudflare():
        print("fallo")
        return 0
    print("ok")

    api = CTAPI(client)
    filt = {"categoria": [category]}

    print(f"[*] Categoria: {category} (todas las paginas)")
    hits = api.fetch_all(filters=filt)

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
    parser.add_argument("--cat", "--categoria", default=DEFAULT_CAT, help=f"Categoria (default: {DEFAULT_CAT})")
    parser.add_argument("--output", "-o", default="./output", help="Carpeta de salida")
    args = parser.parse_args()

    print("=" * 50)
    print("  CTOnline Scraper")
    print("=" * 50)

    run(category=args.cat, output_dir=Path(args.output))


if __name__ == "__main__":
    main()