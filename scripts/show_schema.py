#!/usr/bin/env python3
"""Muestra la estructura COMPLETA del API de CTOnline reusando CTClient/CTAPI."""
import json
import sys
sys.path.insert(0, '.')

from src.client import CTClient
from src.api import CTAPI

client = CTClient()
print("Resolviendo Cloudflare...")
if not client.resolve_cloudflare():
    print("Error: no se pudo resolver Cloudflare")
    sys.exit(1)

api = CTAPI(client)

# 1. Metadata
print("=" * 60)
print("META / categorias disponibles")
print("=" * 60)
cats = api.get_categories()
for name, count in cats[:10]:
    print(f"  {name}: {count} productos")
print(f"  ... ({len(cats)} categorias en total)")

# 2. Primer producto a detalle
print("\n" + "=" * 60)
print("PRIMER PRODUCTO (estructura completa)")
print("=" * 60)
hits = api.fetch_first_page()
if hits:
    h = hits[0]
    print(f"\n{h.get('marca', '?')} - {h.get('clave', '?')}")
    print("-" * 40)
    for k, v in h.items():
        if isinstance(v, dict):
            print(f"  {k}: <dict> con {len(v)} llaves -> {list(v.keys())[:6]}")
        elif isinstance(v, list):
            if v and isinstance(v[0], dict):
                print(f"  {k}: <list[{len(v)}]> de dicts con llaves: {list(v[0].keys())[:6]}")
            else:
                print(f"  {k}: <list[{len(v)}]> {str(v)[:80]}")
        elif isinstance(v, bool):
            print(f"  {k}: {v}")
        else:
            print(f"  {k}: {v}")
else:
    print("No hay productos")
