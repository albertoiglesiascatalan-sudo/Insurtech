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


# ── AI editorial per article ──────────────────────────────────────────────────
def _ai_editorial(article: dict) -> dict:
    """
    Returns {"title": str, "intro": str, "bullets": [str, str, str]} always in Spanish.
    Uses OpenAI if available (translate + editorial); falls back to free translation + templates.
    """
    # Always prefer the Spanish title; fall back to original
    title_es   = article.get("title", "")
    title_orig = article.get("title_original", title_es)
    summary    = article.get("summary", "")
    source     = article.get("source", "")
    why        = article.get("why_matters", "")   # always in Spanish
    deal       = article.get("deal")
    cat        = article.get("category", "General")
    signal_label = article.get("signal_label", "")

    # Best text to feed AI: use Spanish summary if available, else original title
    summary_for_ai = summary if summary else title_orig

    if _openai_client:
        try:
            resp = _openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": (
                    "Eres el redactor jefe de InsurTech Intelligence, newsletter ejecutiva "
                    "para directivos del sector asegurador en España y Latinoamérica. "
                    "Responde SIEMPRE en español, independientemente del idioma del artículo.\n\n"
                    "Escribe:\n"
                    "0. El título traducido al español (si ya está en español, mantenlo).\n"
                    "1. Un párrafo de contexto (2-3 frases): qué ha pasado, por qué importa "
                    "al sector asegurador y qué implica estratégicamente.\n"
                    "2. Exactamente 3 puntos clave formato 'Término: explicación' "
                    "(máx 25 palabras cada uno). Directo, ejecutivo.\n\n"
                    "Responde SOLO con JSON: "
                    '{\"title_es\": \"...\", \"intro\": \"...\", \"bullets\": [\"...\", \"...\", \"...\"]}\n\n'
                    f"Título original: {title_orig}\n"
                    f"Título en español: {title_es}\n"
                    f"Fuente: {source}\n"
                    f"Categoría: {cat}\n"
                    f"Contenido: {summary_for_ai[:600]}"
                )}],
                max_tokens=400,
                temperature=0.4,
            )
            raw = resp.choices[0].message.content.strip()
            # Strip possible markdown code fences
            raw = re.sub(r'^```json\s*|\s*```$', '', raw, flags=re.MULTILINE).strip()
            data = json.loads(raw)
            intro     = data.get("intro", "")
            bullets   = data.get("bullets", [])
            title_out = data.get("title_es", title_es) or title_es
            if intro and len(bullets) >= 2:
                return {"title": title_out, "intro": intro, "bullets": bullets[:3]}
        except Exception as e:
            log.debug(f"OpenAI newsletter editorial error: {e}")

    # ── Spanish-native extractive fallback ────────────────────────────────────
    # Translate title if needed (MyMemory free API, only for non-Spanish titles)
    if not _is_spanish_quick(title_es) and not _is_spanish_quick(title_orig):
        title_es = _translate_to_es(title_orig or title_es)
        time.sleep(0.3)  # avoid rate limiting (5 articles × 0.3s = 1.5s total)

    # Use Spanish summary if it exists and is in Spanish; otherwise build from metadata
    if summary and _is_spanish(summary):
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', summary) if len(s.strip()) > 30]
        intro = " ".join(sentences[:2]) if sentences else summary[:220]
    else:
        # Build intro from guaranteed-Spanish fields
        cat_phrases = {
            "Regulación":   f"{source} ha publicado nueva normativa que afecta al sector asegurador.",
            "Inversión":    f"Nueva operación de inversión detectada en el ecosistema insurtech, publicada por {source}.",
            "Tecnología":   f"{source} informa sobre un avance tecnológico con impacto en el sector seguros.",
            "Catástrofes":  f"Alerta de riesgo catastrófico reportada por {source} con implicaciones para el mercado asegurador.",
            "Fraude":       f"{source} publica información relevante sobre detección o prevención del fraude asegurador.",
            "Vida y Salud": f"Novedad en el segmento de vida y salud publicada por {source}.",
            "Automóvil":    f"Actualización del mercado de seguro de automóvil según {source}.",
            "Embebido":     f"Avance en seguros embebidos o distribución alternativa, según {source}.",
        }
        base = cat_phrases.get(cat, f"{source} publica una noticia relevante para el sector asegurador.")
        if why:
            intro = f"{base} {why}"
        else:
            intro = base

    bullets = []
    if why:
        bullets.append(f"Relevancia: {why}")
    if deal and deal.get("amount_str") and deal["amount_str"] != "—":
        rnd = f" ({deal['round']})" if deal.get("round") and deal["round"] != "—" else ""
        bullets.append(f"Operación detectada: {deal['amount_str']}{rnd}.")
    if signal_label:
        bullets.append(f"Tipo de señal: {signal_label} — impacto clasificado como alto por nuestro sistema de inteligencia.")
    if source:
        bullets.append(f"Publicado por {source}, fuente de referencia en el sector.")
    # Fill to 3
    while len(bullets) < 3:
        bullets.append("Consulta el artículo completo para más contexto y datos.")

    return {"title": title_es, "intro": intro, "bullets": bullets[:3]}


