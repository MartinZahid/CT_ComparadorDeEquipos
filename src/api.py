"""Build payloads and paginate through the CTOnline Algolia proxy."""

from src.client import CTClient


HITS_PER_PAGE = 20


class CTAPI:
    """High-level API caller with pagination support."""

    def __init__(self, client: CTClient):
        self.client = client

    def fetch_page(self, page: int = 0, query: str = "", filters: dict | None = None) -> dict | None:
        """Fetch a single page of results."""
        body = {
            "b": query,
            "p": page,
            "ordenar": "",
            "filtros": filters or {},
        }
        return self.client.post_api(body)

    def fetch_all(self, filters: dict | None = None, query: str = "") -> list[dict]:
        """Fetch all pages for the given filters."""
        all_hits = []
        page = 0

        while True:
            data = self.fetch_page(page=page, query=query, filters=filters)
            if not data:
                break

            datos = data.get("datos")
            if not datos:
                break

            hits = datos.get("hits", [])
            if not hits:
                break

            all_hits.extend(hits)
            nb_pages = datos.get("nbPages", 1)

            if page >= nb_pages - 1:
                break
            page += 1

        return all_hits

    def fetch_first_page(self, filters: dict | None = None, query: str = "") -> list[dict]:
        """Fetch only the first page."""
        data = self.fetch_page(page=0, query=query, filters=filters)
        if not data:
            return []
        datos = data.get("datos", {})
        return datos.get("hits", [])

    def get_meta(self, filters: dict | None = None) -> dict:
        """Get metadata (nbHits, nbPages, facets) without fetching all hits."""
        data = self.fetch_page(page=0, filters=filters)
        if not data:
            return {}
        datos = data.get("datos", {})
        return {
            "nbHits": datos.get("nbHits", 0),
            "nbPages": datos.get("nbPages", 0),
            "hitsPerPage": datos.get("hitsPerPage", HITS_PER_PAGE),
            "facets": datos.get("facets", {}),
        }
