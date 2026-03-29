"""
InsurTech Intelligence — RSS ingestion → GitHub Pages.
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
from generate_site import generate_site

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# OpenAI is optional — skip gracefully if key not set
_openai_client = None
_OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
if _OPENAI_KEY:
    try:
        from openai import OpenAI as _OpenAI
        _openai_client = _OpenAI(api_key=_OPENAI_KEY)
        log.info("OpenAI client initialized")
    except Exception as e:
        log.warning(f"OpenAI unavailable: {e}")

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
    {"name": "INESE",                        "rss": "https://www.inese.es/feed/",                                         "lang": "spanish"},
    {"name": "Actualidad Aseguradora",       "rss": "https://www.actualidadaseguradora.com/feed/",                        "lang": "spanish"},
    {"name": "Aseguranza",                   "rss": "https://www.aseguranza.com/feed/",                                   "lang": "spanish"},
    {"name": "El Economista Seguros",        "rss": "https://www.eleconomista.es/rss/rss-seguros.php",                   "lang": "spanish"},
    {"name": "Fintech.es",                   "rss": "https://fintech.es/feed/",                                           "lang": "spanish"},
    {"name": "iupana (Latam Fintech)",       "rss": "https://iupana.com/feed/",                                           "lang": "spanish"},
    {"name": "Fitch Ratings Insurance",      "rss": "https://www.fitchratings.com/rss/filter?sectorCode=Insurance"},
    {"name": "Latin Insurance",              "rss": "https://latininsurance.com/feed/",                                   "lang": "spanish"},
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


def _extract_image(entry) -> str:
    """Extract best image URL from a feed entry."""
    for thumb in entry.get("media_thumbnail", []):
        if thumb.get("url"):
            return thumb["url"]
    for mc in entry.get("media_content", []):
        if "image" in mc.get("type", "") or mc.get("medium") == "image":
            if mc.get("url"):
                return mc["url"]
    for enc in entry.get("enclosures", []):
        if "image" in enc.get("type", ""):
            if enc.get("href"):
                return enc["href"]
    return ""


_BOILERPLATE = re.compile(
    r'(continue reading|read more|click here|subscribe|the post .{0,80} appeared first on'
    r'|this article (originally )?appeared|view full post|full story|related articles?'
    r'|\[…\]|\[\.{3}\]|&hellip;|&#8230;|\.\.\.\s*$)',
    re.IGNORECASE,
)


def _best_content(entry) -> str:
    """Return the richest text content from a feed entry, cleaned of boilerplate."""
    candidates = []
    # content:encoded is usually the fullest version
    for block in entry.get("content", []):
        val = block.get("value", "")
        if val:
            candidates.append(val)
    # summary / description as fallback
    if entry.get("summary"):
        candidates.append(entry["summary"])
    # pick longest
    raw = max(candidates, key=len) if candidates else ""
    # strip HTML
    raw = re.sub(r'<[^>]+>', ' ', raw)
    raw = re.sub(r'\s+', ' ', raw).strip()
    # remove boilerplate sentences
    sentences = re.split(r'(?<=[.!?])\s+', raw)
    clean = [s for s in sentences if s and not _BOILERPLATE.search(s) and len(s) > 20]
    return " ".join(clean)


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
            content = _best_content(entry)
            image_url = _extract_image(entry)
            if title and url:
                results.append({"title": title, "url": url, "content": content, "image_url": image_url})
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


def extractive_summary(text: str, sentences: int = 3, title: str = "", lang: str = "english") -> str:
    """
    Summarize text using LexRank. Boosts sentences containing title keywords.
    Falls back to keyword-ranked first-sentences if text is too short.
    """
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    if not text:
        return ""

    # Title keywords for relevance boosting (stopwords stripped)
    _STOPS = {"the","a","an","of","in","on","to","for","is","are","was","were",
              "and","or","but","with","at","by","from","as","its","it","that",
              "this","be","have","has","had","will","de","la","el","en","los","las",
              "un","una","por","para","con","del","se","que","su","sus"}
    title_words = {w.lower() for w in re.findall(r'\w+', title) if w.lower() not in _STOPS and len(w) > 3}

    try:
        from sumy.parsers.plaintext import PlaintextParser
        from sumy.nlp.tokenizers import Tokenizer
        from sumy.summarizers.lex_rank import LexRankSummarizer

        # Use Spanish tokenizer for Spanish sources when available
        try:
            tokenizer = Tokenizer(lang)
        except Exception:
            tokenizer = Tokenizer("english")

        parser = PlaintextParser.from_string(text, tokenizer)
        summarizer = LexRankSummarizer()
        # Request extra candidates so we can re-rank by title relevance
        n_candidates = min(sentences + 3, max(sentences, len(parser.document.sentences)))
        result = summarizer(parser.document, sentences_count=n_candidates)
        candidates = [str(s) for s in result]

        if title_words:
            def score(s):
                words = {w.lower() for w in re.findall(r'\w+', s)}
                return len(words & title_words)
            candidates.sort(key=score, reverse=True)

        summary = " ".join(candidates[:sentences]).strip()
        if summary:
            return summary
    except Exception as e:
        log.debug(f"LexRank error: {e}")

    # Fallback: pick sentences that overlap most with title keywords
    parts = [p.strip() for p in re.split(r'(?<=[.!?])\s+', text) if len(p.strip()) > 40]
    if title_words:
        def fallback_score(s):
            words = {w.lower() for w in re.findall(r'\w+', s)}
            return len(words & title_words)
        parts.sort(key=fallback_score, reverse=True)
    return " ".join(parts[:sentences])


def summarize(title: str, content: str) -> dict:
    """Call OpenAI if available; otherwise return empty so extractive fallback kicks in."""
    if not _openai_client:
        return {"title_es": title, "summary_es": None, "category": "General"}
    try:
        resp = _openai_client.chat.completions.create(
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


def _title_key(title: str) -> str:
    """Normalize title for deduplication: first 50 chars, lowercase, no punctuation."""
    return re.sub(r'[^a-z0-9 ]', '', title.lower())[:50].strip()


def main():
    log.info("=== InsurTech ingestion started ===")
    articles = load_articles()
    existing_urls = {a["url"] for a in articles}
    existing_title_keys = {_title_key(a.get("title_original", a["title"])) for a in articles}
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
            tkey = _title_key(item["title"])
            if tkey in existing_title_keys:
                log.info(f"  Duplicate title skipped: {item['title'][:60]}")
                continue
            lang = source.get("lang", "english")
            translated = summarize(item["title"], item["content"])
            summary = translated["summary_es"]
            if not summary:
                full_text = fetch_article_text(item["url"]) or item["content"]
                summary = extractive_summary(full_text, title=item["title"], lang=lang)
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
                "image_url": item.get("image_url", ""),
            }
            articles.insert(0, article)
            existing_urls.add(item["url"])
            existing_title_keys.add(tkey)
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
