#!/usr/bin/env python3
"""Muestra la estructura COMPLETA del API de CTOnline."""
import json
import cloudscraper

scraper = cloudscraper.create_scraper(delay=10)
scraper.headers.update({'User-Agent': 'Mozilla/5.0 Chrome/150.0', 'Accept-Language': 'es-MX,es;q=0.9'})
scraper.get('https://ctonline.mx/buscar/interactiva?style=list', timeout=30)

r = scraper.post('https://ctonline.mx/algolia_search/buscar', json={
    "b": "", "p": 0, "ordenar": "", "filtros": {}
}, headers={
    'Origin': 'https://ctonline.mx', 'Referer': 'https://ctonline.mx/buscar/interactiva?style=list',
    'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest',
}, timeout=30)

data = r.json()
datos = data.get("datos", {})

# 1. Estructura general
print("=" * 60)
print("ESTRUCTURA DEL API: /algolia_search/buscar")
print("=" * 60)

# Response wrapper
print("\n[RESPONSE WRAPPER]")
for k in ('estatus', 'codigo', 'mensaje'):
    print(f"  {k}: {data.get(k)}")

# datos
print("\n[DATOS - metadatos]")
meta_keys = ['nbHits', 'page', 'nbPages', 'hitsPerPage', 'query', 'params', 'queryID', 'precio_min', 'precio_max']
for k in meta_keys:
    if k in datos:
        print(f"  {k}: {datos[k]}")

# Facetas disponibles
print("\n[FACETAS disponibles]")
facets = datos.get("facets", {})
for fn, fv in facets.items():
    if isinstance(fv, dict):
        print(f"  {fn}: {len(fv)} valores (ej: {dict(list(fv.items())[:3])})")
    else:
        print(f"  {fn}: {fv}")

# 2. Campos de cada producto (hit)
print("\n" + "=" * 60)
print("CAMPOS DE CADA PRODUCTO (hit)")
print("=" * 60)

hits = datos.get("hits", [])
if hits:
    h = hits[0]
    print(f"\nEjemplo: {h.get('marca')} - {h.get('clave')}")
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
    print("No hay hits")

# 3. ficha_tecnica a detalle
print("\n" + "=" * 60)
print("FICHA TECNICA (ejemplo)")
print("=" * 60)
for h in hits[:1]:
    ft = h.get("ficha_tecnica")
    if isinstance(ft, dict):
        for k, v in ft.items():
            print(f"  {k}: {v}")
    elif isinstance(ft, list):
        print(f"  (lista vacia o sin datos)")

# 4. icecat specs
print("\n" + "=" * 60)
print("ICECAT (ejemplo)")
print("=" * 60)
for h in hits[:1]:
    ice = h.get("icecat")
    if isinstance(ice, list):
        for item in ice[:3]:
            if isinstance(item, dict):
                for k, v in item.items():
                    print(f"  {k}: {v}")
                print("  ---")
