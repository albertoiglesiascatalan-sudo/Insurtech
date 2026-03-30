"""
Signal Intelligence Engine — scores articles, extracts deals, detects trends.
Zero external dependencies beyond what's already installed.
"""
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta

# ── Source authority scores ──────────────────────────────────────────────────
SOURCE_AUTHORITY = {
    "EIOPA": 10, "FCA News": 10, "FSB": 9, "Swiss Re Institute": 9,
    "Lloyd's of London": 8, "Fitch Ratings Insurance": 8,
    "The Insurer": 7, "Reinsurance News": 7, "Artemis": 7,
    "Insurance Journal": 6, "Business Insurance": 6,
    "Coverager": 6, "Digital Insurance": 5, "InsurTech Magazine": 5,
    # Ibero — regulatory carries extra weight
    "INESE": 7, "Actualidad Aseguradora": 6, "El Economista Seguros": 6,
    "Aseguranza": 5,
}

# ── Signal keyword groups ─────────────────────────────────────────────────────
SIGNAL_GROUPS = [
    {
        "id": "regulatory",
        "label": "Regulación",
        "icon": "⚖️",
        "weight": 9,
        "why_tpl": "Puede requerir adaptación regulatoria en los próximos meses.",
        "keywords": [
            "regulation", "directive", "consultation", "eiopa", "fca", "solvency",
            "dgsfp", "compliance", "mandatory", "ban", "guideline", "framework",
            "supervisory", "regulación", "directiva", "consulta", "cumplimiento",
            "supervisión", "normativa", "circular", "instrucción",
        ],
    },
    {
        "id": "ma",
        "label": "M&A",
        "icon": "🤝",
        "weight": 8,
        "why_tpl": "Consolida el mercado y puede redefinir la competencia en el sector.",
        "keywords": [
            "acqui", "merger", "takeover", "buys ", "acquires", "acquisition",
            "compra", "fusión", "adquisición", "integración", "absorbe",
            "deal closed", "strategic partnership", "joint venture",
        ],
    },
    {
        "id": "funding",
        "label": "Inversión",
        "icon": "💰",
        "weight": 7,
        "why_tpl": "Nueva financiación que puede acelerar la competencia en el sector.",
        "keywords": [
            "raises", "funding", "series a", "series b", "series c", "series d",
            "seed round", "investment round", "venture", "backed by",
            "millones", "ronda", "financiación", "levanta", "capta",
            "million", "billion", "pre-seed",
        ],
    },
    {
        "id": "disruption",
        "label": "Disrupción",
        "icon": "🚀",
        "weight": 6,
        "why_tpl": "Introduce un modelo o tecnología que puede alterar la cadena de valor.",
        "keywords": [
            "launches", "lanza", "new product", "nuevo producto", "parametric",
            "embedded insurance", "on-demand", "usage-based", "telematics",
            "generative ai", "llm", "autonomous", "real-time underwriting",
            "instant claims", "digital-first", "api-first",
        ],
    },
    {
        "id": "climate",
        "label": "Clima & Catástrofes",
        "icon": "🌪️",
        "weight": 7,
        "why_tpl": "Impacto directo en exposición, pricing y reservas del sector.",
        "keywords": [
            "climate", "catastrophe", "nat cat", "flood", "wildfire", "hurricane",
            "earthquake", "climate risk", "physical risk", "transition risk",
            "catástrofe", "inundación", "incendio forestal", "sequía", "clima",
            "pérdidas aseguradas", "insured losses",
        ],
    },
    {
        "id": "ai_tech",
        "label": "IA & Tecnología",
        "icon": "🤖",
        "weight": 5,
        "why_tpl": "Tecnología con potencial de transformar operaciones o experiencia de cliente.",
        "keywords": [
            "artificial intelligence", "machine learning", "generative ai",
            "large language model", "automation", "digital transformation",
            "insurtech platform", "core system", "legacy replacement",
            "inteligencia artificial", "automatización", "transformación digital",
        ],
    },
    {
        "id": "leadership",
        "label": "Cambio de Liderazgo",
        "icon": "👔",
        "weight": 4,
        "why_tpl": "Los cambios de liderazgo suelen anticipar cambios estratégicos.",
        "keywords": [
            "appoints", "names new", "ceo", "cto", "cdo", "coo", "cfo",
            "nombra", "nuevo director", "nueva directora", "leaves", "joins",
            "chief executive", "chief technology", "chief digital",
        ],
    },
]

# ── Deal extraction ───────────────────────────────────────────────────────────
_AMOUNT_RE = re.compile(
    r'[\$€£]?\s*(\d+(?:[,\.]\d+)?)\s*'
    r'(billion|bn|thousand million|million|mn|millones?|mil millones?)\b',
    re.IGNORECASE,
)
_ROUND_RE = re.compile(
    r'\b(Series [A-F]|Seed|Pre-[Ss]eed|Growth|Pre-IPO|IPO|Bridge|Extension)\b',
)


