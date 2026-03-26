"""
InsurTech Intelligence — RSS ingestion → OpenAI summary → Ghost post.
Runs every 6 hours via GitHub Actions.
"""
import os
import time
import hashlib
import logging
import jwt
import httpx
import feedparser
from datetime import datetime, timezone, timedelta
from slugify import slugify
from openai import OpenAI

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
GHOST_URL = os.environ["GHOST_URL"].rstrip("/")
GHOST_ADMIN_API_KEY = os.environ["GHOST_ADMIN_API_KEY"]

openai = OpenAI(api_key=OPENAI_API_KEY)

# ── RSS sources (only those with rss_url) ────────────────────────────────────
SOURCES = [
    {"name": "InsurTech Magazine",          "rss": "https://www.insurtechmagazine.com/rss"},
    {"name": "Coverager",                   "rss": "https://coverager.com/feed/"},
    {"name": "Insurance Thought Leadership","rss": "https://insurancethoughtleadership.com/feed/"},
    {"name": "Digital Insurance",           "rss": "https://www.dig-in.com/rss/news"},
    {"name": "InsurTech Insights",          "rss": "https://insurtechinsights.com/feed/"},
    {"name": "The Insurer",                 "rss": "https://www.theinsurer.com/feed/"},
    {"name": "Insurance Journal",           "rss": "https://www.insurancejournal.com/rss/news/"},
    {"name": "PropertyCasualty360",         "rss": "https://www.propertycasualty360.com/rss/"},
    {"name": "Reinsurance News",            "rss": "https://www.reinsurancene.ws/feed/"},
    {"name": "Artemis",                     "rss": "https://www.artemis.bm/feed/"},
    {"name": "Insurance Age",               "rss": "https://www.insuranceage.co.uk/rss.xml"},
    {"name": "Post Online",                 "rss": "https://www.postonline.co.uk/rss.xml"},
    {"name": "Insurance Business",          "rss": "https://www.insurancebusinessmag.com/rss/all-news"},
    {"name": "TechCrunch Insurance",        "rss": "https://techcrunch.com/tag/insurance/feed/"},
    {"name": "Crunchbase News",             "rss": "https://news.crunchbase.com/feed/"},
    {"name": "Fintech Futures",             "rss": "https://www.fintechfutures.com/feed/"},
    {"name": "PYMNTS Insurance",            "rss": "https://www.pymnts.com/category/insurance/feed/"},
    {"name": "Fintech Magazine",            "rss": "https://fintechmagazine.com/rss"},
    {"name": "Reuters Finance",             "rss": "https://feeds.reuters.com/reuters/financialsNews"},
    {"name": "Business Insurance",          "rss": "https://www.businessinsurance.com/rss/news.xml"},
    {"name": "EIOPA",                       "rss": "https://www.eiopa.europa.eu/media/news_en.rss"},
    {"name": "FCA News",                    "rss": "https://www.fca.org.uk/news/rss.xml"},
    {"name": "FSB",                         "rss": "https://www.fsb.org/feed/"},
    {"name": "PRA News",                    "rss": "https://www.bankofengland.co.uk/rss/news"},
    {"name": "Swiss Re Institute",          "rss": "https://www.swissre.com/institute/research/rss.xml"},
    {"name": "Lloyd's of London",           "rss": "https://www.lloyds.com/rss/news"},
    {"name": "Fintech News Singapore",      "rss": "https://fintechnews.sg/category/insurtech/feed/"},
    {"name": "Fintech News Hong Kong",      "rss": "https://fintechnews.hk/feed/"},
    {"name": "Insurance Asia News",         "rss": "https://insuranceasianews.com/feed/"},
    {"name": "Fintech News India",          "rss": "https://inc42.com/tag/insurtech/feed/"},
    {"name": "InsurTech Hub Munich",        "rss": "https://www.insurtechhub.com/feed/"},
    {"name": "InsTech London",              "rss": "https://www.instech.london/news?format=rss"},
    {"name": "Sifted",                      "rss": "https://sifted.eu/rss"},
    {"name": "Finnovista",                  "rss": "https://www.finnovista.com/feed/"},
    {"name": "Fintech Africa",              "rss": "https://fintechafrica.net/feed/"},
    {"name": "Dark Reading",                "rss": "https://www.darkreading.com/rss.xml"},
    {"name": "Carrier Management",          "rss": "https://www.carriermanagement.com/rss/"},
    {"name": "Claims Journal",              "rss": "https://www.claimsjournal.com/rss/"},
    {"name": "Insurance Innovation Reporter","rss": "https://iireporter.com/feed/"},
    {"name": "Embedded Insurance News",     "rss": "https://embedded-insurance.news/feed/"},
    {"name": "Parametric Insurance Review", "rss": "https://www.parametricinsurancereview.com/feed/"},
]

MAX_ARTICLES_PER_SOURCE = 3   # max new articles per source per run
MAX_TOTAL_ARTICLES = 20       # cap to avoid OpenAI costs


