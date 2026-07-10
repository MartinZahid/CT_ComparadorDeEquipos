# CTOnline Scraper + Comparador de Requisitos

Proyecto para scrapear productos de CTOnline y clasificarlos según requisitos de software (compatibilidad Point).

## Estructura

```
.
├── src/                    # Scraper principal
│   ├── client.py           # Cliente HTTP con Cloudflare bypass
│   ├── api.py              # Llamadas a API Algolia
│   ├── parser.py           # Extracción de datos (procesador, RAM, storage, OS)
│   ├── exporter.py         # Exportación JSON/CSV
│   ├── cli.py              # CLI: scrape y compare
│   └── requirements/       # Módulo de comparación
│       ├── models.py       # Dataclasses
│       ├── cpu_db.py       # BD Intel/AMD (descarga automática)
│       ├── heuristics.py   # Estimación CPUs nuevas
│       ├── extractor.py    # Parseo specs desde JSON scrapeado
│       ├── classifier.py   # Lógica 4 niveles + puede_correr
│       └── comparator.py   # Orquestador
├── output/                 # JSONs generados (gitignore)
├── data/cpu_db/            # Cache BD CPUs (gitignore)
├── web/                    # Página HTML vanilla (legacy)
└── web-react/              # App React moderna
```

## Instalación

```bash
# Python dependencies
pip install -r requirements.txt

# Web React dependencies
cd web-react && npm install
```

## Uso

### 1. Scrapear productos

```bash
# All in One
python -m src scrape --cat "All in One" --output ./output

# Laptops
python -m src scrape --cat "Laptops" --output ./output

# Ambas categorías
python -m src scrape --cat "All in One" --cat "Laptops" --output ./output
```

### 2. Comparar contra requisitos (genera JSONs de clasificación)

```bash
# Requiere haber scrapeado antes
python -m src compare --cat "All in One" --output ./output

# Ambas categorías
python -m src compare --cat "All in One" --cat "Laptops" --output ./output
```

Esto genera en `output/`:
- `comparacion-all-in-one.json` 
- `comparacion-laptops.json`

### 3. Web React (visualización)

```bash
# Copiar JSONs a public/ (o usar los ya generados)
cp output/comparacion-*.json web-react/public/

# Desarrollo
cd web-react && npm run dev
# → http://localhost:5173

# Producción
cd web-react && npm run build
# → carpeta dist/ lista para deploy
```

### 4. Web HTML legacy (opcional)

```bash
# Solo abrir web/index.html en navegador (requiere JSONs en output/)
```

## Requisitos de compatibilidad (hardcoded en `src/requirements/classifier.py`)

| | Mínimos | Recomendados |
|--|---------|--------------|
| **OS** | Windows 10 64-bit | Windows 11 64-bit |
| **CPU** | 3.6 GHz, 4 núcleos | 3.6 GHz, 4 núcleos |
| **RAM** | 8 GB | 16 GB |
| **Disco** | 1 GB + SSD si ≤128 GB | 1 GB + SSD si ≤128 GB |

## Clasificación (4 niveles)

| Nivel | Badge | Puede correr |
|-------|-------|--------------|
| `recommended` | ✅ Recomendado | ✅ Sí |
| `minimos` | ✅ Mínimos | ✅ Sí |
| `capaz` | ⚠️ Capaz | ✅ Sí (CPU+RAM OK, le falta OS/Disco) |
| `no_corre` | ❌ No corre | ❌ No |
| `sin_datos_cpu` | ❓ Sin datos CPU | ❌ No |

## BD de CPUs

- **Fuente**: `felixsteinke/cpu-spec-dataset` (Intel ARK + AMD Specs)
- **3,200+ CPUs** descargadas automáticamente en primera ejecución
- **Cache**: `data/cpu_db/normalized.pkl`
- **Fuzzy matching**: `rapidfuzz` (score ≥ 85)
- **Heurística**: CPUs nuevas no en BD (Core Ultra, Ryzen AI) estimadas por nombre

## Outputs JSON

```json
{
  "requisitos_usados": { "minimos": {...}, "recomendados": {...} },
  "resultados": [
    {
      "clave": "AIOHPI1410",
      "marca": "HP",
      "procesador": "Core Ultra 5 125U",
      "ram_gb": 16,
      "storage_gb": 512,
      "storage_type": "SSD",
      "os": "Windows 11 Home",
      "nivel": "recommended",
      "puede_correr": true,
      "razones": [...],
      "descripcion": "HP AIOHPI1410, Core Ultra 5 125U, 16GB RAM, 512GB SSD, Windows 11 Home",
      "url": "https://ctonline.mx/...",
      "imagen": "https://static.ctonline.mx/...",
      "categoria": "all-in-one"
    }
  ],
  "resumen": { "recommended": 12, "minimos": 6, "capaz": 6, "no_corre": 5, "sin_datos_cpu": 6 }
}
```

## Tech Stack

- **Python**: cloudscraper, rapidfuzz, requests, pandas
- **Web**: React + Vite, vanilla CSS (responsive, mobile-first)