# ── Intro editorial del día ────────────────────────────────────────────────────
def _day_intro(articles_today: list, articles_week: list) -> str:
    """
    Generates the opening editorial paragraph.
    Uses OpenAI if available; otherwise builds it from stats.
    """
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
                    "Eres el redactor jefe de InsurTech Intelligence. Escribe en español "
                    "el párrafo de apertura de la newsletter de hoy (3-4 frases). "
                    "Estilo: directo, ejecutivo, periodístico. Menciona los temas principales "
                    "del día y el número de artículos analizados. "
                    "NO uses 'Estimados lectores' ni saludos formales — empieza con el fondo.\n\n"
                    f"Artículos analizados hoy: {n_today}\n"
                    f"Señales detectadas: {n_signals}\n"
                    f"Temas principales: {', '.join(top_themes) if top_themes else 'General'}\n"
                    f"Titulares de hoy: {titles_sample}"
                )}],
                max_tokens=200,
                temperature=0.5,
            )
            intro = resp.choices[0].message.content.strip()
            if intro:
                return intro
        except Exception as e:
            log.debug(f"OpenAI day intro error: {e}")

    # Extractive fallback
    themes_str = " · ".join(top_themes) if top_themes else "mercado asegurador"
    parts = [f"Hoy hemos analizado <strong>{n_today} artículos</strong> de más de 40 fuentes globales."]
    if n_signals:
        parts.append(f"Detectamos <strong>{n_signals} señales</strong> de alta relevancia.")
    if n_inv:
        parts.append(f"Esta semana se han registrado <strong>{n_inv} operaciones de inversión</strong>.")
    if n_reg:
        parts.append(f"<strong>{n_reg} noticias regulatorias</strong> merecen atención inmediata.")
    parts.append(f"Las cinco historias que no puedes perderte hoy, ordenadas por impacto: {themes_str}.")
    return " ".join(parts)


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
    top5 = pool[:5]

    # Week articles for stats
    week = [a for a in articles if _try_after(a.get("published_at",""), cutoff7)]

    # Build day intro
    day_intro_text = _day_intro(pool, week)

    # Build editorial per article
    editorials = [_ai_editorial(a) for a in top5]

    # Compute reading time
    all_words = [day_intro_text] + [
        e["intro"] + " ".join(e["bullets"]) for e in editorials
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

        bullets_html = "".join(
            f'<li style="margin-bottom:10px;line-height:1.55;color:#c8bfaf">{b}</li>'
            for b in ed["bullets"]
        )

        signal_badge = ""
        if signal_label and score >= 18:
            sig_icon = a.get("signal_icon", "⚡")
            signal_badge = (
                f'<span style="display:inline-block;font-size:10px;font-weight:700;'
                f'color:#f59e0b;background:#f59e0b22;border:1px solid #f59e0b44;'
                f'border-radius:4px;padding:1px 7px;margin-left:8px;vertical-align:middle">'
                f'{sig_icon} {signal_label}</span>'
            )

        articles_html += f"""
        <!-- Article {i} -->
        <tr><td style="padding:28px 0 0;border-top:1px solid #3a2e1e">
          <p style="margin:0 0 6px;font-size:11px;font-weight:800;color:#c0392b;
                    text-transform:uppercase;letter-spacing:1px">
            {i}. {icon} {cat}{signal_badge}
          </p>
          <h2 style="margin:0 0 14px;font-size:22px;font-weight:800;line-height:1.3;color:#f5f0e8">
            <a href="{url}" style="color:#f5f0e8;text-decoration:none">{title}</a>
          </h2>
          {img_html}
          <p style="margin:0 0 16px;font-size:15px;line-height:1.65;color:#c8bfaf">
            {ed['intro']}
          </p>
          <ol style="margin:0 0 16px;padding-left:20px;font-size:14px">
            {bullets_html}
          </ol>
          <p style="margin:0;font-size:12px;color:#6b5e4a">
            Fuente: <a href="{url}" style="color:#d4a857;text-decoration:none">{src}</a>
          </p>
        </td></tr>"""

    # ── Full HTML ────────────────────────────────────────────────────────────────
    html = f"""<!DOCTYPE html>
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
</table>
</body>
</html>"""

    path = os.path.join(DOCS_DIR, "newsletter.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    ai_note = "con IA" if _openai_client else "extractivo"
    log.info(f"Newsletter generated ({ai_note}): {path} — {len(top5)} stories, {words} words")
    print(f"Newsletter generated: {path} ({len(top5)} stories · {read_min} min · {ai_note})")


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