# ── Ghost helpers ─────────────────────────────────────────────────────────────

def _ghost_token() -> str:
    """Generate a short-lived JWT for Ghost Admin API."""
    key_id, secret = GHOST_ADMIN_API_KEY.split(":")
    payload = {
        "iat": int(time.time()),
        "exp": int(time.time()) + 300,
        "aud": "/admin/",
    }
    return jwt.encode(payload, bytes.fromhex(secret), algorithm="HS256",
                      headers={"kid": key_id})


def ghost_get_existing_slugs() -> set[str]:
    """Return slugs of posts already in Ghost (last 500)."""
    headers = {"Authorization": f"Ghost {_ghost_token()}"}
    try:
        r = httpx.get(
            f"{GHOST_URL}/ghost/api/admin/posts/",
            params={"limit": 500, "fields": "slug"},
            headers=headers,
            timeout=15,
        )
        r.raise_for_status()
        return {p["slug"] for p in r.json().get("posts", [])}
    except Exception as e:
        log.warning(f"Could not fetch existing slugs: {e}")
        return set()


def ghost_create_post(title: str, html: str, source_name: str, original_url: str) -> bool:
    """Create a Ghost post. Returns True on success."""
    slug = slugify(title)[:90]
    headers = {
        "Authorization": f"Ghost {_ghost_token()}",
        "Content-Type": "application/json",
    }
    body = {
        "posts": [{
            "title": title,
            "slug": slug,
            "html": html,
            "status": "published",
            "tags": [{"name": "insurtech"}, {"name": source_name}],
            "custom_excerpt": html[:150].replace("<p>", "").replace("</p>", ""),
        }]
    }
    try:
        r = httpx.post(
            f"{GHOST_URL}/ghost/api/admin/posts/",
            json=body,
            headers=headers,
            timeout=15,
        )
        r.raise_for_status()
        log.info(f"  ✓ Published: {title[:70]}")
        return True
    except Exception as e:
        log.warning(f"  ✗ Ghost error for '{title[:50]}': {e}")
        return False


# ── OpenAI helpers ────────────────────────────────────────────────────────────

def summarize(title: str, content: str) -> str:
    """Return a 3-sentence HTML summary of the article."""
    prompt = (
        "You are an insurtech analyst. Summarize this article in exactly 3 sentences "
        "for insurance professionals. Be concise and factual. Return plain text only.\n\n"
        f"Title: {title}\n\nContent: {content[:3000]}"
    )
    try:
        resp = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.3,
        )
        summary = resp.choices[0].message.content.strip()
        return f"<p>{summary}</p><p><a href='{{}}'  target='_blank'>Read full article →</a></p>"
    except Exception as e:
        log.warning(f"OpenAI error: {e}")
        return f"<p>{title}</p>"


# ── RSS fetching ──────────────────────────────────────────────────────────────

def fetch_recent_articles(source: dict, since_hours: int = 7) -> list[dict]:
    """Fetch articles published in the last `since_hours` hours."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)
    articles = []
    try:
        feed = feedparser.parse(source["rss"])
        for entry in feed.entries[:10]:
            published = entry.get("published_parsed") or entry.get("updated_parsed")
            if published:
                pub_dt = datetime(*published[:6], tzinfo=timezone.utc)
                if pub_dt < cutoff:
                    continue
            title = entry.get("title", "").strip()
            url = entry.get("link", "")
            content = (
                entry.get("summary", "")
                or entry.get("content", [{}])[0].get("value", "")
            )
            if title and url:
                articles.append({"title": title, "url": url, "content": content})
            if len(articles) >= MAX_ARTICLES_PER_SOURCE:
                break
    except Exception as e:
        log.warning(f"Feed error [{source['name']}]: {e}")
    return articles


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    log.info("=== InsurTech ingestion started ===")
    existing_slugs = ghost_get_existing_slugs()
    log.info(f"Ghost has {len(existing_slugs)} existing posts")

    total_published = 0

    for source in SOURCES:
        if total_published >= MAX_TOTAL_ARTICLES:
            log.info("Reached max articles limit, stopping.")
            break

        log.info(f"Fetching: {source['name']}")
        articles = fetch_recent_articles(source)
        log.info(f"  Found {len(articles)} recent articles")

        for article in articles:
            if total_published >= MAX_TOTAL_ARTICLES:
                break

            slug = slugify(article["title"])[:90]
            if slug in existing_slugs:
                log.info(f"  Skip (exists): {article['title'][:60]}")
                continue

            summary_html = summarize(article["title"], article["content"])
            summary_html = summary_html.replace("{}", article["url"])

            html = (
                f"<p><em>Source: <a href='{article['url']}' target='_blank'>"
                f"{source['name']}</a></em></p>"
                f"{summary_html}"
            )

            if ghost_create_post(article["title"], html, source["name"], article["url"]):
                existing_slugs.add(slug)
                total_published += 1

    log.info(f"=== Done. Published {total_published} new articles ===")


if __name__ == "__main__":
    main()
