"""
Generate daily newsletter HTML — docs/newsletter.html
Format: executive editorial style with 5 top stories.
Uses OpenAI for article intros if key is set; falls back to extractive.
Titles always translated to Spanish (OpenAI > MyMemory free API > original).
"""
import os
import re
import json
import logging
import time
from datetime import datetime, timezone, timedelta

log = logging.getLogger(__name__)

DOCS_DIR  = os.path.join(os.path.dirname(__file__), "..", "docs")
SITE_URL  = "https://albertoiglesiascatalan-sudo.github.io/Insurtech"

# ── Optional OpenAI ────────────────────────────────────────────────────────────
_openai_client = None
_OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
if _OPENAI_KEY:
    try:
        from openai import OpenAI as _OpenAI
        _openai_client = _OpenAI(api_key=_OPENAI_KEY)
    except Exception:
        pass


# ── Free translation via MyMemory API ─────────────────────────────────────────
def _translate_to_es(text: str) -> str:
    """Translate text to Spanish using Google Translate unofficial endpoint.
    Falls back to original text on any failure — never blocks the pipeline."""
    if not text or _is_spanish_quick(text):
        return text
    try:
        import httpx, urllib.parse
        # Unofficial Google Translate endpoint (no key required, used by many tools)
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx", "sl": "auto", "tl": "es",
            "dt": "t", "q": text[:400],
        }
        headers = {"User-Agent": "Mozilla/5.0 (compatible; InsurTechBot/1.0)"}
        r = httpx.get(url, params=params, headers=headers, timeout=6)
        if r.status_code == 200:
            data = r.json()
            # Response format: [[["translated", "original", ...], ...], ...]
            parts = data[0] if data else []
            translated = "".join(p[0] for p in parts if p and p[0])
            if translated and translated.strip() != text.strip():
                return translated.strip()
    except Exception as e:
        log.debug(f"Translation error: {e}")
    return text


def _is_spanish_quick(text: str) -> bool:
    """Fast check: is text already in Spanish?"""
    words = {w.lower() for w in re.findall(r'\b[a-záéíóúüñ]{2,}\b', text, re.IGNORECASE)}
    es_markers = {"de","la","el","en","los","las","un","una","por","para","con","del",
                  "se","que","su","sus","al","sobre","más","también","son","está","fue",
                  "nuevo","nueva","anuncia","publica","lanza","seguro","seguros"}
    return len(words & es_markers) >= 2


# ── Language detection (simple heuristic) ─────────────────────────────────────
_ES_WORDS = {"de","la","el","en","los","las","un","una","por","para","con","del",
             "se","que","su","sus","al","sobre","más","también","son","está","fue"}

def _is_spanish(text: str) -> bool:
    """Returns True if text appears to be in Spanish."""
    words = {w.lower() for w in re.findall(r'\b[a-záéíóúüñ]{2,}\b', text, re.IGNORECASE)}
    return len(words & _ES_WORDS) >= 2


# ── Key fact extractor ────────────────────────────────────────────────────────
def _extract_key_fact(title: str, summary: str) -> str:
    """
    Extracts the most concrete, specific sentence from title + summary.
    Always uses sentence boundaries — never cuts mid-word.
    Returns in Spanish if translation works, otherwise in original language.
    """
    # Clean summary: strip bullet characters, strip mid-sentence fragments
    clean_summary = re.sub(r'(?m)^[\s•·\-–—]+', '', summary or "").strip()
    full = f"{title}. {clean_summary}" if clean_summary else title
    # Only keep sentences that start with a capital letter (avoid mid-sentence fragments)
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', full)
                 if len(s.strip()) > 25 and re.match(r'^[A-ZÁÉÍÓÚ"\d]', s.strip())]

    def _try_translate(s: str) -> str:
        translated = _translate_to_es(s[:200])
        time.sleep(0.15)
        if translated and translated.strip() != s[:200].strip():
            return translated.strip()
        return s.strip()

    money_re = re.compile(
        r'[\$£€]\s*\d[\d,.]*\s*(?:million|billion|bn|m|mn|MM|B)\b'
        r'|USD\s*\d[\d,.]*\s*(?:million|billion|bn|m)?'
        r'|\d[\d,.]*\s*(?:million|billion)\s+(?:dollar|pound|euro)',
        re.IGNORECASE
    )

    # 1. Sentence with a monetary amount (most specific)
    for sent in sentences:
        if money_re.search(sent):
            return _try_translate(sent).rstrip(".") + "."

    # 2. Sentence with a percentage
    for sent in sentences:
        if re.search(r'\d+[\.,]?\d*\s*(?:percent|%|per cent)\b', sent, re.IGNORECASE):
            return _try_translate(sent).rstrip(".") + "."

    # 3. Direct executive quote
    for sent in sentences:
        m = re.search(r'"([^"]{20,120})"', sent)
        if m:
            return f'"{_try_translate(m.group(1)).strip()}"'

    # 4. Most fact-dense sentence (digits + capitalized entities)
    def fact_density(s):
        return len(re.findall(r'\d', s)) * 2 + len(re.findall(r'\b[A-Z][a-z]{2,}', s))

    ranked = sorted(sentences, key=fact_density, reverse=True)
    if ranked and fact_density(ranked[0]) >= 4:
        return _try_translate(ranked[0][:200]).rstrip(".") + "."

    return ""


