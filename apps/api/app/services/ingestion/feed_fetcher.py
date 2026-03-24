"""RSS/Atom feed fetcher — parses feeds and returns raw article data."""
import logging
from datetime import datetime, timezone
from typing import TypedDict

import feedparser
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class RawArticle(TypedDict):
    title: str
    url: str
    content_raw: str | None
    image_url: str | None
    author: str | None
    published_at: datetime | None
    source_id: int


def _parse_date(entry) -> datetime | None:
    for attr in ("published_parsed", "updated_parsed"):
        val = getattr(entry, attr, None)
        if val:
            try:
                return datetime(*val[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return None


def _extract_image(entry) -> str | None:
    # Try media:thumbnail
    media = getattr(entry, "media_thumbnail", None)
    if media and isinstance(media, list):
        return media[0].get("url")
    # Try enclosures
    for enc in getattr(entry, "enclosures", []):
        if enc.get("type", "").startswith("image"):
            return enc.get("href") or enc.get("url")
    # Try content
    for content in getattr(entry, "content", []):
        if "img" in content.get("value", ""):
            import re
            m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content["value"])
            if m:
                return m.group(1)
    return None


def _extract_content(entry) -> str | None:
    # Full content preferred
    for content in getattr(entry, "content", []):
        if content.get("value"):
            from bs4 import BeautifulSoup
            return BeautifulSoup(content["value"], "lxml").get_text(" ", strip=True)[:5000]
    # Summary fallback
    summary = getattr(entry, "summary", None)
    if summary:
        from bs4 import BeautifulSoup
        return BeautifulSoup(summary, "lxml").get_text(" ", strip=True)[:5000]
    return None


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def fetch_feed(rss_url: str, source_id: int) -> list[RawArticle]:
    """Fetch and parse an RSS/Atom feed, return list of raw articles."""
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(rss_url, headers={"User-Agent": "InsurTechIntelligence/1.0"})
            resp.raise_for_status()
            content = resp.content
    except Exception as e:
        logger.warning(f"Failed to fetch {rss_url}: {e}")
        return []

    feed = feedparser.parse(content)
    if feed.bozo and not feed.entries:
        logger.warning(f"Bozo feed: {rss_url}")
        return []

    articles: list[RawArticle] = []
    for entry in feed.entries[:50]:  # max 50 entries per fetch
        url = getattr(entry, "link", None)
        title = getattr(entry, "title", None)
        if not url or not title:
            continue

        articles.append(
            RawArticle(
                title=title.strip(),
                url=url.strip(),
                content_raw=_extract_content(entry),
                image_url=_extract_image(entry),
                author=getattr(entry, "author", None),
                published_at=_parse_date(entry),
                source_id=source_id,
            )
        )

    logger.info(f"Fetched {len(articles)} articles from {rss_url}")
    return articles
