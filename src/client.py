"""HTTP client with Cloudflare bypass via cloudscraper."""

import cloudscraper


BASE = "https://ctonline.mx"
SEARCH = f"{BASE}/buscar/interactiva"
API = f"{BASE}/algolia_search/buscar"


class CTClient:
    """Wraps cloudscraper session with CTOnline-specific headers."""

    def __init__(self):
        self.scraper = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "desktop": True},
            delay=10,
        )
        self.scraper.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/150.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
        })
        self._cf_ok = False

    @property
    def api_headers(self) -> dict:
        return {
            "Origin": BASE,
            "Referer": f"{SEARCH}?style=list",
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
        }

    def resolve_cloudflare(self) -> bool:
        """Visit search page to trigger + solve the JS challenge."""
        try:
            r = self.scraper.get(f"{SEARCH}?style=list", timeout=30)
            self._cf_ok = r.status_code == 200
            return self._cf_ok
        except Exception:
            return False

    def post_api(self, body: dict) -> dict | None:
        """POST to the Algolia proxy endpoint."""
        try:
            r = self.scraper.post(API, json=body, headers=self.api_headers, timeout=30)
            return r.json() if r.status_code == 200 else None
        except Exception:
            return None