def extract_deal(title: str, summary: str) -> dict | None:
    # Only extract from the title — more precise, avoids market-size paragraphs
    text = title
    amount_m = None
    amount_str = None
    round_type = None

    m = _AMOUNT_RE.search(text)
    if m:
        num_str = m.group(1).replace(",", ".")
        try:
            num = float(num_str)
        except ValueError:
            num = 0
        unit = m.group(2).lower()
        if any(x in unit for x in ("billion", "bn", "mil millon")):
            num *= 1000
        # Sanity: ignore implausible amounts (< 0.5M or > 20B)
        if num < 0.5 or num > 20_000:
            amount_m = None
        else:
            amount_m = num
            amount_str = f"${int(num)}M" if num >= 1 else f"${num*1000:.0f}K"

    r = _ROUND_RE.search(title + " " + summary[:300])
    if r:
        round_type = r.group(1)

    if amount_m is not None or round_type:
        return {"amount_m": amount_m or 0, "amount_str": amount_str or "—", "round": round_type or "—"}
    return None


# ── Signal scoring ────────────────────────────────────────────────────────────
def score_article(article: dict) -> dict:
    """Enrich article with signal_score, signal_label, signal_icon, is_signal, why_matters, deal."""
    title = (article.get("title", "") + " " + article.get("title_original", "")).lower()
    summary = article.get("summary", "").lower()
    source = article.get("source", "")
    text = title + " " + summary

    score = SOURCE_AUTHORITY.get(source, 2)
    best_group = None
    best_score = 0

    for group in SIGNAL_GROUPS:
        hits = sum(1 for kw in group["keywords"] if kw in text)
        if hits:
            group_score = group["weight"] * min(hits, 3)
            score += group_score
            if group_score > best_score:
                best_score = group_score
                best_group = group

    # Recency boost
    try:
        pub = datetime.fromisoformat(article.get("published_at", ""))
        if pub.tzinfo is None:
            pub = pub.replace(tzinfo=timezone.utc)
        hours = (datetime.now(timezone.utc) - pub).total_seconds() / 3600
        score += max(0, 6 - int(hours / 4))  # up to +6 if < 4h old
    except Exception:
        pass

    article["signal_score"] = score
    article["signal_label"] = best_group["label"] if best_group else ""
    article["signal_icon"] = best_group["icon"] if best_group else ""
    article["why_matters"] = best_group["why_tpl"] if best_group else ""
    article["is_signal"] = score >= 18

    # Deal extraction for Inversión / funding articles
    if article.get("category") == "Inversión" or (best_group and best_group["id"] == "funding"):
        article["deal"] = extract_deal(
            article.get("title_original", article.get("title", "")),
            article.get("summary", ""),
        )
    else:
        article.setdefault("deal", None)

    return article


# ── Trend detection ───────────────────────────────────────────────────────────
_STOP = {
    "the", "a", "an", "of", "in", "on", "to", "for", "is", "are", "was",
    "were", "and", "or", "but", "with", "at", "by", "from", "as", "its",
    "it", "that", "this", "be", "have", "has", "had", "will", "new", "says",
    "de", "la", "el", "en", "los", "las", "un", "una", "por", "para", "con",
    "del", "se", "que", "su", "sus", "al", "sobre", "más", "también",
}

_TREND_TOPICS = {
    "parametric": ["parametric", "paramétrico"],
    "embedded": ["embedded insurance", "seguro embebido", "embedded"],
    "IA & Seguros": ["artificial intelligence", "inteligencia artificial", "ai model", "llm", "generative"],
    "Clima": ["climate", "nat cat", "catastrophe", "catástrofe", "flood", "wildfire", "inundación"],
    "Regulación EIOPA": ["eiopa", "solvency ii", "solvencia ii"],
    "Regulación España": ["dgsfp", "dgs", "dirección general de seguros"],
    "Fraude": ["fraud", "fraude", "anti-fraud", "detection"],
    "Telemática": ["telematics", "telemática", "usage-based", "ubi"],
    "Ciberseguro": ["cyber insurance", "ciberseguro", "cyber risk", "riesgo cibernético"],
    "Salud digital": ["digital health", "salud digital", "healthtech", "wearable"],
}


