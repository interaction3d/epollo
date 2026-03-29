"""High-level fetcher for Polymarket questions/markets."""

import logging
from datetime import datetime, timedelta
from typing import Optional

from .client import PolymarketClient
from .tag_resolver import TagResolver

logger = logging.getLogger(__name__)


class PolymarketFetcher:
    """High-level interface for fetching Polymarket questions."""

    GEOPOLITICAL_KEYWORDS = [
        "geopolitic", "politics", "world", "foreign", "diplomat",
        "ukraine", "russia", "israel", "iran", "china", "nato",
        "middle east", "war", "conflict", "military", "troop",
        "sovereignty", "invasion", "treaty", "sanction", "peace",
        "terrorism", "terrorist", "nuclear", "missile", "airstrike",
        "ceasefire", "alliance", "embargo", "regime", "kremlin",
    ]

    KNOWN_GEOPOLITICAL_TAG_IDS = [
        "100265", "101253", "2", "101970", "101794",
        "96", "180", "154", "95", "303", "1597", "101206", "366",
        "126", "101191",
    ]

    def __init__(
        self,
        client: Optional[PolymarketClient] = None,
        tag_resolver: Optional[TagResolver] = None,
    ):
        self.client = client or PolymarketClient()
        self.resolver = tag_resolver or TagResolver(client=self.client)
        self._geopolitical_tag_ids: Optional[list[str]] = None

    def get_geopolitical_questions(
        self,
        limit: int = 50,
        include_related: bool = True,
        days_back: Optional[int] = None,
    ) -> list[dict]:
        """Fetch latest geopolitical questions from Polymarket.

        Args:
            limit: Maximum number of questions to return
            include_related: Whether to include related sub-tags (Ukraine, Russia, Israel, etc.)
            days_back: If set, only return questions created within this many days

        Returns:
            List of dictionaries with question details
        """
        if self._geopolitical_tag_ids is None:
            self._resolve_geopolitical_tags(include_related=include_related)

        cutoff_date = None
        if days_back:
            from zoneinfo import ZoneInfo
            cutoff_date = datetime.now(ZoneInfo("UTC")) - timedelta(days=days_back)

        all_questions = []
        seen_slugs = set()

        for tag_id in self._geopolitical_tag_ids:
            try:
                events = self.client.get_events(
                    tag_id=tag_id,
                    active=True,
                    closed=False,
                    limit=100,
                    order="volume24hr",
                    ascending=False,
                )
                for event in events:
                    slug = event.get("slug")
                    if slug and slug not in seen_slugs:
                        seen_slugs.add(slug)
                        question = self._parse_event(event)
                        
                        if cutoff_date:
                            created = self._get_event_date(event)
                            if created and created < cutoff_date:
                                continue
                        
                        all_questions.append(question)
            except Exception as e:
                logger.warning("Failed to fetch events for tag %s: %s", tag_id, e)

            if len(all_questions) >= limit * 2:
                break

        all_questions.sort(key=lambda x: x.get("volume", 0), reverse=True)
        return all_questions[:limit]

    def get_geopolitical_recent_high_volume(
        self,
        limit: int = 20,
        days_back: int = 60,
    ) -> list[dict]:
        """Fetch high-volume geopolitical questions from the last N days.
        
        Args:
            limit: Maximum number of questions to return
            days_back: Number of days to look back (default 60 = 2 months)
            
        Returns:
            List of dictionaries with question details, sorted by volume
        """
        from zoneinfo import ZoneInfo
        cutoff_date = datetime.now(ZoneInfo("UTC")) - timedelta(days=days_back)
        logger.info("Looking for events created after %s", cutoff_date.isoformat())
        
        all_events = []
        seen_slugs = set()
        total_fetched = 0
        
        all_tag_ids = list(set(self.KNOWN_GEOPOLITICAL_TAG_IDS))
        
        for tag_id in all_tag_ids:
            try:
                for page in range(5):
                    events = self.client.get_events(
                        tag_id=tag_id,
                        active=True,
                        closed=False,
                        limit=100,
                        offset=page * 100,
                        order="volume24hr",
                        ascending=False,
                    )
                    if not events:
                        break
                    
                    for event in events:
                        slug = event.get("slug")
                        if slug and slug not in seen_slugs:
                            seen_slugs.add(slug)
                            created = self._get_event_date(event)
                            if created and created >= cutoff_date:
                                all_events.append(event)
                                total_fetched += 1
                    
                    total_fetched += len(events)
                    
                    if len(events) < 100:
                        break
                        
            except Exception as e:
                logger.warning("Error fetching tag %s: %s", tag_id, e)
                continue

        if len(all_events) < limit * 2:
            logger.info("Fetching more events from general pool...")
            for page in range(20):
                try:
                    events = self.client.get_events(
                        active=True,
                        closed=False,
                        limit=100,
                        offset=page * 100,
                        order="volume24hr",
                        ascending=False,
                    )
                    if not events:
                        break
                    
                    for event in events:
                        slug = event.get("slug")
                        if slug and slug not in seen_slugs:
                            seen_slugs.add(slug)
                            created = self._get_event_date(event)
                            if created and created >= cutoff_date:
                                all_events.append(event)
                    
                    total_fetched += len(events)
                    
                    if len(events) < 100:
                        break
                        
                except Exception as e:
                    logger.warning("Error fetching general events: %s", e)
                    continue

        parsed = [self._parse_event(e) for e in all_events]
        geo_filtered = [e for e in parsed if self._is_geopolitical(e)]
        
        if len(geo_filtered) < limit:
            logger.info("Not enough geo events (%d), adding top volume events", len(geo_filtered))
            remaining = limit - len(geo_filtered)
            non_geo = [e for e in parsed if not self._is_geopolitical(e)]
            non_geo.sort(key=lambda x: x.get("volume", 0), reverse=True)
            geo_filtered.extend(non_geo[:remaining])
        
        geo_filtered.sort(key=lambda x: x.get("volume", 0), reverse=True)
        
        logger.info("Fetched %d events, %d are geopolitical, returning top %d",
                    total_fetched, len(geo_filtered), min(limit, len(geo_filtered)))
        
        return geo_filtered[:limit]

    def _is_geopolitical(self, question: dict) -> bool:
        """Check if a question is geopolitical based on keywords and tags."""
        tags = [t.lower() for t in question.get("tags", [])]
        title = question.get("question", "").lower()
        description = question.get("description", "").lower()
        
        combined = " ".join(tags) + " " + title + " " + description
        
        for kw in self.GEOPOLITICAL_KEYWORDS:
            if kw in combined:
                return True
        return False

    def _get_event_date(self, event: dict) -> Optional[datetime]:
        """Extract datetime from event."""
        created = event.get("creationDate")
        if not created:
            return None
        try:
            return datetime.fromisoformat(created.replace("Z", "+00:00"))
        except:
            return None

    def get_questions_by_tag(self, tag_id: str, limit: int = 100) -> list[dict]:
        """Fetch questions for a specific tag ID."""
        try:
            events = self.client.get_events(
                tag_id=tag_id,
                active=True,
                closed=False,
                limit=limit,
                order="volume24hr",
                ascending=False,
            )
            return [self._parse_event(e) for e in events]
        except Exception as e:
            logger.warning("Failed to fetch events for tag %s: %s", tag_id, e)
            return []

    def _resolve_geopolitical_tags(self, include_related: bool = True) -> None:
        """Resolve geopolitical category to tag IDs."""
        self.resolver.build_tag_index()
        geo_tags = self.resolver.find_geopolitical_tags()
        tag_ids = [tag["id"] for tag in geo_tags]
        logger.info("Found %d geopolitical tags", len(tag_ids))

        if include_related:
            all_ids = set(tag_ids)
            for tag_id in tag_ids:
                try:
                    related = self.resolver.get_related_tag_ids(tag_id)
                    all_ids.update(related)
                except Exception as e:
                    logger.warning("Failed to get related tags for %s: %s", tag_id, e)
            tag_ids = list(all_ids)
            logger.info("Expanded to %d tags with related", len(tag_ids))

        self._geopolitical_tag_ids = tag_ids

    def _parse_event(self, event: dict) -> dict:
        """Parse an event into a structured question dict."""
        slug = event.get("slug", "")
        
        outcomes = []
        markets = event.get("markets", [])
        if markets:
            primary_market = markets[0]
            raw_outcomes = primary_market.get("outcomes", [])
            raw_prices = primary_market.get("outcomePrices", [])
            
            if isinstance(raw_outcomes, str):
                try:
                    import json
                    raw_outcomes = json.loads(raw_outcomes)
                except:
                    raw_outcomes = []
            if isinstance(raw_prices, str):
                try:
                    import json
                    raw_prices = json.loads(raw_prices)
                except:
                    raw_prices = []
            
            outcome_probs = []
            for o, p in zip(raw_outcomes, raw_prices):
                try:
                    prob = float(p) * 100
                    outcome_probs.append((o, prob))
                except (ValueError, TypeError):
                    continue
            
            outcome_probs.sort(key=lambda x: x[1], reverse=True)
            outcomes = [{"outcome": o, "probability": p} for o, p in outcome_probs[:3]]
        
        return {
            "question": event.get("title", event.get("question", "")),
            "slug": slug,
            "url": f"https://polymarket.com/event/{slug}" if slug else "",
            "description": event.get("description", ""),
            "tags": [t.get("label", "") for t in event.get("tags", []) if t.get("label")],
            "volume_24hr": float(event.get("volume24hr", 0) or 0),
            "volume": float(event.get("volume", 0) or 0),
            "liquidity": float(event.get("liquidity", 0) or 0),
            "start_date": event.get("startDate", ""),
            "end_date": event.get("endDate", ""),
            "active": event.get("active", False),
            "closed": event.get("closed", False),
            "creation_date": event.get("creationDate", ""),
            "outcomes": outcomes,
        }

    def get_all_latest_questions(self, limit: int = 50) -> list[dict]:
        """Fetch latest questions from all active markets (no tag filtering)."""
        all_questions = []
        seen_slugs = set()
        offset = 0

        while len(all_questions) < limit:
            events = self.client.get_events(
                active=True,
                closed=False,
                limit=100,
                offset=offset,
                order="volume24hr",
                ascending=False,
            )
            if not events:
                break

            for event in events:
                slug = event.get("slug")
                if slug and slug not in seen_slugs:
                    seen_slugs.add(slug)
                    all_questions.append(self._parse_event(event))

            offset += 100

            if len(events) < 100:
                break

        return all_questions[:limit]