# ── AI editorial per article ──────────────────────────────────────────────────
def _ai_editorial(article: dict) -> dict:
    """
    Returns {"title": str, "intro": str, "bullets": [{"q": str, "a": str}, ...]}.
    Bullets are {"q": bold lead-in, "a": explanation} — rendered as bold question + prose.
    Always in Spanish. Uses OpenAI if available; falls back to free translation + templates.
    """
    title_es   = article.get("title", "")
    title_orig = article.get("title_original", title_es)
    summary    = article.get("summary", "")
    source     = article.get("source", "")
    why        = article.get("why_matters", "")
    deal       = article.get("deal")
    cat        = article.get("category", "General")
    signal_label = article.get("signal_label", "")

    summary_for_ai = summary if summary else title_orig

    if _openai_client:
        try:
            resp = _openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": (
                    "Eres periodista especializado en seguros y fintech para InsurTech Intelligence, "
                    "newsletter de referencia para directivos aseguradores en España y Latinoamérica. "
                    "Escribe SIEMPRE en español, con tono analítico, directo y sin jerga innecesaria.\n\n"
                    "Para este artículo escribe:\n"
                    "1. title_es: el título traducido y adaptado al español (máx 15 palabras).\n"
                    "2. intro: un párrafo periodístico de 3-4 frases que explique QUÉ ha pasado, "
                    "POR QUÉ importa al mercado asegurador y QUÉ implica estratégicamente. "
                    "Empieza directamente con el hecho, sin introducción. Usa datos concretos si los hay.\n"
                    "3. bullets: exactamente 3 objetos con 'q' (pregunta o frase en negrita, máx 6 palabras) "
                    "y 'a' (respuesta analítica, 20-35 palabras). Ejemplos de 'q': "
                    "'¿Qué cambia para las aseguradoras?', 'El dato clave:', '¿Qué vigilar?', "
                    "'Lo que no dice el comunicado:', 'Impacto en pricing:'.\n\n"
                    "JSON: {\"title_es\":\"...\",\"intro\":\"...\","
                    "\"bullets\":[{\"q\":\"...\",\"a\":\"...\"},{\"q\":\"...\",\"a\":\"...\"},"
                    "{\"q\":\"...\",\"a\":\"...\"}]}\n\n"
                    f"Título: {title_orig}\n"
                    f"Fuente: {source}\n"
                    f"Categoría: {cat}\n"
                    f"Contenido: {summary_for_ai[:700]}"
                )}],
                max_tokens=500,
                temperature=0.5,
            )
            raw = resp.choices[0].message.content.strip()
            raw = re.sub(r'^```json\s*|\s*```$', '', raw, flags=re.MULTILINE).strip()
            data    = json.loads(raw)
            intro   = data.get("intro", "")
            bullets = data.get("bullets", [])
            title_out = data.get("title_es", title_es) or title_es
            # Normalise bullets — accept both {q,a} dicts and plain strings
            norm = []
            for b in bullets[:3]:
                if isinstance(b, dict):
                    norm.append({"q": b.get("q",""), "a": b.get("a","")})
                else:
                    parts = str(b).split(":", 1)
                    norm.append({"q": parts[0].strip(), "a": parts[1].strip() if len(parts)>1 else str(b)})
            if intro and len(norm) >= 2:
                return {"title": title_out, "intro": intro, "bullets": norm}
        except Exception as e:
            log.debug(f"OpenAI newsletter editorial error: {e}")

    # ── Extractive fallback ────────────────────────────────────────────────────
    # Translate title if needed
    if not _is_spanish_quick(title_es) and not _is_spanish_quick(title_orig):
        title_es = _translate_to_es(title_orig or title_es)
        time.sleep(0.3)

    # ── Build intro from actual article content ──────────────────────────────
    # Priority: (1) translate summary → (2) use summary in English → (3) minimal template
    intro = ""
    if summary:
        sents = [s.strip() for s in re.split(r'(?<=[.!?])\s+', summary) if len(s.strip()) > 40]
        raw = " ".join(sents[:3]) if sents else summary[:400]
        if _is_spanish(raw):
            intro = raw
        else:
            translated = _translate_to_es(raw[:600])
            time.sleep(0.3)
            if translated and translated.strip() != raw[:600].strip():
                intro = translated.strip()
            else:
                # Translation unavailable — use English summary; it's real content
                intro = raw[:350]

    if not intro:
        # Only as absolute last resort: minimal factual sentence, never a generic template
        intro = f"Según {source}, este movimiento tiene implicaciones directas para el sector asegurador en términos de {(signal_label or cat).lower()}."

    # Clean up common summary artifacts (leading bullets, dashes)
    intro = re.sub(r'^[\s•·\-–—]+', '', intro).strip()

    # ── Build bullets — article-specific, zero padding ───────────────────────
    label = signal_label or cat

    # Bullet 1 — the sharpest specific fact (amount / % / quote / entity)
    key_fact = _extract_key_fact(title_orig or title_es, summary)
    # Skip if key_fact is essentially the same text as the intro (first 60 chars overlap)
    if key_fact and intro and key_fact[:60].lower() == intro[:60].lower():
        key_fact = ""
    # Skip if key_fact is just the title restated
    if key_fact and (title_orig or title_es) and key_fact[:50].lower() in (title_orig or title_es)[:80].lower():
        key_fact = ""
    b1 = {"q": "El dato clave:", "a": key_fact} if key_fact else None

    # Bullet 2 — deal amount or why_matters
    b2 = None
    if deal and deal.get("amount_str") and deal["amount_str"] != "—":
        rnd = f" ({deal['round']})" if deal.get("round") and deal["round"] != "—" else ""
        b2 = {"q": "La operación:", "a": f"{deal['amount_str']}{rnd}, una de las mayores transacciones detectadas en el sector en las últimas semanas."}
    elif why:
        b2 = {"q": "¿Por qué importa?", "a": why}

    # Bullet 3 — forward-looking, signal-specific (the one template we keep — it's analytical)
    fwd_map = {
        "Regulación":          "Las aseguradoras deberán revisar sus modelos de cumplimiento y posiblemente provisionar costes de adaptación normativa.",
        "M&A":                 "La consolidación reduce actores independientes y abre oportunidades para distribuidores y proveedores de tecnología.",
        "Inversión":           "El capital invertido anticipa las áreas donde los incumbentes afrontarán mayor presión competitiva en los próximos 12-24 meses.",
        "Clima & Catástrofes": "El sector deberá revisar modelos de pricing y cobertura en las zonas afectadas ante el incremento de eventos extremos.",
        "Tecnología":          "Las aseguradoras sin plan de integración tecnológica arriesgan rezagarse en eficiencia operativa y experiencia de cliente.",
        "Fraude":              "La inversión en analítica avanzada y verificación digital es prioritaria para proteger los márgenes técnicos.",
        "Vida y Salud":        "El segmento salud crece a doble dígito; los actores sin oferta digital perderán cuota frente a las insurtechs.",
        "Automóvil":           "Movilidad conectada y vehículos eléctricos siguen redefiniendo la tarificación y la gestión de siniestros.",
        "Embebido":            "La distribución embebida crece a doble dígito; los canales tradicionales deben reinventarse para no perder relevancia.",
        "Liderazgo":           "Los cambios de liderazgo suelen anticipar reestructuraciones y nuevas apuestas estratégicas en los 6-18 meses siguientes.",
    }
    b3 = {"q": "¿Qué vigilar?", "a": fwd_map.get(label, "Seguimiento recomendado desde las perspectivas de riesgo técnico, regulatorio y competitivo.")}

    # Assemble — always 3 bullets
    bullets = [b for b in [b1, b2, b3] if b]
    if len(bullets) < 3:
        # Use a second summary sentence as "El contexto:" to fill the gap
        sents = [s.strip() for s in re.split(r'(?<=[.!?])\s+', summary or "")
                 if len(s.strip()) > 40 and re.match(r'^[A-ZÁÉÍÓÚ"\d]', s.strip())]
        ctx_text = sents[1] if len(sents) > 1 else sents[0] if sents else intro[:140]
        ctx_bullet = {"q": "El contexto:", "a": ctx_text[:200].rstrip(".") + "."}
        if not b1 and not b2:
            bullets = [ctx_bullet, b3]
        elif not b1:
            bullets = [ctx_bullet, b2, b3]
        else:
            bullets = [b1, ctx_bullet, b3]
    bullets = bullets[:3]

    return {"title": title_es, "intro": intro, "bullets": bullets}


