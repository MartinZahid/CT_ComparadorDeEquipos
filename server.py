"""FastAPI backend: runs scraper + compare, serves comparison data."""

import json
import subprocess
import uuid
from pathlib import Path
from threading import Thread

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="CTOnline Scraper API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

OUTPUT_DIR = Path("output")
CATEGORIES = ["All in One", "Laptops"]

_refresh_tasks: dict[str, dict] = {}


def _run_refresh(task_id: str, categories: list[str]):
    lines = []
    try:
        for cat in categories:
            lines.append(f"Scrapeando {cat}...")
            r = subprocess.run(
                ["python", "-m", "src.cli", "scrape", "--cat", cat],
                capture_output=True, text=True, timeout=300,
                cwd=Path(__file__).parent,
            )
            out = r.stdout.strip() or "ok"
            lines.append(out[-300:])

            lines.append(f"Comparando {cat}...")
            r = subprocess.run(
                ["python", "-m", "src.cli", "compare", "--cat", cat],
                capture_output=True, text=True, timeout=120,
                cwd=Path(__file__).parent,
            )
            out = r.stdout.strip() or "ok"
            lines.append(out[-300:])

        _refresh_tasks[task_id] = {"status": "done", "error": None, "output": "\n".join(lines)}
    except Exception as e:
        _refresh_tasks[task_id] = {"status": "done", "error": str(e), "output": str(e)}


def _load_comparison(slug: str) -> dict | None:
    path = OUTPUT_DIR / f"comparacion-{slug}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


@app.post("/api/refresh")
def start_refresh():
    task_id = str(uuid.uuid4())
    _refresh_tasks[task_id] = {"status": "running", "error": None, "output": ""}
    Thread(target=_run_refresh, args=(task_id, CATEGORIES), daemon=True).start()
    return {"task_id": task_id, "status": "started"}


@app.get("/api/refresh-status/{task_id}")
def get_status(task_id: str):
    task = _refresh_tasks.get(task_id)
    if not task:
        return {"status": "not_found"}
    return task


@app.get("/api/products")
def get_products():
    aio = _load_comparison("all-in-one")
    laptops = _load_comparison("laptops")

    products = []
    timestamps = []

    if aio:
        for r in aio["resultados"]:
            products.append({**r, "categoria": "all-in-one", "categoriaLabel": "All in One"})
        if aio.get("fecha_generacion"):
            timestamps.append(aio["fecha_generacion"])

    if laptops:
        for r in laptops["resultados"]:
            products.append({**r, "categoria": "laptops", "categoriaLabel": "Laptops"})
        if laptops.get("fecha_generacion"):
            timestamps.append(laptops["fecha_generacion"])

    last_updated = (
        max(timestamps) if timestamps else None
    )

    return {"products": products, "last_updated": last_updated}
