"""FastAPI backend: serves comparison data, classifies on demand, refreshes from web.

NOTE: No authentication on /api/refresh — designed for local/internal network use
only. Do NOT expose this server to the public internet without adding auth.
"""

import json
import subprocess
import time
import uuid
from pathlib import Path
from threading import Thread

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.requirements.models import CPURequirement, RequirementSet, ProductSpec, CPUInfo
from src.requirements.classifier import classify
from src.spec_parsing import parse_os

OUTPUT_DIR = Path("output")
CATEGORIES = ["All in One", "Laptops"]
REFRESH_COOLDOWN_SECS = 300  # 5 min between refreshes
TASK_MAX_AGE_SECS = 3600  # 1 hour

app = FastAPI(title="CTOnline Scraper API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_refresh_tasks: dict[str, dict] = {}
_last_refresh_at: float = 0


# ── Pydantic models for /api/classify ──────────────────────────────

class CPUReqIn(BaseModel):
    min_ghz: float = 3.6
    min_cores: int = 4
    rec_ghz: float = 3.6
    rec_cores: int = 4


class RequirementSetIn(BaseModel):
    cpu: CPUReqIn = CPUReqIn()
    ram_min_gb: int = 8
    ram_rec_gb: int = 16
    disk_min_gb: int = 1
    disk_rec_gb: int = 1
    ssd_required_below_gb: int = 128
    os_min: str = "Windows 10"
    os_rec: str = "Windows 11"


class ProductIn(BaseModel):
    clave: str
    marca: str = ""
    procesador: str = ""
    ram_gb: int = 0
    storage_gb: int = 0
    storage_type: str = "UNKNOWN"
    os: str = "Unknown"
    cpu_turbo_ghz: float | None = None
    cpu_cores: int | None = None
    cpu_source: str = "none"
    url: str = ""
    imagen: str = ""
    categoria: str = ""
    categoriaLabel: str = ""
    descripcion: str = ""


class ClassifyRequest(BaseModel):
    products: list[ProductIn]
    requirements: RequirementSetIn = RequirementSetIn()


# ── Helpers ────────────────────────────────────────────────────────

def _product_to_spec(p: ProductIn) -> ProductSpec:
    return ProductSpec(
        marca=p.marca,
        clave=p.clave,
        procesador=p.procesador,
        cpu=CPUInfo(
            model=p.procesador,
            matched_model=None,
            base_ghz=None,
            turbo_ghz=p.cpu_turbo_ghz,
            cores=p.cpu_cores,
            threads=None,
            source=p.cpu_source,
        ),
        ram_gb=p.ram_gb,
        storage_gb=p.storage_gb,
        storage_type=p.storage_type,
        os=parse_os(p.os),
    )


def _req_to_backend(req: RequirementSetIn) -> RequirementSet:
    return RequirementSet(
        os_min=req.os_min,
        os_rec=req.os_rec,
        cpu=CPURequirement(
            min_ghz=req.cpu.min_ghz,
            min_cores=req.cpu.min_cores,
            rec_ghz=req.cpu.rec_ghz,
            rec_cores=req.cpu.rec_cores,
        ),
        ram_min_gb=req.ram_min_gb,
        ram_rec_gb=req.ram_rec_gb,
        disk_min_gb=req.disk_min_gb,
        disk_rec_gb=req.disk_rec_gb,
        ssd_required_below_gb=req.ssd_required_below_gb,
    )


def _cleanup_old_tasks():
    now = time.time()
    stale = [tid for tid, t in _refresh_tasks.items()
             if now - t.get("created_at", 0) > TASK_MAX_AGE_SECS]
    for tid in stale:
        _refresh_tasks.pop(tid, None)


def _load_comparison(slug: str) -> dict | None:
    path = OUTPUT_DIR / f"comparacion-{slug}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def _run_refresh(task_id: str, categories: list[str]):
    lines = []
    try:
        for cat in categories:
            lines.append(f"Scrapeando {cat}...")
            _refresh_tasks[task_id]["output"] = "\n".join(lines)
            r = subprocess.run(
                ["python", "-m", "src.cli", "scrape", "--cat", cat],
                capture_output=True, text=True, timeout=300,
                cwd=Path(__file__).parent,
            )
            out = r.stdout.strip() or "ok"
            lines.append(out[-300:])

            lines.append(f"Comparando {cat}...")
            _refresh_tasks[task_id]["output"] = "\n".join(lines)
            r = subprocess.run(
                ["python", "-m", "src.cli", "compare", "--cat", cat],
                capture_output=True, text=True, timeout=120,
                cwd=Path(__file__).parent,
            )
            out = r.stdout.strip() or "ok"
            lines.append(out[-300:])

        _refresh_tasks[task_id].update(status="done", error=None, output="\n".join(lines))
    except Exception as e:
        _refresh_tasks[task_id].update(status="done", error=str(e), output=str(e))


# ── Endpoints ──────────────────────────────────────────────────────

@app.post("/api/refresh")
def start_refresh():
    global _last_refresh_at
    now = time.time()
    if now - _last_refresh_at < REFRESH_COOLDOWN_SECS:
        remaining = int(REFRESH_COOLDOWN_SECS - (now - _last_refresh_at))
        raise HTTPException(429, f"Espera {remaining}s entre recargas")
    _last_refresh_at = now

    task_id = str(uuid.uuid4())
    _cleanup_old_tasks()
    _refresh_tasks[task_id] = {"status": "running", "error": None, "output": "", "created_at": now}
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

    for dataset, slug, label in [
        (aio, "all-in-one", "All in One"),
        (laptops, "laptops", "Laptops"),
    ]:
        if dataset:
            for r in dataset["resultados"]:
                r["os"] = parse_os(r.get("os", ""))
                products.append({**r, "categoria": slug, "categoriaLabel": label})
            if dataset.get("fecha_generacion"):
                timestamps.append(dataset["fecha_generacion"])

    last_updated = max(timestamps) if timestamps else None
    return {"products": products, "last_updated": last_updated}


@app.post("/api/classify")
def reclassify(body: ClassifyRequest):
    """Reclassify products with custom requirements (single source of truth = classify.py)."""
    req = _req_to_backend(body.requirements)
    results = []
    for p in body.products:
        spec = _product_to_spec(p)
        cls = classify(spec, req)
        results.append({
            "clave": p.clave,
            "nivel": cls.nivel,
            "puede_correr": cls.puede_correr,
            "razones": cls.reasons,
            "score": cls.score,
        })
    return {"products": results}