# ── Intro editorial del día ────────────────────────────────────────────────────
def _day_intro(articles_today: list, articles_week: list, selected: list = None) -> str:
    """
    Generates the opening editorial paragraph.
    articles_today = full pool (for stats); selected = deduplicated top5 (for story references).
    Uses OpenAI if available; otherwise builds it from stats.
    """
    featured = selected or articles_today   # use top5 for entity extraction
    n_today   = len(articles_today)
    n_signals = sum(1 for a in articles_today if a.get("is_signal"))
    n_inv     = sum(1 for a in articles_week  if a.get("category") == "Inversión")
    n_reg     = sum(1 for a in articles_today if a.get("category") == "Regulación")
    n_deals   = sum(1 for a in articles_today if a.get("deal") and a["deal"].get("amount_str"))

    # Top themes today
    from collections import Counter
    cats = Counter(a.get("signal_label") for a in articles_today if a.get("signal_label"))
    top_themes = [c for c, _ in cats.most_common(3) if c]

    if _openai_client and articles_today:
        # Use Spanish titles (title field) for context
        titles_sample = "; ".join(
            (a.get("title") or a.get("title_original", ""))[:80] for a in articles_today[:8]
        )
        try:
            resp = _openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": (
                    "Eres el redactor jefe de InsurTech Intelligence, newsletter de referencia para "
                    "directivos del sector asegurador en España y Latinoamérica. Escribe el párrafo "
                    "editorial de apertura de hoy. REGLAS: (1) Empieza directamente con la noticia más "
                    "importante — nunca con 'Hoy', 'Buenos días' ni frases de bienvenida. (2) Nombra "
                    "compañías o cifras concretas del día — nada genérico. (3) Conecta 2-3 noticias del "
                    "día con una lectura periodística: ¿qué patrón o tensión revelan juntas? (4) Cierra "
                    "invitando a seguir leyendo de forma natural, sin ser comercial. (5) Entre 4 y 6 "
                    "frases. (6) Tono: analítico, humano, con criterio — como el editorial de un "
                    "suplemento financiero de calidad, no como un boletín automático.\n\n"
                    f"Artículos monitorizados hoy: {n_today} de más de 40 fuentes globales.\n"
                    f"Señales de alto impacto detectadas: {n_signals}\n"
                    f"Operaciones de inversión esta semana: {n_inv}\n"
                    f"Temas dominantes: {', '.join(top_themes) if top_themes else 'mercado general'}\n"
                    f"Titulares de hoy: {titles_sample}"
                )}],
                max_tokens=220,
                temperature=0.6,
            )
            intro = resp.choices[0].message.content.strip()
            if intro:
                return intro
        except Exception as e:
            log.debug(f"OpenAI day intro error: {e}")

    # ── Extractive fallback — journalistic, not a dashboard ────────────────────
    # Build narrative using real article data: lead story, dominant themes, context
    lead = featured[0] if featured else None
    lead_title = (lead.get("title_original") or lead.get("title", "")) if lead else ""
    lead_src   = lead.get("source", "") if lead else ""
    lead_label = lead.get("signal_label", "") if lead else ""

    # Extract the dominant company or entity from the lead title
    entity_match = re.search(r'\b([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})*)\b', lead_title)
    lead_entity = entity_match.group(1) if entity_match else lead_src

    # Pick second theme for narrative contrast
    second_label = top_themes[1] if len(top_themes) > 1 else top_themes[0] if top_themes else ""
    third_label  = top_themes[2] if len(top_themes) > 2 else ""

    # Build investment/regulatory narrative beats
    inv_sentence = ""
    reg_sentence = ""
    if n_inv >= 2:
        inv_sentence = f" Esta semana el dinero no ha parado: <strong>{n_inv} operaciones de inversión</strong> detectadas en los últimos siete días dibujan un sector que sigue captando capital a buen ritmo."
    elif n_inv == 1:
        inv_sentence = " Se ha cerrado al menos una operación de inversión relevante en los últimos siete días."
    if n_reg >= 2:
        reg_sentence = f" En el frente regulatorio, <strong>{n_reg} noticias</strong> de hoy exigen atención de los equipos de cumplimiento."
    elif n_reg == 1:
        reg_sentence = " Hay además un movimiento regulatorio que conviene seguir de cerca."

    # Signals context
    signal_sentence = ""
    if n_signals >= 10:
        signal_sentence = f" De los {n_today} artículos rastreados hoy, <strong>{n_signals}</strong> han activado nuestras alertas de señal — una densidad de noticias relevante que no veíamos en días."
    elif n_signals >= 3:
        signal_sentence = f" Entre los {n_today} artículos analizados, hemos identificado <strong>{n_signals} señales</strong> que merecen seguimiento inmediato."

    # Second story entity for narrative contrast
    second = featured[1] if len(featured) > 1 else None
    second_title = (second.get("title_original") or second.get("title", "")) if second else ""
    second_match = re.search(r'\b([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})*)\b', second_title)
    second_entity = second_match.group(1) if second_match else ""
    second_label_a = second.get("signal_label", "") if second else ""

    # Connective between lead and second story (only if second entity adds something)
    second_beat = ""
    if second_entity and second_entity != lead_entity:
        if second_label_a == lead_label:
            second_beat = f" No es la única señal del día: {second_entity} también mueve ficha en la misma dirección."
        else:
            second_beat = f" La jornada se completa con {second_entity}, que pone el foco en otro frente del mercado: el de {second_label_a.lower() if second_label_a else 'las operaciones corporativas'}."

    # Compose the opening — start with the lead story entity, not stats
    label_verbs = {
        "Inversión":           f"{lead_entity} protagoniza la apertura con un movimiento de capital que confirma el apetito inversor por la transformación del seguro",
        "M&A":                 f"{lead_entity} encabeza la jornada con una operación corporativa que redefine el mapa competitivo del sector",
        "Regulación":          f"Los supervisores marcan la agenda hoy: {lead_entity} centra el debate regulatorio con implicaciones para todo el mercado asegurador",
        "Clima & Catástrofes": f"{lead_entity} abre la jornada recordando que el riesgo catastrófico sigue siendo el gran acelerador del cambio en el sector reasegurador",
        "Tecnología":          f"{lead_entity} marca el paso tecnológico de la jornada con un avance que presiona a los incumbentes a repensar sus operaciones",
        "Fraude":              f"El fraude vuelve al primer plano: {lead_entity} activa las alertas del sector con un movimiento que los equipos de siniestros no pueden ignorar",
        "Liderazgo":           f"Los movimientos directivos centran la atención hoy: {lead_entity} anticipa un giro estratégico con implicaciones para el mercado",
    }
    opening = label_verbs.get(lead_label,
        f"{lead_entity} encabeza la jornada de hoy con una noticia de primer orden para el sector asegurador")

    close = (f" A continuación, las cinco historias que hemos seleccionado entre {n_today} artículos"
             f" de más de 40 fuentes, ordenadas por impacto real sobre el negocio asegurador.")

    return f"{opening}.{second_beat}{inv_sentence}{reg_sentence}{signal_sentence}{close}"


