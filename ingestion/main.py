"""
InsurTech Intelligence — RSS ingestion → OpenAI summary → GitHub Pages.
Runs every 6 hours via GitHub Actions.
"""
import os
import json
import logging
import feedparser
from datetime import datetime, timezone, timedelta
from slugify import slugify
import anthropic
from generate_site import generate_site

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

ARTICLES_FILE = os.path.join(os.path.dirname(__file__), "articles.json")

MAX_PER_SOURCE = 3
MAX_NEW_PER_RUN = 20
KEEP_ARTICLES = 500   # max articles stored

SOURCES = [
    # ── InsurTech especializado ──────────────────────────────────────────────────
    {"name": "InsurTech Magazine",           "rss": "https://www.insurtechmagazine.com/rss"},
    {"name": "Coverager",                    "rss": "https://coverager.com/feed/"},
    {"name": "Insurance Thought Leadership", "rss": "https://insurancethoughtleadership.com/feed/"},
    {"name": "Digital Insurance",            "rss": "https://www.dig-in.com/rss/news"},
    {"name": "InsurTech Insights",           "rss": "https://insurtechinsights.com/feed/"},
    {"name": "Insurance Innovation Reporter","rss": "https://iireporter.com/feed/"},
    {"name": "Embedded Insurance News",      "rss": "https://embedded-insurance.news/feed/"},
    {"name": "Parametric Insurance Review",  "rss": "https://www.parametricinsurancereview.com/feed/"},
    # ── Prensa aseguradora global ────────────────────────────────────────────────
    {"name": "The Insurer",                  "rss": "https://www.theinsurer.com/feed/"},
    {"name": "Insurance Journal",            "rss": "https://www.insurancejournal.com/rss/news/"},
    {"name": "Insurance Business",           "rss": "https://www.insurancebusinessmag.com/rss/all-news"},
    {"name": "Business Insurance",           "rss": "https://www.businessinsurance.com/rss/news.xml"},
    {"name": "Carrier Management",           "rss": "https://www.carriermanagement.com/rss/"},
    {"name": "Claims Journal",               "rss": "https://www.claimsjournal.com/rss/"},
    {"name": "PropertyCasualty360",          "rss": "https://www.propertycasualty360.com/rss/"},
    # ── Reaseguro & mercados de capital ─────────────────────────────────────────
    {"name": "Reinsurance News",             "rss": "https://www.reinsurancene.ws/feed/"},
    {"name": "Artemis",                      "rss": "https://www.artemis.bm/feed/"},
    {"name": "Reactions Magazine",           "rss": "https://www.reactionsnet.com/rss"},
    {"name": "Global Reinsurance",           "rss": "https://www.globalreinsurance.com/rss/news"},
    {"name": "Swiss Re Institute",           "rss": "https://www.swissre.com/institute/research/rss.xml"},
    # ── Europa — mercado & innovación ───────────────────────────────────────────
    {"name": "InsTech London",               "rss": "https://www.instech.london/news?format=rss"},
    {"name": "Insurance Age",                "rss": "https://www.insuranceage.co.uk/rss.xml"},
    {"name": "Insurance Post",               "rss": "https://www.postonline.co.uk/rss.xml"},
    {"name": "Intelligent Insurer",          "rss": "https://www.intelligentinsurer.com/rss/news"},
    {"name": "Lloyd's of London",            "rss": "https://www.lloyds.com/rss/news"},
    {"name": "The Geneva Association",       "rss": "https://www.genevaassociation.org/rss"},
    # ── Europa — reguladores ─────────────────────────────────────────────────────
    {"name": "EIOPA",                        "rss": "https://www.eiopa.europa.eu/media/news_en.rss"},
    {"name": "FCA News",                     "rss": "https://www.fca.org.uk/news/rss.xml"},
    {"name": "BaFin",                        "rss": "https://www.bafin.de/SiteGlobals/Functions/RSS/EN/Feed/RSSNewsfeed_Veroeffentlichungen.html"},
    {"name": "ACPR France",                  "rss": "https://acpr.banque-france.fr/en/rss.xml"},
    {"name": "Insurance Europe",             "rss": "https://www.insuranceeurope.eu/news/rss"},
    # ── España & Iberoamérica ────────────────────────────────────────────────────
    {"name": "INESE",                        "rss": "https://www.inese.es/feed/",                        "lang": "spanish"},
    {"name": "Actualidad Aseguradora",       "rss": "https://www.actualidadaseguradora.com/feed/",        "lang": "spanish"},
    {"name": "Aseguranza",                   "rss": "https://www.aseguranza.com/feed/",                   "lang": "spanish"},
    {"name": "El Economista Seguros",        "rss": "https://www.eleconomista.es/rss/rss-seguros.php",    "lang": "spanish"},
    {"name": "Latin Insurance",              "rss": "https://latininsurance.com/feed/",                   "lang": "spanish"},
    {"name": "Fitch Ratings Insurance",      "rss": "https://www.fitchratings.com/rss/filter?sectorCode=Insurance"},
    {"name": "Insurance Asia News",          "rss": "https://insuranceasianews.com/feed/"},
]