def detect_trends(articles: list) -> list[dict]:
    """
    Compare topic frequency this week vs previous 4 weeks.
    Returns list of {topic, this_week, prev_avg, change_pct, trend} sorted by change.
    """
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=35)

    this_week_texts = []
    prev_texts = []

    for a in articles:
        try:
            pub = datetime.fromisoformat(a.get("published_at", ""))
            if pub.tzinfo is None:
                pub = pub.replace(tzinfo=timezone.utc)
        except Exception:
            continue
        text = (a.get("title", "") + " " + a.get("summary", "")).lower()
        if pub >= week_ago:
            this_week_texts.append(text)
        elif pub >= month_ago:
            prev_texts.append(text)

    if not this_week_texts:
        return []

    # Normalize prev by time proportion (4x the week period)
    prev_norm = max(len(prev_texts), 1) / 4

    results = []
    for topic, keywords in _TREND_TOPICS.items():
        this_count = sum(1 for t in this_week_texts if any(kw in t for kw in keywords))
        prev_count = sum(1 for t in prev_texts if any(kw in t for kw in keywords)) / prev_norm
        if this_count == 0:
            continue
        if prev_count < 0.5:
            # New topic this week — high signal
            change_pct = 999
        else:
            change_pct = int((this_count - prev_count) / prev_count * 100)
        results.append({
            "topic": topic,
            "this_week": this_count,
            "prev_avg": round(prev_count, 1),
            "change_pct": change_pct,
            "is_new": prev_count < 0.5,
        })

    results.sort(key=lambda x: x["change_pct"], reverse=True)
    return results[:6]


# ── Cross-source amplification ────────────────────────────────────────────────
def _title_tokens(title: str) -> set:
    return {w.lower() for w in re.findall(r'\w{4,}', title) if w.lower() not in _STOP}


def detect_amplified(articles: list, window_days: int = 3, threshold: int = 3) -> set:
    """Return set of article IDs that appear in 3+ sources covering the same topic."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
    recent = []
    for a in articles:
        try:
            pub = datetime.fromisoformat(a.get("published_at", ""))
            if pub.tzinfo is None:
                pub = pub.replace(tzinfo=timezone.utc)
            if pub >= cutoff:
                recent.append(a)
        except Exception:
            pass

    # Group by topic cluster using Jaccard similarity
    clusters: list[list] = []
    for a in recent:
        tokens_a = _title_tokens(a.get("title_original", a.get("title", "")))
        placed = False
        for cluster in clusters:
            rep = cluster[0]
            tokens_rep = _title_tokens(rep.get("title_original", rep.get("title", "")))
            if tokens_a and tokens_rep:
                jaccard = len(tokens_a & tokens_rep) / len(tokens_a | tokens_rep)
                if jaccard >= 0.25:
                    cluster.append(a)
                    placed = True
                    break
        if not placed:
            clusters.append([a])

    amplified_ids = set()
    for cluster in clusters:
        sources = {a.get("source") for a in cluster}
        if len(sources) >= threshold:
            for a in cluster:
                amplified_ids.add(a.get("id", ""))
    return amplified_ids


# ── Incumbent tracker ────────────────────────────────────────────────────────
INCUMBENTS = {
    "Mapfre":           ["mapfre"],
    "Allianz":          ["allianz"],
    "AXA":              ["axa"],
    "Zurich":           ["zurich"],
    "Generali":         ["generali"],
    "Mutua Madrileña":  ["mutua madrileña", "mutua madrilena", "mutua madrile"],
    "Sanitas":          ["sanitas"],
    "Munich Re":        ["munich re", "munichre"],
    "Swiss Re":         ["swiss re", "swissre"],
    "Lloyd's":          ["lloyd's", "lloyds"],
    "Lemonade":         ["lemonade"],
    "Root":             ["root insurance"],
    "Hippo":            ["hippo insurance", "hippo home"],
}


def detect_incumbents(articles: list, window_days: int = 7) -> list[dict]:
    """Count incumbent mentions in the last N days. Returns sorted list."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
    counts: dict[str, int] = {k: 0 for k in INCUMBENTS}
    articles_by_incumbent: dict[str, list] = {k: [] for k in INCUMBENTS}

    for a in articles:
        try:
            pub = datetime.fromisoformat(a.get("published_at", ""))
            if pub.tzinfo is None:
                pub = pub.replace(tzinfo=timezone.utc)
            if pub < cutoff:
                continue
        except Exception:
            continue
        text = (a.get("title", "") + " " + a.get("summary", "")).lower()
        for name, keywords in INCUMBENTS.items():
            if any(kw in text for kw in keywords):
                counts[name] += 1
                if len(articles_by_incumbent[name]) < 3:
                    articles_by_incumbent[name].append(a)

    result = [
        {"name": name, "count": counts[name], "articles": articles_by_incumbent[name]}
        for name in INCUMBENTS if counts[name] > 0
    ]
    result.sort(key=lambda x: x["count"], reverse=True)
    return result


# ── Enrich all articles ───────────────────────────────────────────────────────
def enrich_articles(articles: list) -> list:
    """Run all enrichment in one pass. Call after loading articles."""
    amplified = detect_amplified(articles)
    for a in articles:
        score_article(a)
        a["amplified"] = a.get("id", "") in amplified
    return articles
