"""
Backfill summaries for articles that have none.
Re-fetches RSS feeds to recover content, then applies extractive summary.
Run once from GitHub Actions after ingestion.
"""
import json, re, logging
import feedparser

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger(__name__)

ARTICLES_FILE = "articles.json"

SOURCES = [
    {"name": "InsurTech Magazine",            "rss": "https://www.insurtechmagazine.com/rss"},
    {"name": "Coverager",                     "rss": "https://coverager.com/feed/"},
    {"name": "Insurance Thought Leadership",  "rss": "https://insurancethoughtleadership.com/feed/"},
    {"name": "Digital Insurance",             "rss": "https://www.dig-in.com/rss/news"},
    {"name": "InsurTech Insights",            "rss": "https://insurtechinsights.com/feed/"},
    {"name": "The Insurer",                   "rss": "https://www.theinsurer.com/feed/"},
    {"name": "Insurance Journal",             "rss": "https://www.insurancejournal.com/rss/news/"},
    {"name": "PropertyCasualty360",           "rss": "https://www.propertycasualty360.com/rss/"},
    {"name": "Reinsurance News",              "rss": "https://www.reinsurancene.ws/feed/"},
    {"name": "Artemis",                       "rss": "https://www.artemis.bm/feed/"},
    {"name": "Insurance Age",                 "rss": "https://www.insuranceage.co.uk/rss.xml"},
    {"name": "Insurance Business",            "rss": "https://www.insurancebusinessmag.com/rss/all-news"},
    {"name": "TechCrunch Insurance",          "rss": "https://techcrunch.com/tag/insurance/feed/"},
    {"name": "Crunchbase News",               "rss": "https://news.crunchbase.com/feed/"},
    {"name": "Fintech Futures",               "rss": "https://www.fintechfutures.com/feed/"},
    {"name": "PYMNTS Insurance",              "rss": "https://www.pymnts.com/category/insurance/feed/"},
    {"name": "Reuters Finance",               "rss": "https://feeds.reuters.com/reuters/financialsNews"},
    {"name": "Business Insurance",            "rss": "https://www.businessinsurance.com/rss/news.xml"},
    {"name": "EIOPA",                         "rss": "https://www.eiopa.europa.eu/media/news_en.rss"},
    {"name": "FCA News",                      "rss": "https://www.fca.org.uk/news/rss.xml"},
    {"name": "FSB",                           "rss": "https://www.fsb.org/feed/"},
    {"name": "Swiss Re Institute",            "rss": "https://www.swissre.com/institute/research/rss.xml"},
    {"name": "Lloyd's of London",             "rss": "https://www.lloyds.com/rss/news"},
    {"name": "Fintech News Singapore",        "rss": "https://fintechnews.sg/category/insurtech/feed/"},
    {"name": "Insurance Asia News",           "rss": "https://insuranceasianews.com/feed/"},
    {"name": "InsTech London",                "rss": "https://www.instech.london/news?format=rss"},
    {"name": "Fintech Africa",                "rss": "https://fintechafrica.net/feed/"},
    {"name": "Carrier Management",            "rss": "https://www.carriermanagement.com/rss/"},
    {"name": "Claims Journal",                "rss": "https://www.claimsjournal.com/rss/"},
    {"name": "Insurance Innovation Reporter", "rss": "https://iireporter.com/feed/"},
    {"name": "Embedded Insurance News",       "rss": "https://embedded-insurance.news/feed/"},
    {"name": "Parametric Insurance Review",   "rss": "https://www.parametricinsurancereview.com/feed/"},
    {"name": "INESE",                         "rss": "https://www.inese.es/feed/"},
    {"name": "Actualidad Aseguradora",        "rss": "https://www.actualidadaseguradora.com/feed/"},
    {"name": "Aseguranza",                    "rss": "https://www.aseguranza.com/feed/"},
    {"name": "El Economista Seguros",         "rss": "https://www.eleconomista.es/rss/rss-seguros.php"},
    {"name": "Fintech.es",                    "rss": "https://fintech.es/feed/"},
    {"name": "iupana (Latam Fintech)",        "rss": "https://iupana.com/feed/"},
    {"name": "Latin Insurance",               "rss": "https://latininsurance.com/feed/"},
]


def clean(text: str) -> str:
    text = re.sub(r'<[^>]+>', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def extractive_summary(text: str, sentences: int = 3) -> str:
    if not text:
        return ""
    parts = re.split(r'(?<=[.!?])\s+', text)
    result = []
    for part in parts:
        part = part.strip()
        if len(part) > 40:
            result.append(part)
        if len(result) >= sentences:
            break
    return " ".join(result)


def main():
    with open(ARTICLES_FILE) as f:
        articles = json.load(f)

    # Index articles without summary by URL
    need_summary = {a["url"]: a for a in articles if not a.get("summary")}
    log.info(f"Articles needing summary: {len(need_summary)}")
    if not need_summary:
        log.info("Nothing to do.")
        return

    updated = 0
    for source in SOURCES:
        if not need_summary:
            break
        try:
            feed = feedparser.parse(source["rss"])
            for entry in feed.entries:
                url = entry.get("link", "")
                if url not in need_summary:
                    continue
                raw = (
                    entry.get("summary", "")
                    or (entry.get("content") or [{}])[0].get("value", "")
                )
                summary = extractive_summary(clean(raw))
                if summary:
                    need_summary[url]["summary"] = summary
                    del need_summary[url]
                    updated += 1
                    log.info(f"  OK [{source['name']}] {entry.get('title','')[:50]}")
        except Exception as e:
            log.warning(f"Feed error [{source['name']}]: {e}")

    with open(ARTICLES_FILE, "w") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)

    log.info(f"Backfill complete: {updated} summaries added, {len(need_summary)} still missing")


if __name__ == "__main__":
    main()