def load_articles() -> list:
    try:
        with open(ARTICLES_FILE) as f:
            return json.load(f)
    except Exception:
        return []


def save_articles(articles: list):
    with open(ARTICLES_FILE, "w") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)


def fetch_recent(source: dict, since_hours: int = 7) -> list:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)
    results = []
    try:
        feed = feedparser.parse(source["rss"])
        for entry in feed.entries[:10]:
            parsed = entry.get("published_parsed") or entry.get("updated_parsed")
            if parsed:
                pub_dt = datetime(*parsed[:6], tzinfo=timezone.utc)
                if pub_dt < cutoff:
                    continue
            title = entry.get("title", "").strip()
            url = entry.get("link", "")
            content = (
                entry.get("summary", "")
                or (entry.get("content") or [{}])[0].get("value", "")
            )
            if title and url:
                results.append({"title": title, "url": url, "content": content})
            if len(results) >= MAX_PER_SOURCE:
                break
    except Exception as e:
        log.warning(f"Feed error [{source['name']}]: {e}")
    return results


def summarize(title: str, content: str) -> dict:
    try:
        resp = claude.messages.create(
            model="claude-haiku-4-5",
            max_tokens=350,
            messages=[{"role": "user", "content": (
                "Eres un analista de insurtech. Traduce el título al español, resume el artículo "
                "en 2-3 frases en español para profesionales del seguro, y clasifícalo en UNA de estas categorías:\n"
                "Tecnología, Regulación, Inversión, Vida y Salud, Automóvil, Catástrofes, Fraude, Embebido, General\n\n"
                "Sé conciso y objetivo. Responde SOLO con JSON válido con este formato:\n"
                '{"title_es": "...", "summary_es": "...", "category": "..."}\n\n'
                f"Title: {title}\n\nContent: {content[:2000]}"
            )}],
        )
        import json as _json
        data = _json.loads(resp.content[0].text.strip())
        return {
            "title_es": data.get("title_es", title),
            "summary_es": data.get("summary_es", ""),
            "category": data.get("category", "General"),
        }
    except Exception as e:
        log.warning(f"Claude API error: {e}")
        return {"title_es": title, "summary_es": None, "category": "General"}


def main():
    log.info("=== InsurTech ingestion started ===")
    articles = load_articles()
    existing_urls = {a["url"] for a in articles}
    new_count = 0

    for source in SOURCES:
        if new_count >= MAX_NEW_PER_RUN:
            break
        log.info(f"Fetching: {source['name']}")
        items = fetch_recent(source)
        for item in items:
            if new_count >= MAX_NEW_PER_RUN:
                break
            if item["url"] in existing_urls:
                continue
            translated = summarize(item["title"], item["content"])
            article = {
                "id": slugify(item["title"])[:80],
                "title": translated["title_es"],
                "title_original": item["title"],
                "url": item["url"],
                "summary": translated["summary_es"],
                "source": source["name"],
                "published_at": datetime.now(timezone.utc).isoformat(),
            }
            articles.insert(0, article)
            existing_urls.add(item["url"])
            new_count += 1
            log.info(f"  + {item['title'][:70]}")

    # Keep only the latest KEEP_ARTICLES
    articles = articles[:KEEP_ARTICLES]
    save_articles(articles)
    log.info(f"Saved {len(articles)} total articles ({new_count} new)")

    generate_site(articles)
    log.info("=== Site generated ===")


if __name__ == "__main__":
    main()
