"""Tag resolver for mapping human-readable category names to Polymarket tag IDs."""

import json
import logging
from pathlib import Path
from typing import Optional

from .client import PolymarketClient

logger = logging.getLogger(__name__)


class TagResolver:
    """Resolves human-readable category names to Polymarket tag IDs."""

    CACHE_FILE = Path(__file__).parent.parent.parent / "data" / "polymarket_tags.json"

    def __init__(self, client: Optional[PolymarketClient] = None, cache_file: Optional[Path] = None):
        self.client = client or PolymarketClient()
        self.cache_file = cache_file or self.CACHE_FILE
        self._tag_index: dict[str, dict] = {}
        self._label_to_id: dict[str, str] = {}

    def load_tag_cache(self) -> bool:
        """Load tag cache from disk."""
        if not self.cache_file.exists():
            logger.info("Tag cache not found at %s", self.cache_file)
            return False
        try:
            with open(self.cache_file, "r") as f:
                data = json.load(f)
            self._tag_index = {tag["id"]: tag for tag in data.get("tags", [])}
            self._label_to_id = {tag.get("label", "").lower(): tag["id"] for tag in data.get("tags", []) if tag.get("label")}
            logger.info("Loaded %d tags from cache", len(self._tag_index))
            return True
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("Failed to load tag cache: %s", e)
            return False

    def save_tag_cache(self, tags: list[dict]) -> None:
        """Save tag cache to disk."""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        data = {"tags": tags}
        with open(self.cache_file, "w") as f:
            json.dump(data, f, indent=2)
        logger.info("Saved %d tags to cache", len(tags))

    def build_tag_index(self, force_refresh: bool = False) -> dict[str, dict]:
        """Fetch all tags and build the internal index.
        
        Fetches tags from both /tags endpoint and from events, since not all
        tags appear in the /tags endpoint.
        """
        if not force_refresh and self.load_tag_cache():
            return self._tag_index

        logger.info("Fetching all tags from /tags endpoint...")
        all_tags = []
        offset = 0
        limit = 1000

        while True:
            tags = self.client.get_all_tags(limit=limit, offset=offset)
            if not tags:
                break
            all_tags.extend(tags)
            if len(tags) < limit:
                break
            offset += limit

        seen_ids = {tag["id"] for tag in all_tags}

        logger.info("Fetching additional tags from events...")
        event_tags = self._collect_tags_from_events()
        for tag in event_tags:
            if tag["id"] not in seen_ids:
                all_tags.append(tag)
                seen_ids.add(tag["id"])

        self._tag_index = {tag["id"]: tag for tag in all_tags}
        self._label_to_id = {
            tag.get("label", "").lower(): tag["id"]
            for tag in all_tags
            if tag.get("label")
        }

        self.save_tag_cache(all_tags)
        logger.info("Total tags indexed: %d", len(self._tag_index))
        return self._tag_index

    def _collect_tags_from_events(self) -> list[dict]:
        """Collect tags from events since /tags endpoint is incomplete."""
        collected = []
        for page in range(5):
            events = self.client.get_events(
                active=True, closed=False, limit=100, offset=page * 100
            )
            if not events:
                break
            for event in events:
                for tag in event.get("tags", []):
                    if tag.get("label"):
                        collected.append(tag)
        return collected

    def find_tags_by_label(self, label: str) -> list[dict]:
        """Find all tags whose label contains the given string (case-insensitive)."""
        label_lower = label.lower()
        return [
            tag for tag in self._tag_index.values()
            if tag.get("label") and label_lower in tag["label"].lower()
        ]

    def find_tag_ids_by_label(self, label: str) -> list[str]:
        """Find all tag IDs whose label contains the given string."""
        return [tag["id"] for tag in self.find_tags_by_label(label)]

    def get_tag_id_by_label(self, label: str) -> Optional[str]:
        """Get a single tag ID by exact label match (case-insensitive)."""
        key = label.lower()
        return self._label_to_id.get(key)

    def find_geopolitical_tags(self) -> list[dict]:
        """Find all tags related to geopolitics.
        
        Keywords cover: politics, world affairs, international relations,
        specific countries/regions involved in geopolitical events.
        """
        keywords = [
            "geopolitic", "politics", "world", "foreign", "diplomat",
            "ukraine", "russia", "israel", "iran", "china", "nato",
            "middle east", "war", "conflict", "military", "troop",
            "sovereignty", "invasion", "treaty", "sanction",
        ]
        results = []
        for tag in self._tag_index.values():
            label = tag.get("label", "").lower()
            if any(kw in label for kw in keywords):
                results.append(tag)
        return results

    def get_related_tag_ids(self, tag_id: str) -> list[str]:
        """Get related tag IDs for a given tag ID."""
        related = self.client.get_related_tags(tag_id)
        return [tag["id"] for tag in related]

    def resolve_category_to_ids(self, category: str) -> list[str]:
        """Resolve a category name to all related tag IDs including sub-tags."""
        primary_ids = self.find_tag_ids_by_label(category)
        all_ids = set(primary_ids)

        for tag_id in primary_ids:
            related = self.get_related_tag_ids(tag_id)
            all_ids.update(related)

        return list(all_ids)
