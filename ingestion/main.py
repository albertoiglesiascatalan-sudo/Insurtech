"""
InsurTech Intelligence — RSS ingestion → OpenAI summary → GitHub Pages.
Runs every 6 hours via GitHub Actions.
"""
import os
import json
import re
import logging
import feedparser
import httpx
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
from slugify import slugify
from openai import OpenAI
from generate_site import generate_site

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
openai = OpenAI(api_key=OPENAI_API_KEY)

ARTICLES_FILE = os.path.join(os.path.dirname(__file__), "articles.json")

MAX_PER_SOURCE = 3
MAX_NEW_PER_RUN = 20
KEEP_ARTICLES = 500   # max articles stored

SOURCES = [
    # ── Global ──────────────────────────────────────────────────────────────
    {"name": "InsurTech Magazine",           "rss": "https://www.insurtechmagazine.com/rss"},
    {"name": "Coverager",                    "rss": "https://coverager.com/feed/"},
    {"name": "Insurance Thought Leadership", "rss": "https://insurancethoughtleadership.com/feed/"},
    {"name": "Digital Insurance",            "rss": "https://www.dig-in.com/rss/news"},
    {"name": "InsurTech Insights",           "rss": "https://insurtechinsights.com/feed/"},
    {"name": "The Insurer",                  "rss": "https://www.theinsurer.com/feed/"},
    {"name": "Insurance Journal",            "rss": "https://www.insurancejournal.com/rss/news/"},
    {"name": "PropertyCasualty360",          "rss": "https://www.propertycasualty360.com/rss/"},
    {"name": "Reinsurance News",             "rss": "https://www.reinsurancene.ws/feed/"},
    {"name": "Artemis",                      "rss": "https://www.artemis.bm/feed/"},
    {"name": "Insurance Age",                "rss": "https://www.insuranceage.co.uk/rss.xml"},
    {"name": "Insurance Business",           "rss": "https://www.insurancebusinessmag.com/rss/all-news"},
    {"name": "TechCrunch Insurance",         "rss": "https://techcrunch.com/tag/insurance/feed/"},
    {"name": "Crunchbase News",              "rss": "https://news.crunchbase.com/feed/"},
    {"name": "Fintech Futures",              "rss": "https://www.fintechfutures.com/feed/"},
    {"name": "PYMNTS Insurance",             "rss": "https://www.pymnts.com/category/insurance/feed/"},
    {"name": "Reuters Finance",              "rss": "https://feeds.reuters.com/reuters/financialsNews"},
    {"name": "Business Insurance",           "rss": "https://www.businessinsurance.com/rss/news.xml"},
    {"name": "EIOPA",                        "rss": "https://www.eiopa.europa.eu/media/news_en.rss"},
    {"name": "FCA News",                     "rss": "https://www.fca.org.uk/news/rss.xml"},
    {"name": "FSB",                          "rss": "https://www.fsb.org/feed/"},
    {"name": "Swiss Re Institute",           "rss": "https://www.swissre.com/institute/research/rss.xml"},
    {"name": "Lloyd's of London",            "rss": "https://www.lloyds.com/rss/news"},
    {"name": "Fintech News Singapore",       "rss": "https://fintechnews.sg/category/insurtech/feed/"},
    {"name": "Insurance Asia News",          "rss": "https://insuranceasianews.com/feed/"},
    {"name": "InsTech London",               "rss": "https://www.instech.london/news?format=rss"},
    {"name": "Fintech Africa",               "rss": "https://fintechafrica.net/feed/"},
    {"name": "Carrier Management",           "rss": "https://www.carriermanagement.com/rss/"},
    {"name": "Claims Journal",               "rss": "https://www.claimsjournal.com/rss/"},
    {"name": "Insurance Innovation Reporter","rss": "https://iireporter.com/feed/"},
    {"name": "Embedded Insurance News",      "rss": "https://embedded-insurance.news/feed/"},
    {"name": "Parametric Insurance Review",  "rss": "https://www.parametricinsurancereview.com/feed/"},
    # ── España & Iberoamérica ────────────────────────────────────────────────
    {"name": "INESE",                        "rss": "https://www.inese.es/feed/"},
    {"name": "Actualidad Aseguradora",       "rss": "https://www.actualidadaseguradora.com/feed/"},
    {"name": "Aseguranza",                   "rss": "https://www.aseguranza.com/feed/"},
    {"name": "El Economista Seguros",        "rss": "https://www.eleconomista.es/rss/rss-seguros.php"},
    {"name": "Fintech.es",                   "rss": "https://fintech.es/feed/"},
    {"name": "iupana (Latam Fintech)",       "rss": "https://iupana.com/feed/"},
    {"name": "Fitch Ratings Insurance",      "rss": "https://www.fitchratings.com/rss/filter?sectorCode=Insurance"},
    {"name": "Latin Insurance",              "rss": "https://latininsurance.com/feed/"},
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


def fetch_article_text(url: str) -> str:
    """Fetch full article and extract main text."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; InsurTechBot/1.0)"}
        r = httpx.get(url, headers=headers, timeout=8, follow_redirects=True)
        if r.status_code != 200:
            return ""
        soup = BeautifulSoup(r.text, "lxml")
        # Remove noise
        for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form", "figure"]):
            tag.decompose()
        # Try article/main first, fallback to body
        container = soup.find("article") or soup.find("main") or soup.find("body")
        if not container:
            return ""
        paragraphs = [p.get_text(" ", strip=True) for p in container.find_all("p")]
        # Keep only meaningful paragraphs (>40 chars)
        paragraphs = [p for p in paragraphs if len(p) > 40]
        return " ".join(paragraphs[:10])
    except Exception as e:
        log.debug(f"fetch_article_text error [{url[:60]}]: {e}")
        return ""


def extractive_summary(text: str, sentences: int = 3) -> str:
    """
    Summarize text by selecting the most representative sentences (LexRank).
    Falls back to first-sentences if text is too short.
    Strips HTML first.
    """
    if not text:
        return ""
    # Strip HTML
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    if not text:
        return ""

    try:
        from sumy.parsers.plaintext import PlaintextParser
        from sumy.nlp.tokenizers import Tokenizer
        from sumy.summarizers.lex_rank import LexRankSummarizer

        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LexRankSummarizer()
        result = summarizer(parser.document, sentences_count=sentences)
        summary = " ".join(str(s) for s in result).strip()
        if summary:
            return summary
    except Exception as e:
        log.debug(f"LexRank error: {e}")

    # Fallback: first meaningful sentences
    parts = re.split(r'(?<=[.!?])\s+', text)
    result = []
    for part in parts:
        if len(part.strip()) > 40:
            result.append(part.strip())
        if len(result) >= sentences:
            break
    return " ".join(result)


def summarize(title: str, content: str) -> dict:
    try:
        resp = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": (
                "Eres un analista de insurtech. Traduce el título al español, resume el artículo "
                "en 2-3 frases en español para profesionales del seguro, y clasifícalo en UNA de estas categorías:\n"
                "Tecnología, Regulación, Inversión, Vida y Salud, Automóvil, Catástrofes, Fraude, Embebido, General\n\n"
                "Sé conciso y objetivo. Responde SOLO con JSON válido con este formato:\n"
                '{"title_es": "...", "summary_es": "...", "category": "..."}\n\n'
                f"Title: {title}\n\nContent: {content[:2000]}"
            )}],
            max_tokens=250,
            temperature=0.3,
        )
        import json as _json
        data = _json.loads(resp.choices[0].message.content.strip())
        return {
            "title_es": data.get("title_es", title),
            "summary_es": data.get("summary_es", ""),
            "category": data.get("category", "General"),
        }
    except Exception as e:
        log.warning(f"OpenAI error: {e}")
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
            # If OpenAI didn't produce a summary, use RSS content directly
            summary = translated["summary_es"]
            if not summary:
                # Try scraping the article, fallback to RSS content
                full_text = fetch_article_text(item["url"]) or item["content"]
                summary = extractive_summary(full_text)
                if summary:
                    log.info(f"  Extractive summary used for: {item['title'][:50]}")
            article = {
                "id": slugify(item["title"])[:80],
                "title": translated["title_es"],
                "title_original": item["title"],
                "url": item["url"],
                "summary": summary,
                "category": translated["category"],
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
