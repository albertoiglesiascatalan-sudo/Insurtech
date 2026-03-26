"""Web scraper for sources without RSS feeds."""
import logging
from datetime import datetime, timezone
from typing import TypedDict

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; InsurTechIntelligenceBot/1.0; "
        "+https://insurtech.news/bot)"
    )
}


class ScrapedArticle(TypedDict):
    title: str
    url: str
    content_raw: str | None
    image_url: str | None
    author: str | None
    published_at: datetime | None
    source_id: int


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=3, max=15))
async def scrape_article_list(base_url: str, source_id: int, selectors: dict) -> list[ScrapedArticle]:
    """
    Generic article list scraper.
    selectors: {
        "article": CSS selector for article containers,
        "title": CSS selector for title (within container),
        "link": CSS selector for link,
        "summary": CSS selector for summary (optional),
        "image": CSS selector for image (optional),
        "date": CSS selector for date (optional),
    }
    """
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(base_url, headers=HEADERS)
            resp.raise_for_status()
    except Exception as e:
        logger.warning(f"Scrape failed for {base_url}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    articles: list[ScrapedArticle] = []

    for container in soup.select(selectors.get("article", "article"))[:30]:
        title_el = container.select_one(selectors.get("title", "h2"))
        link_el = container.select_one(selectors.get("link", "a"))
        if not title_el or not link_el:
            continue

        title = title_el.get_text(strip=True)
        href = link_el.get("href", "")
        if href.startswith("/"):
            from urllib.parse import urlparse
            base = urlparse(base_url)
            href = f"{base.scheme}://{base.netloc}{href}"

        summary_el = container.select_one(selectors.get("summary", "p"))
        image_el = container.select_one(selectors.get("image", "img"))
        image_url = image_el.get("src") or image_el.get("data-src") if image_el else None

        articles.append(
            ScrapedArticle(
                title=title,
                url=href,
                content_raw=summary_el.get_text(strip=True)[:2000] if summary_el else None,
                image_url=image_url,
                author=None,
                published_at=None,
                source_id=source_id,
            )
        )

    logger.info(f"Scraped {len(articles)} articles from {base_url}")
    return articles
