"""CLI entry point – scraper and requirements comparison."""

import argparse
import glob
import json
from datetime import datetime
from pathlib import Path

from src.client import CTClient
from src.api import CTAPI
from src.parser import parse_hits
from src.exporter import save
from src.requirements.comparator import compare_category
from src.requirements.models import RequirementSet
from src.requirements.cpu_db import CPUDatabase


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

    products = parse_hits(hits, client.scraper)

    fecha = datetime.now().strftime("%Y-%m-%d")
    slug = f"{category.lower().replace(' ', '-')}-{fecha}"
    jp, cp = save(products, slug, output_dir)

    print(f"\n[+] TOTAL: {len(products)} equipos")
    print(f"[+] {jp}")
    print(f"[+] {cp}")
    return len(products)


def compare_cmd(args):
    """Compare scraped products against requirements."""
    cpu_db = CPUDatabase()
    print("[*] Cargando base de datos de CPUs...")
    cpu_db.load()
    print(f"[+] CPUs en BD: {len(cpu_db._cpus)}")

    requirements = RequirementSet()

    if args.cat:
        categories = args.cat if isinstance(args.cat, list) else [args.cat]
    else:
        categories = [DEFAULT_CAT]

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    for cat in categories:
        # Find latest JSON for this category
        pattern = str(output_dir / f"ctonline-{cat.lower().replace(' ', '-')}-*.json")
        files = glob.glob(pattern)
        if not files:
            print(f"[!] No hay archivo scrapeado para '{cat}'. Ejecuta el scraper primero.")
            continue

        latest = max(files, key=lambda f: Path(f).stat().st_mtime)
        print(f"[*] Procesando {cat} desde {latest}")

        out_name = f"comparacion-{cat.lower().replace(' ', '-')}.json"
        out_path = output_dir / out_name

        compare_category(
            Path(latest),
            out_path,
            requirements,
            cpu_db
        )

        # Print summary
        with open(out_path, encoding="utf-8") as f:
            data = json.load(f)
        resumen = data["resumen"]
        total = sum(resumen.values())
        print(f"[+] {cat}: {total} productos")
        print(f"    [OK] Recomendados: {resumen.get('recommended', 0)}")
        print(f"    [OK] Minimos: {resumen.get('minimos', 0)}")
        print(f"    [!]  Capaces: {resumen.get('capaz', 0)}")
        print(f"    [X] No corren: {resumen.get('no_corre', 0)}")
        print(f"    [?] Sin datos CPU: {resumen.get('sin_datos_cpu', 0)}")
        print(f"    [FILE] Guardado en: {out_path}")


def main():
    parser = argparse.ArgumentParser(description="CTOnline Scraper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Scraper command
    scraper_parser = subparsers.add_parser("scrape", help="Scrapear productos")
    scraper_parser.add_argument("--cat", "--categoria", default=DEFAULT_CAT, help=f"Categoria (default: {DEFAULT_CAT})")
    scraper_parser.add_argument("--output", "-o", default="./output", help="Carpeta de salida")

    # Compare command
    compare_parser = subparsers.add_parser("compare", help="Comparar contra requisitos")
    compare_parser.add_argument("--cat", "--categoria", action="append", help="Categoría (puede repetirse)")
    compare_parser.add_argument("--output", "-o", default="./output", help="Carpeta de salida")

    args = parser.parse_args()

    print("=" * 50)
    print("  CTOnline Scraper")
    print("=" * 50)

    if args.command == "scrape":
        run(category=args.cat, output_dir=Path(args.output))
    elif args.command == "compare":
        compare_cmd(args)


if __name__ == "__main__":
    main()