# ── Word count for reading time ────────────────────────────────────────────────
def _word_count(texts: list) -> int:
    return sum(len(t.split()) for t in texts if t)


# ── Main generator ─────────────────────────────────────────────────────────────
def generate_newsletter(articles: list):
    now      = datetime.now(timezone.utc)
    cutoff48 = now - timedelta(hours=48)
    cutoff7  = now - timedelta(days=7)

    # Candidate pool: last 48h, sorted by signal_score
    pool = []
    for a in articles:
        try:
            pub = datetime.fromisoformat(a.get("published_at", ""))
            if pub.tzinfo is None:
                pub = pub.replace(tzinfo=timezone.utc)
            if pub >= cutoff48:
                pool.append(a)
        except Exception:
            pass

    if not pool:
        log.info("Newsletter: no articles in last 48h, skipping.")
        return

    pool.sort(key=lambda x: x.get("signal_score", 0), reverse=True)

    def _title_fingerprint(title: str) -> frozenset:
        """Significant words from title for cross-source story dedup."""
        stopwords = {"the","a","an","in","on","to","for","of","is","are","was","as","with",
                     "from","its","it","that","this","at","by","and","or","but","raises","launches",
                     "million","billion","m","bn","new","says","said","report","reports","how","why"}
        # Normalize numbers: $12m → 12, $12 million → 12
        normalized = re.sub(r'[\$£€]', '', title.lower())
        normalized = re.sub(r'(\d+)\s*(?:m|mn|million)\b', r'\1', normalized)
        normalized = re.sub(r'(\d+)\s*(?:bn|billion)\b', r'\1000', normalized)
        words = re.findall(r'[a-z0-9]{2,}', normalized)
        return frozenset(w for w in words if w not in stopwords)

    def _is_story_dup(fp: frozenset, seen: frozenset) -> bool:
        """True when two titles describe the same story (containment ≥ 70%)."""
        if not fp or not seen:
            return False
        overlap = len(fp & seen)
        shorter = min(len(fp), len(seen))
        if shorter < 2:
            return False
        return overlap / shorter >= 0.7

    # Enforce source diversity AND title-level story dedup
    top5: list = []
    source_count: dict = {}
    seen_fingerprints: list = []
    for a in pool:
        src = a.get("source", "")
        if source_count.get(src, 0) >= 2:
            continue
        fp = _title_fingerprint(a.get("title_original", a.get("title", "")))
        if any(_is_story_dup(fp, seen) for seen in seen_fingerprints):
            log.debug(f"Newsletter: dedup story '{a.get('title','')[:50]}'")
            continue
        top5.append(a)
        source_count[src] = source_count.get(src, 0) + 1
        seen_fingerprints.append(fp)
        if len(top5) == 5:
            break

    # Week articles for stats
    week = [a for a in articles if _try_after(a.get("published_at",""), cutoff7)]

    # Build day intro — use pool for aggregate stats, top5 for story references
    day_intro_text = _day_intro(pool, week, top5)

    # Build editorial per article
    editorials = [_ai_editorial(a) for a in top5]

    # ── Post-process: eliminate duplicate "¿Por qué importa?" bullets ──────────
    # "¿Qué vigilar?" is intentionally sector-level so repetition is acceptable.
    # "¿Por qué importa?" and "El dato clave:" should be unique per article.
    seen_why: set = set()
    for idx, (a, ed) in enumerate(zip(top5, editorials)):
        new_bullets = []
        for b in ed["bullets"]:
            if b["q"] in ("¿Por qué importa?", "El dato clave:"):
                key = b["a"][:70]
                if key in seen_why:
                    # Replace with a short extractive sentence from the summary
                    summary_sents = [s.strip() for s in re.split(r'(?<=[.!?])\s+',
                                     a.get("summary", "")) if len(s.strip()) > 40]
                    alt = summary_sents[1] if len(summary_sents) > 1 else summary_sents[0] if summary_sents else ""
                    if alt and alt[:60] not in seen_why:
                        new_bullets.append({"q": b["q"], "a": alt[:200]})
                        seen_why.add(alt[:60])
                    # else just drop the duplicate — 2 bullets is better than a repeated one
                    continue
                seen_why.add(key)
            new_bullets.append(b)
        ed["bullets"] = new_bullets if new_bullets else ed["bullets"]

    # Compute reading time
    def _bullets_text(bullets):
        parts = []
        for b in bullets:
            if isinstance(b, dict):
                parts.append(b.get("q","") + " " + b.get("a",""))
            else:
                parts.append(str(b))
        return " ".join(parts)

    all_words = [day_intro_text] + [
        e["intro"] + " " + _bullets_text(e["bullets"]) for e in editorials
    ]
    words = _word_count(all_words)
    read_min = max(3, round(words / 200))

    # Date strings
    day_names = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"]
    day_label = day_names[now.weekday()].capitalize()
    date_long = now.strftime(f"{day_label} %-d de %B de %Y")
    month_names = {
        "January":"enero","February":"febrero","March":"marzo","April":"abril",
        "May":"mayo","June":"junio","July":"julio","August":"agosto",
        "September":"septiembre","October":"octubre","November":"noviembre","December":"diciembre"
    }
    for en, es in month_names.items():
        date_long = date_long.replace(en, es)

    # Category icons
    cat_icons = {
        "Tecnología": "🤖", "Regulación": "⚖️", "Inversión": "💰",
        "Vida y Salud": "❤️", "Automóvil": "🚗", "Catástrofes": "🌪️",
        "Fraude": "🔍", "Embebido": "🔗", "General": "📰",
    }

    # ── Render articles ──────────────────────────────────────────────────────────
    articles_html = ""
    for i, (a, ed) in enumerate(zip(top5, editorials), 1):
        cat   = a.get("category", "General")
        # When OpenAI wasn't available during ingestion, category defaults to "General"
        # Use signal_label as a more accurate display label
        signal_label_disp = a.get("signal_label", "")
        display_cat = signal_label_disp if (cat == "General" and signal_label_disp) else cat
        icon  = cat_icons.get(cat, "📰")
        # Use AI/free-translated Spanish title from editorial (always in Spanish)
        title = ed.get("title") or a.get("title", "") or a.get("title_original", "")
        url   = a.get("url", "#")
        src   = a.get("source", "")
        image = a.get("image_url", "")
        signal_label = a.get("signal_label", "")
        score = a.get("signal_score", 0)

        img_html = ""
        if image:
            img_html = f"""
        <tr><td style="padding:0 0 20px">
          <img src="{image}" alt="" width="100%" style="display:block;border-radius:8px;max-height:280px;object-fit:cover" />
        </td></tr>"""

        bullets_html = ""
        for b in ed["bullets"]:
            if isinstance(b, dict):
                q, a_text = b.get("q",""), b.get("a","")
            else:
                parts = str(b).split(":", 1)
                q, a_text = parts[0].strip(), (parts[1].strip() if len(parts) > 1 else str(b))
            bullets_html += (
                f'<li style="margin-bottom:14px;line-height:1.6;color:#c8bfaf;font-size:14px">'
                f'<strong style="color:#f0e6d3">{q}</strong> {a_text}'
                f'</li>'
            )

        signal_badge = ""
        sig_icon = a.get("signal_icon", "⚡")
        # Show badge only if signal_label adds info beyond what display_cat already shows
        if signal_label and score >= 18 and signal_label != display_cat:
            signal_badge = (
                f' <span style="font-size:10px;font-weight:700;color:#f59e0b;'
                f'background:#f59e0b22;border:1px solid #f59e0b44;border-radius:4px;'
                f'padding:1px 7px">{sig_icon} {signal_label}</span>'
            )
        elif display_cat == signal_label and signal_label:
            # Use signal icon inline with the category label
            icon = sig_icon

        articles_html += f"""
        <!-- Article {i} -->
        <tr><td style="padding:28px 0 0;border-top:1px solid #3a2e1e">
          <p style="margin:0 0 8px;font-size:11px;font-weight:800;color:#c0392b;
                    text-transform:uppercase;letter-spacing:1px">
            {i}. {icon} {display_cat}{signal_badge}
          </p>
          <h2 style="margin:0 0 14px;font-size:21px;font-weight:800;line-height:1.3;color:#f5f0e8">
            {title}
          </h2>
          {img_html}
          <p style="margin:0 0 18px;font-size:15px;line-height:1.7;color:#c8bfaf">
            {ed['intro']}
          </p>
          <ol style="margin:0 0 18px;padding-left:20px">
            {bullets_html}
          </ol>
          <p style="margin:0">
            <a href="{url}" style="font-size:13px;color:#d4a857;font-weight:600;text-decoration:none">
              Leer en {src} →
            </a>
          </p>
        </td></tr>"""

    # ── Full HTML ────────────────────────────────────────────────────────────────
    html = _build_html(date_long, words, read_min, day_intro_text, articles_html)

    path = os.path.join(DOCS_DIR, "newsletter.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    ai_note = "con IA" if _openai_client else "extractivo"
    log.info(f"Newsletter generated ({ai_note}): {path} — {len(top5)} stories, {words} words")
    print(f"Newsletter generated: {path} ({len(top5)} stories · {read_min} min · {ai_note})")
    return date_long, read_min, words, articles_html, day_intro_text


def _build_html(date_long, words, read_min, day_intro_text, articles_html):
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>InsurTech Intelligence · {date_long}</title>
  <meta name="description" content="Las 5 noticias más importantes del sector insurtech hoy." />
  <link rel="canonical" href="{SITE_URL}/newsletter.html" />
  <style>
    body {{ margin:0; padding:0; background:#0e0a04; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; }}
    a {{ color:#d4a857; }}
    @media (max-width:600px) {{
      .wrapper {{ padding: 0 !important; }}
      .inner   {{ padding: 24px 20px !important; }}
      h1       {{ font-size: 28px !important; }}
      h2       {{ font-size: 18px !important; }}
    }}
  </style>
</head>
<body style="background:#0e0a04">
{_newsletter_body(date_long, words, read_min, day_intro_text, articles_html)}
</body>
</html>"""


def _newsletter_body(date_long, words, read_min, day_intro_text, articles_html):
    """Returns just the table body — reused both in newsletter.html and embedded in index.html."""
    return f"""
<table role="presentation" width="100%" cellspacing="0" cellpadding="0"
       style="background:#0e0a04;padding:32px 16px" class="wrapper">
<tr><td>
<table role="presentation" width="100%" cellspacing="0" cellpadding="0"
       style="max-width:620px;margin:0 auto;background:#1a1208;border-radius:12px;overflow:hidden">

  <!-- Header -->
  <tr><td style="background:#120d06;padding:36px 40px 28px;border-bottom:2px solid #3a2e1e" class="inner">
    <p style="margin:0 0 4px;font-size:11px;font-weight:700;color:#6b5e4a;
              text-transform:uppercase;letter-spacing:2px">InsurTech Intelligence</p>
    <h1 style="margin:0 0 8px;font-size:34px;font-weight:900;color:#f5f0e8;line-height:1.15">
      Briefing Diario
    </h1>
    <p style="margin:0;font-size:13px;color:#6b5e4a">{date_long} &nbsp;·&nbsp; {words} palabras &nbsp;·&nbsp; {read_min} min de lectura</p>
  </td></tr>

  <!-- Day intro -->
  <tr><td style="padding:28px 40px 0" class="inner">
    <p style="margin:0;font-size:16px;line-height:1.7;color:#c8bfaf">{day_intro_text}</p>
  </td></tr>

  <!-- Articles -->
  <tr><td style="padding:0 40px" class="inner">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
      {articles_html}
    </table>
  </td></tr>

  <!-- CTA -->
  <tr><td style="padding:32px 40px;text-align:center;border-top:1px solid #3a2e1e" class="inner">
    <a href="{SITE_URL}" style="display:inline-block;padding:13px 32px;background:#c0392b;
       color:#fff;border-radius:6px;text-decoration:none;font-size:14px;font-weight:700;
       letter-spacing:.3px">Ver todas las noticias →</a>
    <p style="margin:16px 0 0;font-size:11px;color:#4a3e2e">
      InsurTech Intelligence · Actualizado cada 6 horas ·
      <a href="{SITE_URL}/feed.xml" style="color:#6b5e4a">RSS</a> ·
      <a href="{SITE_URL}" style="color:#6b5e4a">Web</a>
    </p>
  </td></tr>

</table>
</td></tr>
</table>"""


def build_inline_newsletter(articles: list) -> str:
    """Returns the newsletter body HTML for embedding directly in index.html.
    Returns empty string if no articles available."""
    result = generate_newsletter(articles)
    if result is None:
        return ""
    date_long, read_min, words, articles_html, day_intro_text = result
    return _newsletter_body(date_long, words, read_min, day_intro_text, articles_html)


def _try_after(iso: str, cutoff) -> bool:
    try:
        pub = datetime.fromisoformat(iso)
        if pub.tzinfo is None:
            pub = pub.replace(tzinfo=timezone.utc)
        return pub >= cutoff
    except Exception:
        return False


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    articles_path = os.path.join(os.path.dirname(__file__), "articles.json")
    with open(articles_path) as f:
        articles = json.load(f)
    generate_newsletter(articles)
