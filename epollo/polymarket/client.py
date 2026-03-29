"""Polymarket API client for fetching market data."""

import requests
from typing import Optional


BASE_URL = "https://gamma-api.polymarket.com"


class PolymarketClient:
    """Client for interacting with the Polymarket Gamma API."""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()

    def _get(self, endpoint: str, params: Optional[dict] = None) -> list | dict:
        """Make a GET request to the API."""
        url = f"{self.base_url}{endpoint}"
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()

    def get_all_tags(
        self, limit: int = 1000, offset: int = 0
    ) -> list[dict]:
        """Fetch all available tags."""
        return self._get("/tags", params={"limit": limit, "offset": offset})

    def get_tag_by_id(self, tag_id: str) -> dict:
        """Fetch a specific tag by ID."""
        return self._get(f"/tags/{tag_id}")

    def get_related_tags(self, tag_id: str, status: str = "active") -> list[dict]:
        """Fetch tags related to a given tag ID."""
        return self._get(
            f"/tags/{tag_id}/related-tags/tags",
            params={"status": status, "omit_empty": True},
        )

    def get_events(
        self,
        tag_id: Optional[str] = None,
        active: bool = True,
        closed: bool = False,
        limit: int = 100,
        offset: int = 0,
        order: str = "volume24hr",
        ascending: bool = False,
    ) -> list[dict]:
        """Fetch events (markets grouped by outcome) filtered by tag."""
        params = {
            "active": str(active).lower(),
            "closed": str(closed).lower(),
            "limit": limit,
            "offset": offset,
            "order": order,
            "ascending": str(ascending).lower(),
        }
        if tag_id:
            params["tag_id"] = tag_id
        return self._get("/events", params=params)

    def get_markets(
        self,
        slug: Optional[str] = None,
        tag_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        """Fetch individual markets."""
        params = {"limit": limit, "offset": offset}
        if slug:
            params["slug"] = slug
        if tag_id:
            params["tag_id"] = tag_id
        return self._get("/markets", params=params)

    def get_event_by_slug(self, slug: str) -> dict:
        """Fetch a single event by slug."""
        return self._get("/events", params={"slug": slug})

    def get_market_by_slug(self, slug: str) -> dict:
        """Fetch a single market by slug."""
        return self._get("/markets", params={"slug": slug})
