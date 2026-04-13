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
                    "Eres corresponsal especializado en seguros para InsurTech Intelligence, una de las "
                    "newsletters más respetadas del sector asegurador en España y Latinoamérica. Tu estilo "
                    "es el de un periodista económico galardonado: preciso, sin jerga, con criterio propio "
                    "y capaz de conectar hechos con implicaciones estratégicas. Escribes SIEMPRE en español.\n\n"
                    "Para este artículo, escribe en JSON con exactamente estos tres campos:\n\n"
                    "• title_es: el titular en español, informativo y directo, máximo 14 palabras. "
                    "Sin dos puntos iniciales ni gerundios. Empieza con el sujeto.\n\n"
                    "• intro: un párrafo de 4-5 frases. Arranca con el hecho concreto (quién, qué, cuánto). "
                    "Segunda frase: contexto del sector o de la empresa. Tercera: por qué este movimiento "
                    "importa ahora. Cuarta-quinta: implicación estratégica o dato que lo hace relevante. "
                    "Usa cifras reales del artículo si las hay. Tono de 'El País Economía' o 'Cinco Días'.\n\n"
                    "• analysis: un párrafo de 3-4 frases de análisis puro. Qué revela este hecho sobre "
                    "la dirección del mercado asegurador. Qué deben vigilar los directivos. Sin repetir "
                    "información del intro, añade perspectiva. Termina con una frase de acción o alerta.\n\n"
                    "JSON EXACTO (sin markdown, sin texto extra):\n"
                    "{\"title_es\":\"...\",\"intro\":\"...\",\"analysis\":\"...\"}\n\n"
                    f"Título original: {title_orig}\n"
                    f"Fuente: {source}\n"
                    f"Señal: {signal_label or cat}\n"
                    f"Contenido: {summary_for_ai[:900]}"
                )}],
                max_tokens=650,
                temperature=0.65,
            )
            raw = resp.choices[0].message.content.strip()
            raw = re.sub(r'^```json\s*|\s*```$', '', raw, flags=re.MULTILINE).strip()
            data = json.loads(raw)
            intro    = data.get("intro", "").strip()
            analysis = data.get("analysis", "").strip()
            title_out = data.get("title_es", title_es) or title_es
            if intro and analysis:
                return {"title": title_out, "intro": intro, "analysis": analysis}
        except Exception as e:
            log.debug(f"OpenAI newsletter editorial error: {e}")

    # ── Extractive fallback ─────────────────────────────────────────────────────
    # Translate title if needed
    if not _is_spanish_quick(title_es) and not _is_spanish_quick(title_orig):
        title_es = _translate_to_es(title_orig or title_es)
        time.sleep(0.3)

    # Strip RSS boilerplate — only the "appeared first on" pattern; leave content intact
    sc = summary or ''
    sc = re.sub(r'(?i)the post .{0,160} appeared first on[^\.]*\.', ' ', sc)
    sc = re.sub(r'(?i)\. appeared first on[^\.]+\.', '.', sc)
    sc = re.sub(r'\s{2,}', ' ', sc).strip()
    summary_clean = re.sub(r'^[\s•·\-–—]+', '', sc).strip()

    # Build intro: first 3 substantive full sentences
    intro = ""
    if summary_clean:
        sents = [s.strip() for s in re.split(r'(?<=[.!?])\s+', summary_clean)
                 if len(s.strip()) > 40 and re.match(r'^[A-ZÁÉÍÓÚ"\d]', s.strip())]
        raw = " ".join(sents[:3]) if sents else summary_clean.strip()
        if _is_spanish(raw):
            intro = raw
        else:
            translated = _translate_to_es(raw[:700])
            time.sleep(0.3)
            intro = translated.strip() if (translated and translated.strip() != raw[:700].strip()) else raw

    if not intro:
        intro = f"Según {source}, este movimiento tiene implicaciones directas para el sector asegurador."

    intro = re.sub(r'^[\s•·\-–—]+', '', intro).strip()

    # Build analysis: most specific extractive sentence NOT in intro + signal closing
    label = signal_label or cat
    fwd_map = {
        "Regulación":          "Para los equipos de cumplimiento y riesgo, este movimiento exige revisión de procedimientos y potencial provisión de costes de adaptación normativa.",
        "M&A":                 "En un mercado donde la consolidación avanza a ritmo sostenido, cada operación reduce el espacio de maniobra de los actores independientes y revalúa el peso de las plataformas tecnológicas.",
        "Inversión":           "El flujo de capital hacia este segmento anticipa dónde los incumbentes encontrarán mayor presión competitiva en los próximos 12 a 24 meses. Las compañías sin hoja de ruta digital en esta área se arriesgan a perder cuota de forma silenciosa.",
        "Clima & Catástrofes": "El sector reasegurador deberá revisar modelos de pricing y límites de cobertura en las geografías expuestas. La frecuencia creciente de eventos extremos está dejando de ser una variable de cola para convertirse en el nuevo escenario base.",
        "Tecnología":          "Las aseguradoras que no integren esta tecnología en su hoja de ruta operativa en los próximos 18 meses arriesgan una brecha de eficiencia difícil de cerrar. La ventana de adopción temprana es estrecha.",
        "Fraude":              "La presión sobre los márgenes técnicos por fraude exige inversión prioritaria en analítica avanzada y verificación digital. Las aseguradoras que dependan de procesos manuales serán las primeras en notar el impacto.",
        "Vida y Salud":        "El segmento salud sigue siendo el de mayor crecimiento y el más disputado. Los actores sin oferta digital o sin acuerdo con plataformas de distribución perderán cuota frente a las insurtechs especializadas.",
        "Automóvil":           "La convergencia entre movilidad conectada, vehículos eléctricos y nuevos modelos de uso está redefiniendo los fundamentos del seguro de auto. Las carteras sin segmentación telemática ya acumulan desventaja técnica.",
        "Embebido":            "La distribución embebida está creciendo a doble dígito en todos los mercados relevantes. Los canales tradicionales que no desarrollen acuerdos de integración perderán visibilidad justo en el momento de la decisión de compra.",
        "Liderazgo":           "Los cambios en la cúpula directiva suelen anticipar giros estratégicos que se materializan en los 6 a 18 meses siguientes. Vale la pena seguir de cerca la evolución del discurso público de la nueva dirección.",
    }
    base_closing = fwd_map.get(label, "Este movimiento merece seguimiento desde las perspectivas de riesgo técnico, regulatorio y competitivo a corto plazo.")

    # Extract the lead entity: first meaningful capitalized word(s) from the title
    _STOP_ENT = {"The","A","An","In","On","To","For","Of","Is","Are","Was","With","From",
                 "Its","At","By","And","Or","But","How","Why","New","More","US","UK","EU",
                 "Report","Study","Survey","According","Source","Update","Analysis","New"}
    # Words that look capitalized in a title but aren't proper nouns / company names
    _COMMON_TITLE = {"Motor","Finance","Scandal","Bond","Bonds","Insurance","Market","Industry",
                     "Bank","Fund","Capital","Risk","Model","Pool","Channel","Platform","Commission",
                     "Authority","Agency","Scheme","Proposal","Law","Act","Rule","Regulation",
                     "Cost","Lenders","Loans","Firms","Companies","Groups","Plans","Deal","Deals"}
    _ent_single = re.findall(r'\b([A-Z][A-Za-z]{2,}(?:\s+[A-Z][A-Za-z]{2,})?)\b',
                              title_orig or title_es or "")
    entity_words = [e for e in _ent_single
                    if e.split()[0] not in _STOP_ENT and e.split()[0] not in _COMMON_TITLE]
    lead_entity = entity_words[0] if entity_words else source

    # Build personalised closing — avoid double "para" prefix + closing
    entity_prefixes = {
        "Regulación":          f"En el caso de {lead_entity},",
        "M&A":                 f"La operación de {lead_entity} es una señal más de que",
        "Inversión":           f"El movimiento de {lead_entity} anticipa que",
        "Clima & Catástrofes": f"La iniciativa de {lead_entity} refleja que",
        "Tecnología":          f"Con {lead_entity} como referente,",
        "Fraude":              f"El caso de {lead_entity} ilustra que",
        "Vida y Salud":        f"El avance de {lead_entity} confirma que",
        "Automóvil":           f"La apuesta de {lead_entity} demuestra que",
        "Embebido":            f"El modelo de {lead_entity} anticipa que",
        "Liderazgo":           f"Tras el cambio en {lead_entity},",
    }
    prefix = entity_prefixes.get(label, f"{lead_entity}:")
    closing_joined = base_closing[0].lower() + base_closing[1:] if base_closing else base_closing
    personalised_closing = f"{prefix} {closing_joined}"

    # Try to prepend a unique key fact before the closing
    specific = _extract_key_fact(title_orig or title_es, summary_clean)
    # Only use if it doesn't duplicate the intro opener and isn't just the title
    title_norm = (title_orig or title_es or "")[:80].lower()
    if (specific
            and specific.strip()[:50].lower() not in intro[:100].lower()
            and specific.strip()[:40].lower() not in title_norm):
        analysis = specific + " " + personalised_closing
    else:
        # Try unused summary sentence
        all_sents = [s.strip() for s in re.split(r'(?<=[.!?])\s+', summary_clean)
                     if len(s.strip()) > 40 and re.match(r'^[A-ZÁÉÍÓÚ"\d]', s.strip())]
        unused = [s for s in all_sents[2:] if s[:40].lower() not in intro.lower()]
        if unused:
            raw_extra = unused[0]
            translated_extra = _translate_to_es(raw_extra[:400])
            time.sleep(0.2)
            extra = translated_extra.strip() if (translated_extra and translated_extra.strip() != raw_extra[:400].strip()) else raw_extra
            analysis = extra + " " + personalised_closing
        else:
            analysis = personalised_closing

    return {"title": title_es, "intro": intro, "analysis": analysis}


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

    # Compute reading time
    all_words = [day_intro_text] + [
        e.get("intro","") + " " + e.get("analysis","") for e in editorials
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
            img_html = f'<div style="margin:0 0 20px"><img src="{image}" alt="" width="100%" style="display:block;border-radius:8px;max-height:260px;object-fit:cover" /></div>'

        sig_icon = a.get("signal_icon", "⚡")
        signal_badge = ""
        if signal_label and score >= 18 and signal_label != display_cat:
            signal_badge = (
                f' <span style="font-size:10px;font-weight:700;color:#f59e0b;'
                f'background:#f59e0b22;border:1px solid #f59e0b44;border-radius:4px;'
                f'padding:1px 7px">{sig_icon} {signal_label}</span>'
            )
        elif display_cat == signal_label and signal_label:
            icon = sig_icon

        analysis = ed.get("analysis", "")

        articles_html += f"""
        <!-- Article {i} -->
        <tr><td style="padding:28px 0 0;border-top:1px solid #3a2e1e">
          <p style="margin:0 0 8px;font-size:11px;font-weight:800;color:#c0392b;
                    text-transform:uppercase;letter-spacing:1px">
            {i}. {icon} {display_cat}{signal_badge}
          </p>
          <h2 style="margin:0 0 18px;font-size:21px;font-weight:800;line-height:1.3;color:#f5f0e8">
            {title}
          </h2>
          {img_html}
          <p style="margin:0 0 16px;font-size:15px;line-height:1.8;color:#c8bfaf">
            {ed['intro']}
          </p>
          <p style="margin:0 0 20px;font-size:14px;line-height:1.8;color:#a89880;border-left:2px solid #3a2e1e;padding-left:14px">
            {analysis}
          </p>
          <p style="margin:0">
            <a href="{url}" style="font-size:13px;color:#d4a857;font-weight:600;text-decoration:none">
              Leer artículo completo en {src} →
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
