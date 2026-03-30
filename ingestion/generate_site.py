"""Generates static HTML + RSS feed for GitHub Pages from articles list."""
import os
import json
from datetime import datetime, timezone, timedelta
from collections import Counter

from xml.sax.saxutils import escape as xml_escape
from signal_engine import detect_trends, detect_incumbents

DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "docs")
SITE_URL = "https://albertoiglesiascatalan-sudo.github.io/Insurtech"

CATEGORIES = [
    "Tecnología", "Regulación", "Inversión", "Vida y Salud",
    "Automóvil", "Catástrofes", "Fraude", "Embebido", "General",
]

IBERO_SOURCES = {
    "INESE", "Actualidad Aseguradora", "Aseguranza",
    "El Economista Seguros", "Fintech.es", "iupana (Latam Fintech)", "Latin Insurance",
}


def _date(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).strftime("%d %b %Y")
    except Exception:
        return ""


def _is_new(iso: str, hours: int = 24) -> bool:
    try:
        pub = datetime.fromisoformat(iso)
        if pub.tzinfo is None:
            pub = pub.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - pub) < timedelta(hours=hours)
    except Exception:
        return False


def _read_minutes(text: str) -> int:
    words = len(text.split())
    return max(1, round(words / 200))


def _share_urls(title: str, url: str) -> tuple:
    import urllib.parse
    t = urllib.parse.quote_plus(title[:100])
    u = urllib.parse.quote_plus(url)
    twitter = f"https://twitter.com/intent/tweet?text={t}&url={u}"
    linkedin = f"https://www.linkedin.com/sharing/share-offsite/?url={u}"
    return twitter, linkedin


def _group_label(iso: str) -> str:
    try:
        pub = datetime.fromisoformat(iso)
        if pub.tzinfo is None:
            pub = pub.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - pub
        if delta.total_seconds() < 86400:
            return "Hoy"
        elif delta.days == 1:
            return "Ayer"
        elif delta.days < 7:
            return "Esta semana"
        else:
            return "Anteriores"
    except Exception:
        return "Anteriores"


def _cards_grouped(articles: list) -> str:
    parts = []
    current_group = None
    for a in articles:
        group = _group_label(a.get("published_at", ""))
        if group != current_group:
            current_group = group
            parts.append(f'<div class="time-sep" data-group="{group}"><span>{group}</span></div>')
        parts.append(_card(a))
    return "\n".join(parts)


def _rel_date(iso: str) -> tuple:
    """Returns (relative_label, absolute_for_tooltip)."""
    try:
        pub = datetime.fromisoformat(iso)
        if pub.tzinfo is None:
            pub = pub.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - pub
        abs_date = pub.strftime("%d %b %Y %H:%M")
        secs = delta.total_seconds()
        if secs < 60:
            return "ahora mismo", abs_date
        elif secs < 3600:
            return f"hace {int(secs/60)} min", abs_date
        elif secs < 86400:
            return f"hace {int(secs/3600)}h", abs_date
        elif delta.days == 1:
            return "ayer", abs_date
        elif delta.days < 7:
            return f"hace {delta.days} días", abs_date
        else:
            return pub.strftime("%d %b"), abs_date
    except Exception:
        return "", ""


def _card(a: dict, featured: bool = False) -> str:
    category  = a.get("category", "General")
    summary   = a.get("summary", "")
    image_url = a.get("image_url", "")
    read_min  = _read_minutes(a["title"] + " " + summary)
    rel_date, abs_date = _rel_date(a.get("published_at", ""))
    twitter_url, linkedin_url = _share_urls(a["title"], a["url"])
    searchable = f"{a['title']} {summary} {a['source']}".lower().replace('"', '')
    article_id = a.get("id", "")
    region = "ibero" if a.get("source", "") in IBERO_SOURCES else "global"

    # Badges
    badges = []
    if _is_new(a.get("published_at", "")):
        badges.append('<span class="badge-new">Nuevo</span>')
    if a.get("is_signal"):
        icon = a.get("signal_icon", "⚡")
        label = a.get("signal_label", "Señal")
        badges.append(f'<span class="badge-signal" title="Señal detectada: {label}">{icon} {label}</span>')
    if a.get("amplified"):
        badges.append('<span class="badge-amp" title="Cubierto por 3+ fuentes">🔥 Tendencia</span>')
    if a.get("deal") and a["deal"].get("amount_str"):
        d = a["deal"]
        deal_txt = d["amount_str"]
        if d.get("round") and d["round"] != "—":
            deal_txt += f' · {d["round"]}'
        badges.append(f'<span class="badge-deal">💰 {deal_txt}</span>')

    badges_html = " ".join(badges)
    why_html = f'<p class="card-why"><span class="why-icon">💡</span>{a["why_matters"]}</p>' if a.get("why_matters") and a.get("is_signal") else ""
    img_html  = f'<a href="{a["url"]}" target="_blank" rel="noopener"><img class="card-image" src="{image_url}" alt="" loading="lazy" onerror="this.parentElement.style.display=\'none\'"></a>' if image_url else ""
    extra_class = " card-featured" if featured else (" card-signal" if a.get("is_signal") else "")

    try:
        from urllib.parse import urlparse as _up
        _domain = _up(a["url"]).netloc
        favicon_html = f'<img class="source-favicon" src="https://www.google.com/s2/favicons?domain={_domain}&sz=16" alt="" loading="lazy">'
    except Exception:
        favicon_html = ""

    signal_flag = "1" if a.get("is_signal") else "0"
    return f"""
    <article class="card{extra_class}" data-category="{category}" data-region="{region}" data-search="{searchable}" data-id="{article_id}" data-url="{a['url']}" data-signal="{signal_flag}">
      {img_html}
      <div class="card-meta">
        {favicon_html}<span class="card-source">{a['source']}</span>
        <span class="card-dot">·</span>
        <span class="card-date" title="{abs_date}">{rel_date}</span>
        <span class="card-dot">·</span>
        <span class="card-read">{read_min} min</span>
        {badges_html}
        <span class="card-tag">{category}</span>
      </div>
      <h2 class="card-title">
        <a href="{a['url']}" target="_blank" rel="noopener">{a['title']}</a>
      </h2>
      {"<p class='card-summary'>" + summary + "</p>" if summary else ""}
      {why_html}
      <div class="card-actions">
        <a href="{a['url']}" target="_blank" rel="noopener" class="card-link">Leer artículo →</a>
        <div class="card-share">
          <a href="{twitter_url}" target="_blank" rel="noopener" class="share-btn share-x" title="Compartir en X">𝕏</a>
          <a href="{linkedin_url}" target="_blank" rel="noopener" class="share-btn share-li" title="Compartir en LinkedIn">in</a>
          <button class="share-btn save-btn" data-id="{article_id}" title="Guardar artículo">🔖</button>
        </div>
      </div>
    </article>"""


def generate_feed(articles: list):
    """Generate RSS feed XML with images."""
    now_rfc = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    items = []
    for a in articles[:50]:
        try:
            pub = datetime.fromisoformat(a["published_at"])
            if pub.tzinfo is None:
                pub = pub.replace(tzinfo=timezone.utc)
            pub_rfc = pub.strftime("%a, %d %b %Y %H:%M:%S +0000")
        except Exception:
            pub_rfc = now_rfc
        desc = xml_escape(a.get("summary") or a["title"])
        enclosure = ""
        if a.get("image_url"):
            enclosure = f'    <enclosure url="{xml_escape(a["image_url"])}" type="image/jpeg" length="0"/>\n'
        items.append(f"""  <item>
    <title>{xml_escape(a['title'])}</title>
    <link>{xml_escape(a['url'])}</link>
    <description>{desc}</description>
    <pubDate>{pub_rfc}</pubDate>
    <guid>{xml_escape(a['url'])}</guid>
    <category>{xml_escape(a.get('category', 'General'))}</category>
{enclosure}  </item>""")

    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:media="http://search.yahoo.com/mrss/">
<channel>
  <title>InsurTech Intelligence</title>
  <link>{SITE_URL}</link>
  <description>Noticias globales de insurtech, actualizadas cada 6 horas.</description>
  <language>es</language>
  <lastBuildDate>{now_rfc}</lastBuildDate>
  <atom:link href="{SITE_URL}/feed.xml" rel="self" type="application/rss+xml"/>
{chr(10).join(items)}
</channel>
</rss>"""
    feed_path = os.path.join(DOCS_DIR, "feed.xml")
    with open(feed_path, "w", encoding="utf-8") as f:
        f.write(feed)
    print(f"RSS feed generated: {feed_path}")


def generate_sitemap(articles: list):
    """Generate sitemap.xml for SEO."""
    now_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    urls = [f"""  <url>
    <loc>{SITE_URL}/</loc>
    <lastmod>{now_date}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>"""]
    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>"""
    sitemap_path = os.path.join(DOCS_DIR, "sitemap.xml")
    with open(sitemap_path, "w", encoding="utf-8") as f:
        f.write(sitemap)
    print(f"Sitemap generated: {sitemap_path}")


def _daily_briefing(articles: list) -> str:
    """Executive daily briefing: groups today's signals by type, one line each."""
    from collections import defaultdict, Counter as _Counter

    now = datetime.now(timezone.utc)
    cutoff_24h = now - timedelta(hours=24)

    today_all = []
    for a in articles:
        try:
            pub = datetime.fromisoformat(a.get("published_at", ""))
            if pub.tzinfo is None:
                pub = pub.replace(tzinfo=timezone.utc)
            if pub >= cutoff_24h:
                today_all.append(a)
        except Exception:
            pass

    if not today_all:
        return ""

    # Group signals by label, sorted by score within group
    groups: dict = defaultdict(list)
    for a in today_all:
        if a.get("signal_label"):
            groups[a["signal_label"]].append(a)

    # Sort each group by score descending
    for label in groups:
        groups[label].sort(key=lambda x: x.get("signal_score", 0), reverse=True)

    # Order groups by max score of their top article
    ordered = sorted(groups.items(), key=lambda kv: kv[1][0].get("signal_score", 0), reverse=True)

    # Stats
    total_today   = len(today_all)
    signals_today = sum(1 for a in today_all if a.get("is_signal"))
    reg_sources   = sum(1 for a in today_all if a.get("source", "") in ("EIOPA", "FCA News", "FSB"))
    deals_today   = sum(1 for a in today_all if a.get("deal") and a["deal"].get("amount_str"))

    # Build lines
    lines_html = ""
    for label, arts in ordered[:6]:
        icon = arts[0].get("signal_icon", "⚡")
        # Take titles of top 2 articles, shortened to ~55 chars
        titles = []
        for a in arts[:2]:
            t = a.get("title", "")
            titles.append((t[:55] + "…") if len(t) > 55 else t)
        titles_str = " · ".join(titles)
        count_badge = f'<span class="brief-count">{len(arts)}</span>' if len(arts) > 1 else ''
        lines_html += f"""
        <div class="brief-line">
          <span class="brief-icon">{icon}</span>
          <span class="brief-label">{label}{count_badge}</span>
          <span class="brief-titles">{titles_str}</span>
        </div>"""

    if not lines_html:
        # No signals yet today — show top articles by score
        top = sorted(today_all, key=lambda x: x.get("signal_score", 0), reverse=True)[:4]
        for a in top:
            t = a.get("title", "")
            t_short = (t[:65] + "…") if len(t) > 65 else t
            lines_html += f"""
        <div class="brief-line">
          <span class="brief-icon">📰</span>
          <span class="brief-label">{a.get("source","")}</span>
          <span class="brief-titles">{t_short}</span>
        </div>"""

    # Stats footer — absorbs thermometer + incumbent data
    week_cutoff = now - timedelta(days=7)
    week_all = [a for a in articles if _is_new(a.get("published_at", ""), 168)]
    week_inv = sum(1 for a in week_all if a.get("category") == "Inversión")
    week_reg = sum(1 for a in week_all if a.get("category") == "Regulación")

    inc_data = detect_incumbents(articles, window_days=7)
    inc_top2 = [f"{x['name']} ×{x['count']}" for x in inc_data[:2]]

    stat_parts = [f"<strong>{total_today}</strong> hoy"]
    if signals_today:
        stat_parts.append(f"<strong>{signals_today}</strong> señales")
    if deals_today:
        stat_parts.append(f"<strong>{deals_today}</strong> deals")
    if week_inv:
        stat_parts.append(f"<strong>{week_inv}</strong> inversiones esta semana")
    if week_reg:
        stat_parts.append(f"<strong>{week_reg}</strong> regulación esta semana")
    if inc_top2:
        stat_parts.append("más mencionados: " + " · ".join(inc_top2))
    stats_str = " · ".join(stat_parts)

    # Day label
    day_names = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"]
    day_label = day_names[now.weekday()]
    date_str  = now.strftime(f"{day_label} %-d %b %Y").lower()

    # Next refresh countdown (runs every 6h from midnight UTC)
    next_refresh_h = 6 - (now.hour % 6)
    next_refresh_m = 60 - now.minute if now.minute > 0 else 0
    if next_refresh_m == 60:
        next_refresh_m = 0
    else:
        next_refresh_h -= 1
    refresh_str = f"{next_refresh_h}h {next_refresh_m:02d}min" if next_refresh_h > 0 else f"{next_refresh_m}min"

    return f"""
  <section class="brief-section">
    <div class="brief-header">
      <div class="brief-title-row">
        <span class="brief-badge">📋 BRIEFING</span>
        <span class="brief-date">{date_str}</span>
        <span class="brief-refresh" title="Próxima actualización automática">↻ en {refresh_str}</span>
      </div>
    </div>
    <div class="brief-body">{lines_html}
    </div>
    <div class="brief-stats">📊 {stats_str}</div>
  </section>"""


def _radar_section(articles: list) -> str:
    """Top signals of the week — highest scored articles."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    signals = []
    for a in articles:
        if not a.get("is_signal"):
            continue
        try:
            pub = datetime.fromisoformat(a.get("published_at", ""))
            if pub.tzinfo is None:
                pub = pub.replace(tzinfo=timezone.utc)
            if pub < cutoff:
                continue
        except Exception:
            pass
        signals.append(a)

    signals.sort(key=lambda x: x.get("signal_score", 0), reverse=True)
    signals = signals[:6]
    if not signals:
        return ""

    rows = ""
    for a in signals:
        icon  = a.get("signal_icon", "⚡")
        label = a.get("signal_label", "Señal")
        score = a.get("signal_score", 0)
        rel, abs_d = _rel_date(a.get("published_at", ""))
        amp_badge = ' <span class="radar-amp">🔥</span>' if a.get("amplified") else ""
        deal = a.get("deal")
        deal_badge = f' <span class="radar-deal">💰 {deal["amount_str"]}</span>' if deal and deal.get("amount_str") else ""
        rows += f"""
      <a href="{a['url']}" target="_blank" rel="noopener" class="radar-row">
        <span class="radar-icon" title="{label}">{icon}</span>
        <div class="radar-content">
          <span class="radar-title">{a['title']}</span>
          <span class="radar-meta">{a['source']} · {rel}{amp_badge}{deal_badge}</span>
          {"<span class='radar-why'>" + a['why_matters'] + "</span>" if a.get('why_matters') else ""}
        </div>
        <span class="radar-score" title="Puntuación de señal">{score}</span>
      </a>"""

    # Build deal column (reuse deal logic inline)
    deal_cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    deals = []
    for a in articles:
        if not a.get("deal"):
            continue
        d = a["deal"]
        if not d.get("amount_str") and not d.get("round"):
            continue
        try:
            pub = datetime.fromisoformat(a.get("published_at", ""))
            if pub.tzinfo is None:
                pub = pub.replace(tzinfo=timezone.utc)
            if pub >= deal_cutoff:
                deals.append(a)
        except Exception:
            pass
    deals.sort(key=lambda x: x["deal"].get("amount_m", 0), reverse=True)
    deals = deals[:6]

    deal_col = ""
    if deals:
        deal_rows = ""
        for a in deals:
            d = a["deal"]
            rel, _ = _rel_date(a.get("published_at", ""))
            rnd = f'<span class="deal-round">{d["round"]}</span>' if d.get("round") and d["round"] != "—" else ""
            t = a.get("title", "")
            t_short = (t[:52] + "…") if len(t) > 52 else t
            deal_rows += f"""
        <a href="{a['url']}" target="_blank" rel="noopener" class="deal-row2">
          <span class="deal-amount">{d['amount_str']}</span>{rnd}
          <span class="deal-title2">{t_short}</span>
        </a>"""
        deal_col = f"""
    <div class="intel-col">
      <div class="intel-col-header">
        <span class="intel-col-title">💰 Deals · 30 días</span>
      </div>
      <div class="intel-col-body">{deal_rows}
      </div>
    </div>"""

    # Layout: 2 cols if deals exist, else 1 col full-width
    grid_class = "intel-grid-2" if deal_col else "intel-grid-1"

    return f"""
  <section class="intel-section">
    <div class="{grid_class}">
      <div class="intel-col">
        <div class="intel-col-header">
          <span class="intel-col-title">⚡ Señales · 7 días</span>
          <span class="intel-col-sub">por relevancia</span>
        </div>
        <div class="intel-col-body">{rows}
        </div>
      </div>{deal_col}
    </div>
  </section>"""


def _trends_section(articles: list) -> str:
    """Trending topics this week vs last 4 weeks.
    Hidden if all results are 'Nuevo' — no real baseline to compare against."""
    trends = detect_trends(articles)
    if not trends:
        return ""

    # Need at least one real % change (not just "Nuevo") to be meaningful
    real_changes = [t for t in trends if t["change_pct"] != 999]
    if not real_changes:
        return ""  # Not enough historical data yet

    pills = ""
    for t in trends:
        if t["change_pct"] == 999:
            label = f'{t["topic"]} <span class="trend-badge new">Nuevo</span>'
        elif t["change_pct"] > 0:
            label = f'{t["topic"]} <span class="trend-badge up">↑ {t["change_pct"]}%</span>'
        else:
            continue
        pills += f'<span class="trend-pill">{label} <small>{t["this_week"]} art.</small></span>'

    if not pills:
        return ""

    return f"""
  <section class="trends-section">
    <span class="trends-label">📈 Esta semana se habla más de:</span>
    <div class="trends-pills">{pills}</div>
  </section>"""


def _deal_tracker(articles: list) -> str:
    return ""  # Deals now shown inside _radar_section 2-col layout


def _thermometer(articles: list) -> str:
    return ""  # Stats absorbed into _daily_briefing footer


def _regulatory_alert(articles: list) -> str:
    """Prominent banner if EIOPA/FCA/FSB published a high-impact article this week."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    top = None
    for a in articles:
        if a.get("source", "") not in ("EIOPA", "FCA News", "FSB"):
            continue
        if a.get("signal_score", 0) < 20:
            continue
        try:
            pub = datetime.fromisoformat(a.get("published_at", ""))
            if pub.tzinfo is None:
                pub = pub.replace(tzinfo=timezone.utc)
            if pub >= cutoff:
                if top is None or a.get("signal_score", 0) > top.get("signal_score", 0):
                    top = a
        except Exception:
            pass
    if not top:
        return ""
    rel, _ = _rel_date(top.get("published_at", ""))
    src = top.get("source", "")
    src_icons = {"EIOPA": "🇪🇺", "FCA News": "🇬🇧", "FSB": "🌐"}
    icon = src_icons.get(src, "⚖️")
    why = top.get("why_matters", "")
    return f"""
  <div class="reg-alert">
    <div class="reg-alert-inner">
      <span class="reg-alert-icon">{icon}</span>
      <div class="reg-alert-body">
        <span class="reg-alert-label">⚖️ Alerta Regulatoria · {src}</span>
        <a href="{top['url']}" target="_blank" rel="noopener" class="reg-alert-title">{top['title']}</a>
        {f'<span class="reg-alert-why">{why}</span>' if why else ''}
      </div>
      <span class="reg-alert-meta">{rel}</span>
    </div>
  </div>"""


def _incumbent_tracker(articles: list) -> str:
    return ""  # Incumbent data absorbed into _daily_briefing footer stats


def _startup_card(articles: list) -> str:
    return ""  # Removed: selection criterion was unreliable


def generate_digest(articles: list):
    """Generate a weekly HTML digest (docs/digest.html) ready for Buttondown or email."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    signals = [
        a for a in articles
        if a.get("is_signal") and _is_new(a.get("published_at", ""), 168)
    ]
    signals.sort(key=lambda x: x.get("signal_score", 0), reverse=True)
    top5 = signals[:5]

    items_html = ""
    for i, a in enumerate(top5, 1):
        icon  = a.get("signal_icon", "⚡")
        label = a.get("signal_label", "Señal")
        summary = a.get("summary", "")
        why     = a.get("why_matters", "")
        deal    = a.get("deal")
        deal_str = f'<span style="color:#16a34a;font-weight:700">{deal["amount_str"]}</span>' if deal and deal.get("amount_str") else ""
        items_html += f"""
    <tr><td style="padding:20px 0;border-bottom:1px solid #e2e8f0;">
      <p style="margin:0 0 4px;font-size:11px;text-transform:uppercase;letter-spacing:.5px;color:#64748b;font-weight:700">{i}. {icon} {label} {deal_str}</p>
      <p style="margin:0 0 6px;font-size:16px;font-weight:700;line-height:1.4">
        <a href="{a['url']}" style="color:#1a1a2e;text-decoration:none">{a['title']}</a>
      </p>
      {f'<p style="margin:0 0 6px;font-size:13px;color:#4a5568;line-height:1.5">{summary}</p>' if summary else ''}
      {f'<p style="margin:0;font-size:12px;color:#d97706">💡 {why}</p>' if why else ''}
      <p style="margin:6px 0 0;font-size:11px;color:#94a3b8">{a.get("source","")} · {_date(a.get("published_at",""))}</p>
    </td></tr>"""

    if not top5:
        items_html = '<tr><td style="padding:20px 0;color:#64748b">Sin señales relevantes esta semana.</td></tr>'

    week_date = datetime.now(timezone.utc).strftime("%d %b %Y")
    digest_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>InsurTech Intelligence · Digest Semanal {week_date}</title>
</head>
<body style="margin:0;padding:0;background:#f4f6f9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f4f6f9;padding:32px 16px">
    <tr><td>
      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:600px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;border:1px solid #e2e8f0">

        <!-- Header -->
        <tr><td style="background:#1a1a2e;padding:28px 32px;text-align:center">
          <p style="margin:0;font-size:22px;font-weight:700;color:#fff">InsurTech Intelligence</p>
          <p style="margin:6px 0 0;font-size:13px;color:#a0aec0">Digest Semanal · {week_date}</p>
        </td></tr>

        <!-- Intro -->
        <tr><td style="padding:24px 32px 8px">
          <p style="margin:0;font-size:14px;color:#4a5568;line-height:1.6">
            Esta semana hemos detectado <strong>{len(signals)} señales</strong> de alta relevancia en el sector insurtech.
            Aquí están las <strong>5 más importantes</strong>:
          </p>
        </td></tr>

        <!-- Signal items -->
        <tr><td style="padding:0 32px">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
            {items_html}
          </table>
        </td></tr>

        <!-- CTA -->
        <tr><td style="padding:24px 32px;text-align:center">
          <a href="{SITE_URL}" style="display:inline-block;padding:12px 28px;background:#4a6fa5;color:#fff;border-radius:24px;text-decoration:none;font-size:14px;font-weight:600">
            Ver todas las noticias →
          </a>
        </td></tr>

        <!-- Footer -->
        <tr><td style="padding:16px 32px 24px;border-top:1px solid #e2e8f0;text-align:center">
          <p style="margin:0;font-size:11px;color:#94a3b8">
            InsurTech Intelligence · Actualizado cada 6 horas ·
            <a href="{SITE_URL}/feed.xml" style="color:#4a6fa5">RSS</a>
          </p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""
    digest_path = os.path.join(DOCS_DIR, "digest.html")
    with open(digest_path, "w", encoding="utf-8") as f:
        f.write(digest_html)
    print(f"Digest generated: {digest_path} ({len(top5)} signals)")


def generate_site(articles: list):
    os.makedirs(DOCS_DIR, exist_ok=True)
    updated = datetime.utcnow().strftime("%d %b %Y · %H:%M UTC")
    new_count = sum(1 for a in articles if _is_new(a.get("published_at", "")))

    thermometer_html  = _thermometer(articles)
    startup_html      = _startup_card(articles)
    radar_html        = _radar_section(articles)
    trends_html       = _trends_section(articles)
    deals_html        = _deal_tracker(articles)
    reg_alert_html    = _regulatory_alert(articles)
    incumbent_html    = _incumbent_tracker(articles)
    briefing_html     = _daily_briefing(articles)
    ibero_count      = sum(1 for a in articles if a.get("source", "") in IBERO_SOURCES)
    signal_count     = sum(1 for a in articles if a.get("is_signal") and _is_new(a.get("published_at",""), 168))

    featured = articles[0] if articles else None
    rest     = articles[1:] if articles else []

    counts = Counter(a.get("category", "General") for a in articles)
    filter_buttons = '\n      '.join(
        f'<button class="filter-btn" data-filter="{c}">{c} <span class="count">{counts[c]}</span></button>'
        for c in CATEGORIES if counts[c] > 0
    )

    featured_html = _card(featured, featured=True) if featured else ""
    cards_html    = _cards_grouped(rest)

    og_image = next((a.get("image_url") for a in articles if a.get("image_url")), "")
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>InsurTech Intelligence — Noticias globales de insurtech</title>
  <meta name="description" content="Noticias globales de insurtech con resúmenes en español, actualizadas cada 6 horas. Tecnología, regulación, inversión y más." />
  <link rel="canonical" href="{SITE_URL}/" />
  <link rel="alternate" type="application/rss+xml" title="InsurTech Intelligence RSS" href="{SITE_URL}/feed.xml" />
  <link rel="sitemap" type="application/xml" href="{SITE_URL}/sitemap.xml" />
  <!-- Open Graph -->
  <meta property="og:type" content="website" />
  <meta property="og:url" content="{SITE_URL}/" />
  <meta property="og:title" content="InsurTech Intelligence" />
  <meta property="og:description" content="Noticias globales de insurtech con resúmenes en español, actualizadas cada 6 horas." />
  {"<meta property='og:image' content='" + og_image + "' />" if og_image else ""}
  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="InsurTech Intelligence" />
  <meta name="twitter:description" content="Noticias globales de insurtech con resúmenes en español, actualizadas cada 6 horas." />
  {"<meta name='twitter:image' content='" + og_image + "' />" if og_image else ""}
  <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --bg: #f4f6f9; --surface: #fff; --border: #e2e8f0;
      --text: #1a1a2e; --muted: #64748b; --accent: #4a6fa5;
      --header: #1a1a2e; --tag-bg: #eef2ff; --tag-color: #4a6fa5;
    }}
    @media (prefers-color-scheme: dark) {{
      :root {{
        --bg: #0f1117; --surface: #1a1d27; --border: #2d3148;
        --text: #e2e8f0; --muted: #8892a4; --accent: #7aa2d4;
        --header: #0d0f18; --tag-bg: #1e2340; --tag-color: #7aa2d4;
      }}
    }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; }}

    /* Header */
    header {{ background: var(--header); color: white; padding: 2rem 1rem 1.5rem; text-align: center; }}
    header h1 {{ font-size: 2rem; font-weight: 700; letter-spacing: -.5px; }}
    .header-sub {{ margin-top: .4rem; color: #a0aec0; font-size: .9rem; }}
    .header-stats {{ display: flex; justify-content: center; gap: 1.25rem; margin-top: .6rem; flex-wrap: wrap; }}
    .stat {{ font-size: .78rem; color: #718096; }}
    .stat strong {{ color: #a0aec0; }}
    .updated {{ font-size: .75rem; color: #4a5568; margin-top: .3rem; }}

    /* Translate */
    #google_translate_element {{ margin-top: 1rem; display: flex; justify-content: center; }}
    .goog-te-gadget {{ font-family: inherit !important; color: transparent !important; font-size: 0 !important; }}
    .goog-te-gadget-simple {{ background: transparent !important; border: 1.5px solid rgba(255,255,255,.2) !important; border-radius: 20px !important; padding: .35rem 1rem !important; font-size: .8rem !important; font-family: inherit !important; cursor: pointer !important; }}
    .goog-te-gadget-simple .goog-te-menu-value {{ color: #a0aec0 !important; }}
    .goog-te-gadget-simple .goog-te-menu-value span:first-child {{ color: white !important; font-weight: 500 !important; }}
    .goog-te-gadget-simple .goog-te-menu-value span[style] {{ color: rgba(255,255,255,.2) !important; }}
    .goog-te-gadget-simple img {{ display: none !important; }}
    .goog-te-banner-frame {{ display: none !important; }}
    body {{ top: 0 !important; }}

    /* Toolbar */
    .toolbar {{ max-width: 900px; margin: 1.5rem auto 0; padding: .75rem 1rem; display: flex; flex-direction: column; gap: .7rem; position: sticky; top: 0; z-index: 100; background: var(--bg); border-bottom: 1px solid var(--border); }}
    .search-row {{ display: flex; align-items: center; gap: .6rem; }}
    #search {{ flex: 1; padding: .5rem 1rem; border: 1.5px solid var(--border); border-radius: 20px; background: var(--surface); color: var(--text); font-size: .88rem; font-family: inherit; outline: none; transition: border-color .15s; }}
    #search:focus {{ border-color: var(--accent); }}
    #search::placeholder {{ color: var(--muted); }}
    .view-toggle {{ display: flex; gap: .3rem; }}
    .view-btn {{ background: var(--surface); border: 1.5px solid var(--border); border-radius: 8px; padding: .4rem .55rem; cursor: pointer; color: var(--muted); transition: all .15s; font-size: 1rem; line-height: 1; }}
    .view-btn.active {{ border-color: var(--accent); color: var(--accent); }}
    .filters {{ display: flex; flex-wrap: wrap; gap: .4rem; align-items: center; }}
    .filter-btn {{ background: var(--surface); border: 1.5px solid var(--border); border-radius: 20px; padding: .3rem .85rem; font-size: .8rem; font-weight: 500; color: var(--muted); cursor: pointer; transition: all .15s; display: flex; align-items: center; gap: .3rem; }}
    .filter-btn:hover {{ border-color: var(--accent); color: var(--accent); }}
    .filter-btn.active, .filter-btn.all-active {{ background: var(--accent); border-color: var(--accent); color: white; }}
    .filter-btn .count {{ font-size: .7rem; background: rgba(0,0,0,.08); border-radius: 10px; padding: .05rem .4rem; font-weight: 600; }}
    .filter-btn.active .count, .filter-btn.all-active .count {{ background: rgba(255,255,255,.25); }}
    .rss-link {{ margin-left: auto; font-size: .78rem; color: var(--muted); text-decoration: none; display: flex; align-items: center; gap: .3rem; white-space: nowrap; }}
    .rss-link:hover {{ color: var(--accent); }}
    .region-filters {{ border-top: 1px solid var(--border); padding-top: .5rem; }}
    .region-btn {{ background: var(--surface); border: 1.5px solid var(--border); border-radius: 20px; padding: .3rem .85rem; font-size: .8rem; font-weight: 500; color: var(--muted); cursor: pointer; transition: all .15s; display: flex; align-items: center; gap: .3rem; }}
    .region-btn:hover {{ border-color: var(--accent); color: var(--accent); }}
    .region-btn.region-active {{ background: var(--accent); border-color: var(--accent); color: white; }}
    .region-btn .count {{ font-size: .7rem; background: rgba(0,0,0,.08); border-radius: 10px; padding: .05rem .4rem; font-weight: 600; }}
    .region-btn.region-active .count {{ background: rgba(255,255,255,.25); }}

    /* Subscribe bar */
    .subscribe-bar {{ max-width: 900px; margin: 1rem auto 0; padding: 0 1rem; }}
    .subscribe-form {{ background: var(--surface); border: 1.5px solid var(--border); border-radius: 12px; padding: .8rem 1rem; display: flex; align-items: center; gap: .6rem; flex-wrap: wrap; }}
    .subscribe-form span {{ font-size: .85rem; color: var(--muted); flex-shrink: 0; }}
    .subscribe-form input {{ flex: 1; min-width: 180px; padding: .4rem .9rem; border: 1.5px solid var(--border); border-radius: 20px; background: var(--bg); color: var(--text); font-size: .85rem; font-family: inherit; outline: none; }}
    .subscribe-form input:focus {{ border-color: var(--accent); }}
    .subscribe-form button {{ padding: .4rem 1.1rem; background: var(--accent); color: white; border: none; border-radius: 20px; font-size: .85rem; font-weight: 600; cursor: pointer; white-space: nowrap; }}
    .subscribe-form button:hover {{ opacity: .85; }}

    /* Cards */
    main {{ max-width: 900px; margin: 1.25rem auto 2rem; padding: 0 1rem; display: grid; gap: 1rem; }}
    main.list-view {{ grid-template-columns: 1fr; }}
    main.grid-view {{ grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); }}
    .card {{ background: var(--surface); border-radius: 12px; padding: 1.4rem; border: 1px solid var(--border); transition: box-shadow .2s, transform .15s; }}
    .card:hover {{ box-shadow: 0 4px 20px rgba(0,0,0,.08); transform: translateY(-1px); }}
    .card.hidden {{ display: none; }}
    .card-featured {{ border-left: 4px solid var(--accent); }}
    .card-meta {{ display: flex; align-items: center; gap: .4rem; flex-wrap: wrap; margin-bottom: .55rem; }}
    .card-source {{ font-size: .73rem; color: var(--muted); text-transform: uppercase; letter-spacing: .5px; font-weight: 600; }}
    .card-dot {{ color: var(--border); font-size: .7rem; }}
    .card-date, .card-read {{ font-size: .73rem; color: var(--muted); }}
    .badge-new {{ font-size: .65rem; font-weight: 700; background: #22c55e; color: white; border-radius: 8px; padding: .1rem .45rem; text-transform: uppercase; letter-spacing: .3px; }}
    .card-tag {{ font-size: .68rem; font-weight: 600; background: var(--tag-bg); color: var(--tag-color); border-radius: 10px; padding: .1rem .5rem; margin-left: auto; }}
    .card-title {{ font-size: 1.05rem; font-weight: 600; margin-bottom: .6rem; line-height: 1.45; }}
    .card-title a {{ color: var(--text); text-decoration: none; }}
    .card-title a:hover {{ color: var(--accent); }}
    .card-featured .card-title {{ font-size: 1.2rem; }}
    .card-image {{ width: 100%; height: 180px; object-fit: cover; border-radius: 8px; margin-bottom: .75rem; display: block; }}
    .card-featured .card-image {{ height: 220px; }}
    .card-summary {{ font-size: .88rem; color: var(--muted); margin-bottom: .9rem; }}
    .card-actions {{ display: flex; align-items: center; justify-content: space-between; }}

    /* Compact view */
    main.compact-view .card {{ padding: .65rem 1rem; border-radius: 8px; }}
    main.compact-view .card-image {{ display: none; }}
    main.compact-view .card-summary {{ display: none; }}
    main.compact-view .card-actions {{ display: none; }}
    main.compact-view .card-title {{ font-size: .92rem; margin-bottom: 0; }}
    main.compact-view .card-meta {{ margin-bottom: .25rem; }}
    main.compact-view {{ gap: .3rem; }}
    .card-link {{ font-size: .82rem; color: var(--accent); font-weight: 500; text-decoration: none; }}
    .card-link:hover {{ text-decoration: underline; }}
    .card-share {{ display: flex; gap: .4rem; align-items: center; }}
    .share-btn {{ display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; border-radius: 6px; font-size: .75rem; font-weight: 700; text-decoration: none; border: 1.5px solid var(--border); background: var(--surface); color: var(--muted); cursor: pointer; transition: all .15s; }}
    .share-btn:hover {{ border-color: var(--accent); color: var(--accent); }}
    .save-btn.saved {{ background: var(--accent); border-color: var(--accent); color: white; }}
    .no-results {{ text-align: center; color: var(--muted); padding: 3rem; display: none; grid-column: 1/-1; }}


    /* Signal & amplification badges */
    .badge-signal {{ font-size: .65rem; font-weight: 700; background: #f59e0b22; color: #d97706; border: 1px solid #f59e0b44; border-radius: 8px; padding: .1rem .45rem; }}
    .badge-amp    {{ font-size: .65rem; font-weight: 700; background: #ef444422; color: #dc2626; border: 1px solid #ef444444; border-radius: 8px; padding: .1rem .45rem; }}
    .badge-deal   {{ font-size: .65rem; font-weight: 700; background: #22c55e22; color: #16a34a; border: 1px solid #22c55e44; border-radius: 8px; padding: .1rem .45rem; }}
    .card-signal  {{ border-left: 3px solid #f59e0b; }}
    .card-why     {{ font-size: .8rem; color: #d97706; margin: .4rem 0 .7rem; display: flex; align-items: flex-start; gap: .35rem; line-height: 1.4; }}
    .why-icon     {{ flex-shrink: 0; }}

    /* Intel 2-col section (Señales + Deals) */
    .intel-section  {{ max-width: 900px; margin: 1rem auto 0; padding: 0 1rem; }}
    .intel-grid-2   {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }}
    .intel-grid-1   {{ display: grid; grid-template-columns: 1fr; gap: 1rem; }}
    @media (max-width: 640px) {{ .intel-grid-2 {{ grid-template-columns: 1fr; }} }}
    .intel-col      {{ background: var(--surface); border: 1.5px solid #f59e0b44; border-radius: 12px; overflow: hidden; display: flex; flex-direction: column; }}
    .intel-col-header {{ display: flex; align-items: baseline; justify-content: space-between; padding: .75rem 1rem .6rem; border-bottom: 1px solid var(--border); }}
    .intel-col-title  {{ font-size: .88rem; font-weight: 700; color: var(--text); }}
    .intel-col-sub    {{ font-size: .68rem; color: var(--muted); }}
    .intel-col-body   {{ display: flex; flex-direction: column; flex: 1; }}
    /* Radar rows */
    .radar-row    {{ display: flex; align-items: flex-start; gap: .75rem; padding: .75rem 1rem; border-bottom: 1px solid var(--border); text-decoration: none; color: inherit; transition: background .15s; }}
    .radar-row:last-child {{ border-bottom: none; }}
    .radar-row:hover {{ background: var(--bg); }}
    .radar-icon   {{ font-size: 1.1rem; flex-shrink: 0; padding-top: .1rem; }}
    .radar-content {{ flex: 1; min-width: 0; }}
    .radar-title  {{ display: block; font-size: .84rem; font-weight: 600; color: var(--text); line-height: 1.4; margin-bottom: .15rem; }}
    .radar-meta   {{ font-size: .7rem; color: var(--muted); }}
    .radar-why    {{ display: block; font-size: .72rem; color: #d97706; margin-top: .2rem; }}
    .radar-score  {{ font-size: .72rem; font-weight: 700; color: #f59e0b; background: #f59e0b18; border-radius: 6px; padding: .15rem .45rem; flex-shrink: 0; align-self: center; }}
    .radar-amp    {{ font-size: .68rem; }}
    .radar-deal   {{ font-size: .68rem; color: #16a34a; }}
    /* Deal rows (compact, inside intel col) */
    .deal-row2    {{ display: flex; align-items: center; gap: .5rem; padding: .65rem 1rem; border-bottom: 1px solid var(--border); text-decoration: none; color: inherit; transition: background .15s; min-width: 0; }}
    .deal-row2:last-child {{ border-bottom: none; }}
    .deal-row2:hover {{ background: var(--bg); }}
    .deal-amount  {{ font-size: .88rem; font-weight: 700; color: #16a34a; white-space: nowrap; flex-shrink: 0; }}
    .deal-round   {{ font-size: .65rem; font-weight: 700; background: #22c55e22; color: #16a34a; border-radius: 6px; padding: .08rem .38rem; white-space: nowrap; flex-shrink: 0; }}
    .deal-title2  {{ font-size: .78rem; color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; min-width: 0; }}

    /* Trends */
    .trends-section {{ max-width: 900px; margin: .75rem auto 0; padding: 0 1rem; display: flex; align-items: center; gap: .75rem; flex-wrap: wrap; }}
    .trends-label {{ font-size: .8rem; font-weight: 600; color: var(--muted); white-space: nowrap; }}
    .trends-pills {{ display: flex; flex-wrap: wrap; gap: .4rem; }}
    .trend-pill   {{ font-size: .75rem; background: var(--surface); border: 1px solid var(--border); border-radius: 20px; padding: .25rem .75rem; color: var(--text); display: flex; align-items: center; gap: .35rem; }}
    .trend-badge  {{ font-size: .65rem; font-weight: 700; border-radius: 6px; padding: .05rem .35rem; }}
    .trend-badge.up  {{ background: #22c55e22; color: #16a34a; }}
    .trend-badge.new {{ background: #6366f122; color: #6366f1; }}

    /* Favicon */
    .source-favicon {{ width: 14px; height: 14px; border-radius: 2px; vertical-align: middle; margin-right: .25rem; flex-shrink: 0; }}

    /* Read articles */
    .card.read {{ opacity: .55; }}
    .card.read .card-title a {{ text-decoration: line-through; text-decoration-color: var(--muted); }}
    .card.read:hover {{ opacity: .8; }}

    /* Saved filter btn */
    #btn-saved {{ transition: all .15s; }}
    #btn-saved.saved-active {{ background: #f59e0b; border-color: #f59e0b; color: white; }}

    /* Share filter btn */
    .share-filter-btn {{ background: var(--surface); border: 1.5px solid var(--border); border-radius: 20px; padding: .3rem .85rem; font-size: .8rem; font-weight: 500; color: var(--muted); cursor: pointer; transition: all .15s; }}
    .share-filter-btn:hover {{ border-color: var(--accent); color: var(--accent); }}
    .share-filter-btn.copied {{ background: #22c55e; border-color: #22c55e; color: white; }}

    /* Results counter */
    #results-info {{ max-width: 900px; margin: .5rem auto 0; padding: 0 1.25rem; font-size: .78rem; color: var(--muted); min-height: 1.2rem; }}

    /* Time separators */
    .time-sep {{ max-width: 900px; margin: 1.5rem auto 0; padding: 0 1rem; display: flex; align-items: center; gap: .75rem; grid-column: 1/-1; }}
    .time-sep span {{ font-size: .75rem; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: .8px; white-space: nowrap; }}
    .time-sep::after {{ content: ''; flex: 1; height: 1px; background: var(--border); }}

    /* Keyboard focus highlight */
    .card.kbd-focus {{ outline: 2px solid var(--accent); outline-offset: 2px; }}

    /* Empty state */
    .no-results {{ text-align: center; color: var(--muted); padding: 3rem; display: none; grid-column: 1/-1; }}
    .no-results p {{ margin-bottom: 1rem; }}
    .no-results button {{ padding: .45rem 1.2rem; background: var(--accent); color: white; border: none; border-radius: 20px; font-size: .85rem; font-weight: 600; cursor: pointer; }}

    /* Back to top */
    #back-to-top {{ position: fixed; bottom: 5rem; right: 1.25rem; width: 40px; height: 40px; background: var(--accent); color: white; border: none; border-radius: 50%; font-size: 1.1rem; font-weight: 700; cursor: pointer; display: none; box-shadow: 0 2px 12px rgba(0,0,0,.2); z-index: 200; transition: opacity .2s; }}
    #back-to-top:hover {{ opacity: .85; }}

    /* Keyboard hint */
    .kbd-hint {{ margin-top: .6rem; font-size: .72rem; color: var(--border); }}
    kbd {{ background: var(--surface); border: 1px solid var(--border); border-radius: 4px; padding: .1rem .35rem; font-size: .7rem; font-family: monospace; color: var(--muted); }}

    /* Mobile FAB + sheet */
    .mobile-fab {{ display: none; position: fixed; bottom: 1.25rem; right: 1.25rem; padding: .6rem 1.2rem; background: var(--accent); color: white; border: none; border-radius: 24px; font-size: .88rem; font-weight: 600; cursor: pointer; box-shadow: 0 2px 16px rgba(0,0,0,.25); z-index: 200; }}
    .mobile-overlay {{ display: none; position: fixed; inset: 0; background: rgba(0,0,0,.45); z-index: 300; }}
    .mobile-sheet {{ display: none; position: fixed; bottom: 0; left: 0; right: 0; background: var(--surface); border-radius: 20px 20px 0 0; z-index: 400; padding: 0 0 2rem; max-height: 80vh; overflow-y: auto; box-shadow: 0 -4px 32px rgba(0,0,0,.2); }}
    .mobile-sheet.open, .mobile-overlay.open {{ display: block; }}
    .mobile-sheet-header {{ display: flex; align-items: center; justify-content: space-between; padding: 1rem 1.25rem .75rem; border-bottom: 1px solid var(--border); font-weight: 700; font-size: .95rem; }}
    .mobile-sheet-close {{ background: none; border: none; font-size: 1.1rem; cursor: pointer; color: var(--muted); padding: .2rem; }}
    .mobile-sheet-body {{ padding: 1rem 1.25rem; }}
    .mobile-sheet-label {{ font-size: .72rem; font-weight: 700; text-transform: uppercase; letter-spacing: .6px; color: var(--muted); margin-bottom: .5rem; }}
    .mobile-filter-group {{ display: flex; flex-wrap: wrap; gap: .4rem; margin-bottom: 1.25rem; }}
    @media (max-width: 640px) {{
      .toolbar .filters {{ display: none; }}
      .mobile-fab {{ display: flex; align-items: center; gap: .4rem; }}
      #back-to-top {{ bottom: 4.5rem; }}
    }}

    /* Daily Briefing */
    .brief-section {{ max-width: 900px; margin: 1rem auto 0; padding: 0 1rem; }}
    .brief-section > * {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }}
    .brief-section > .brief-header,
    .brief-section > .brief-body,
    .brief-section > .brief-stats {{ background: none; border: none; border-radius: 0; }}
    .brief-section {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }}
    .brief-header {{ border-bottom: 1px solid var(--border); padding: .85rem 1.2rem .7rem; }}
    .brief-title-row {{ display: flex; align-items: center; gap: .75rem; flex-wrap: wrap; }}
    .brief-badge {{ font-size: .78rem; font-weight: 800; color: #fff; background: #1a1a2e; border-radius: 6px; padding: .2rem .6rem; letter-spacing: .3px; flex-shrink: 0; }}
    @media (prefers-color-scheme: dark) {{ .brief-badge {{ background: var(--accent); }} }}
    .brief-date  {{ font-size: .82rem; font-weight: 600; color: var(--text); text-transform: capitalize; }}
    .brief-refresh {{ margin-left: auto; font-size: .72rem; color: var(--muted); }}
    .brief-body  {{ padding: .6rem 1.2rem .5rem; display: flex; flex-direction: column; gap: .45rem; }}
    .brief-line  {{ display: flex; align-items: baseline; gap: .55rem; min-width: 0; }}
    .brief-icon  {{ font-size: .95rem; flex-shrink: 0; width: 1.4rem; text-align: center; }}
    .brief-label {{ font-size: .78rem; font-weight: 700; color: var(--text); white-space: nowrap; flex-shrink: 0; display: flex; align-items: center; gap: .3rem; min-width: 110px; }}
    .brief-count {{ font-size: .65rem; font-weight: 700; background: var(--accent); color: white; border-radius: 8px; padding: .05rem .38rem; }}
    .brief-titles {{ font-size: .82rem; color: var(--muted); line-height: 1.45; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
    @media (max-width: 600px) {{ .brief-titles {{ white-space: normal; }} }}
    .brief-stats {{ padding: .65rem 1.2rem .85rem; font-size: .75rem; color: var(--muted); border-top: 1px solid var(--border); line-height: 1.6; }}
    .brief-stats strong {{ color: var(--text); }}

    /* Regulatory Alert */
    .reg-alert {{ max-width: 900px; margin: .75rem auto 0; padding: 0 1rem; }}
    .reg-alert-inner {{ background: linear-gradient(90deg, #fef3c7 0%, #fffbeb 100%); border: 1.5px solid #fbbf24; border-radius: 12px; padding: 1rem 1.2rem; display: flex; align-items: flex-start; gap: .9rem; }}
    @media (prefers-color-scheme: dark) {{
      .reg-alert-inner {{ background: linear-gradient(90deg, #292010 0%, #1f1a09 100%); border-color: #b45309; }}
    }}
    .reg-alert-icon {{ font-size: 1.4rem; flex-shrink: 0; }}
    .reg-alert-body {{ flex: 1; min-width: 0; }}
    .reg-alert-label {{ display: block; font-size: .68rem; font-weight: 700; text-transform: uppercase; letter-spacing: .5px; color: #92400e; margin-bottom: .3rem; }}
    @media (prefers-color-scheme: dark) {{ .reg-alert-label {{ color: #fbbf24; }} }}
    .reg-alert-title {{ display: block; font-size: .92rem; font-weight: 700; color: #78350f; text-decoration: none; line-height: 1.4; margin-bottom: .25rem; }}
    .reg-alert-title:hover {{ text-decoration: underline; }}
    @media (prefers-color-scheme: dark) {{ .reg-alert-title {{ color: #fde68a; }} }}
    .reg-alert-why {{ font-size: .78rem; color: #92400e; }}
    @media (prefers-color-scheme: dark) {{ .reg-alert-why {{ color: #fbbf24; }} }}
    .reg-alert-meta {{ font-size: .72rem; color: #b45309; white-space: nowrap; flex-shrink: 0; padding-top: .15rem; }}


    /* Briefing view */
    main.briefing-view .card {{ display: none; }}
    main.briefing-view .card[data-signal="1"] {{ display: flex; flex-direction: row; align-items: flex-start; gap: .75rem; padding: .75rem 1rem; border-radius: 8px; }}
    main.briefing-view .card[data-signal="1"] .card-image, main.briefing-view .card[data-signal="1"] .card-summary, main.briefing-view .card[data-signal="1"] .card-actions, main.briefing-view .card[data-signal="1"] .card-why {{ display: none; }}
    main.briefing-view .card[data-signal="1"] .card-title {{ font-size: .9rem; margin-bottom: 0; }}
    main.briefing-view .card[data-signal="1"] .card-meta {{ margin-bottom: 0; }}
    main.briefing-view {{ gap: .3rem; }}
    main.briefing-view .time-sep {{ margin-top: .75rem; }}

    footer {{ text-align: center; padding: 2rem; font-size: .8rem; color: var(--muted); border-top: 1px solid var(--border); }}
    footer a {{ color: var(--accent); text-decoration: none; }}

    @media (max-width: 600px) {{
      /* Compact header — only title + updated */
      header {{ padding: .75rem 1rem; }}
      header h1 {{ font-size: 1.25rem; }}
      .header-sub, .header-stats, #google_translate_element {{ display: none; }}
      .updated {{ margin-top: .2rem; font-size: .7rem; }}
      /* Toolbar: just the search bar, no padding waste */
      .toolbar {{ margin-top: 0; padding: .5rem .75rem; gap: .4rem; top: 0; }}
      .search-row {{ gap: .4rem; }}
      #search {{ font-size: .85rem; padding: .4rem .85rem; }}
      /* Cards */
      .card {{ padding: .9rem; }}
      .card-image {{ height: 140px; }}
      main.grid-view {{ grid-template-columns: 1fr; }}
      .rss-link, .share-filter-btn, .kbd-hint {{ display: none; }}
      /* Radar rows compact */
      .radar-row {{ padding: .65rem .9rem; }}
      .deal-row {{ grid-template-columns: 60px auto 1fr; }}
      .deal-meta {{ display: none; }}
      /* Subscribe form compact */
      .subscribe-form {{ flex-direction: column; align-items: stretch; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>InsurTech Intelligence</h1>
    <p class="header-sub">Noticias globales de insurtech, actualizadas cada 6 horas</p>
    <div class="header-stats">
      <span class="stat"><strong>{len(articles)}</strong> artículos</span>
      <span class="stat"><strong>{new_count}</strong> nuevos hoy</span>
      <span class="stat"><strong>{signal_count}</strong> señales esta semana</span>
      <span class="stat"><strong>40</strong> fuentes monitorizadas</span>
      <span class="stat"><strong>{ibero_count}</strong> iberoamérica</span>
    </div>
    <div class="updated">Actualizado el {updated}</div>
    <div id="google_translate_element"></div>
  </header>

  <div class="toolbar">
    <div class="search-row">
      <input id="search" type="search" placeholder="Buscar artículos... (o pulsa /)" autocomplete="off" />
      <div class="view-toggle">
        <button class="view-btn active" id="btn-list" title="Vista lista [1]">&#9776;</button>
        <button class="view-btn" id="btn-grid" title="Vista grid [2]">&#9638;</button>
        <button class="view-btn" id="btn-compact" title="Vista compacta [3]">&#9472;</button>
        <button class="view-btn" id="btn-briefing" title="Modo Briefing — solo señales [4]">📋</button>
      </div>
    </div>
    <div class="filters">
      <button class="filter-btn all-active" data-filter="all">Todos <span class="count">{len(articles)}</span></button>
      {filter_buttons}
      <button class="filter-btn" id="btn-saved">🔖 Guardados</button>
    </div>
    <div class="filters region-filters">
      <button class="region-btn region-active" data-region="all">🌍 Todo el mundo</button>
      <button class="region-btn" data-region="ibero">🌎 Iberoamérica <span class="count">{ibero_count}</span></button>
      <button class="region-btn" data-region="global">🌐 Global <span class="count">{len(articles) - ibero_count}</span></button>
      <button class="share-filter-btn" id="btn-share-filter" title="Copiar enlace con filtros activos">🔗 Compartir</button>
      <a href="{SITE_URL}/feed.xml" class="rss-link" target="_blank">&#x2609; RSS</a>
    </div>
  </div>
  <div id="results-info"></div>

  {briefing_html}
  {reg_alert_html}
  {radar_html}
  {trends_html}
  {deals_html}
  {thermometer_html}
  {incumbent_html}
  {startup_html}

  <div class="subscribe-bar">
    <form class="subscribe-form" action="https://buttondown.email/api/emails/embed-subscribe/insurtechintelligence" method="post" target="_blank">
      <span>📬 Recibe el briefing diario en tu email:</span>
      <input type="email" name="email" placeholder="tu@email.com" required />
      <button type="submit">Suscribirse gratis</button>
      <a href="{SITE_URL}/newsletter.html" target="_blank" style="font-size:.8rem;color:var(--muted);text-decoration:none;white-space:nowrap">Ver ejemplo →</a>
    </form>
  </div>

  <main class="list-view" id="main">
    {featured_html}
    {cards_html if articles else '<p style="text-align:center;color:var(--muted);padding:3rem">Sin artículos por ahora.</p>'}
    <div class="no-results" id="no-results">
      <p>No hay artículos que coincidan con los filtros actuales.</p>
      <button id="btn-clear-filters">Quitar todos los filtros</button>
    </div>
  </main>
  <div style="text-align:center;padding:1rem 1rem 2rem">
    <button id="load-more" style="display:none;padding:.55rem 2rem;background:var(--accent);color:white;border:none;border-radius:20px;font-size:.88rem;font-weight:600;cursor:pointer;transition:opacity .15s">Cargar más artículos</button>
  </div>

  <footer>
    InsurTech Intelligence · <a href="{SITE_URL}/newsletter.html">📬 Newsletter del día</a> · <a href="{SITE_URL}/feed.xml">RSS</a> · <a href="{SITE_URL}/digest.html">Digest Semanal</a>
    <div class="kbd-hint">Atajos: <kbd>/</kbd> buscar · <kbd>J</kbd>/<kbd>K</kbd> navegar · <kbd>O</kbd> abrir · <kbd>B</kbd> guardar · <kbd>4</kbd> briefing</div>
  </footer>

  <!-- Back to top -->
  <button id="back-to-top" title="Volver arriba">↑</button>

  <!-- Mobile filter FAB -->
  <button class="mobile-fab" id="mobile-fab">⚙ Filtros</button>
  <div class="mobile-overlay" id="mobile-overlay"></div>
  <div class="mobile-sheet" id="mobile-sheet">
    <div class="mobile-sheet-header">
      <span>Filtros</span>
      <button class="mobile-sheet-close" id="mobile-sheet-close">✕</button>
    </div>
    <div class="mobile-sheet-body">
      <p class="mobile-sheet-label">Categoría</p>
      <div class="mobile-filter-group" id="mobile-cats"></div>
      <p class="mobile-sheet-label">Región</p>
      <div class="mobile-filter-group" id="mobile-regions"></div>
    </div>
  </div>

  <script type="text/javascript">
    function googleTranslateElementInit() {{
      new google.translate.TranslateElement({{
        pageLanguage: 'en',
        includedLanguages: 'es,fr,de,pt,it,zh-CN,ar',
        layout: google.translate.TranslateElement.InlineLayout.SIMPLE,
        autoDisplay: false,
      }}, 'google_translate_element');
    }}
  </script>
  <script src="//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit"></script>

  <script>
    // ── State ──
    const cards      = Array.from(document.querySelectorAll('.card'));
    const filterBtns = Array.from(document.querySelectorAll('.filter-btn:not(#btn-saved)'));
    const regionBtns = Array.from(document.querySelectorAll('.region-btn'));
    const search     = document.getElementById('search');
    const mainEl     = document.getElementById('main');
    const loadMoreBtn= document.getElementById('load-more');
    const resultsInfo= document.getElementById('results-info');
    const noResults  = document.getElementById('no-results');
    const PAGE_SIZE  = 20;
    let activeFilter = 'all';
    let activeRegion = 'all';
    let searchQuery  = '';
    let showSavedOnly= false;
    let loadedCount  = PAGE_SIZE;
    let focusedIdx   = -1;

    // ── localStorage helpers ──
    const SAVED_KEY = 'insurtech_saved';
    const READ_KEY  = 'insurtech_read';
    const ls = k => {{ try {{ return JSON.parse(localStorage.getItem(k) || '[]'); }} catch {{ return []; }} }};
    const lsSet = (k,v) => localStorage.setItem(k, JSON.stringify(v));

    // ── URL sync ──
    function syncURL() {{
      const p = new URLSearchParams();
      if (activeFilter !== 'all') p.set('cat', activeFilter);
      if (activeRegion !== 'all') p.set('region', activeRegion);
      if (showSavedOnly) p.set('saved', '1');
      if (searchQuery) p.set('q', searchQuery);
      history.replaceState(null, '', p.toString() ? '?' + p.toString() : location.pathname);
    }}

    function readURL() {{
      const p = new URLSearchParams(location.search);
      if (p.get('cat'))    activeFilter = p.get('cat');
      if (p.get('region')) activeRegion = p.get('region');
      if (p.get('saved'))  showSavedOnly = true;
      if (p.get('q'))      {{ searchQuery = p.get('q'); search.value = searchQuery; }}
    }}

    // ── Main update ──
    function update() {{
      const saved = ls(SAVED_KEY);
      let visible = 0, filtered = 0;
      cards.forEach(card => {{
        const matchFilter = activeFilter === 'all' || card.dataset.category === activeFilter;
        const matchRegion = activeRegion === 'all' || card.dataset.region === activeRegion;
        const matchSearch = !searchQuery || card.dataset.search.includes(searchQuery);
        const matchSaved  = !showSavedOnly || saved.includes(card.dataset.id);
        if (matchFilter && matchRegion && matchSearch && matchSaved) {{
          filtered++;
          const show = filtered <= loadedCount;
          card.classList.toggle('hidden', !show);
          if (show) visible++;
        }} else {{
          card.classList.add('hidden');
        }}
      }});

      // Time separators: hide if no visible cards follow
      document.querySelectorAll('.time-sep').forEach(sep => {{
        let el = sep.nextElementSibling, has = false;
        while (el && !el.classList.contains('time-sep')) {{
          if (el.classList.contains('card') && !el.classList.contains('hidden')) {{ has = true; break; }}
          el = el.nextElementSibling;
        }}
        sep.style.display = has ? '' : 'none';
      }});

      noResults.style.display = visible === 0 ? 'flex' : 'none';
      loadMoreBtn.style.display = filtered > loadedCount ? 'block' : 'none';

      // Results counter
      const total = cards.length;
      if (filtered === total && !searchQuery)
        resultsInfo.textContent = '';
      else
        resultsInfo.textContent = `Mostrando ${{Math.min(visible, filtered)}} de ${{filtered}} artículos`;

      syncURL();
    }}

    // ── Category filters ──
    filterBtns.forEach(btn => {{
      btn.addEventListener('click', () => {{
        activeFilter = btn.dataset.filter;
        loadedCount = PAGE_SIZE; focusedIdx = -1;
        filterBtns.forEach(b => b.classList.remove('active','all-active'));
        btn.classList.add(activeFilter === 'all' ? 'all-active' : 'active');
        update();
      }});
    }});

    // ── Region filters ──
    regionBtns.forEach(btn => {{
      btn.addEventListener('click', () => {{
        activeRegion = btn.dataset.region;
        loadedCount = PAGE_SIZE; focusedIdx = -1;
        regionBtns.forEach(b => b.classList.remove('region-active'));
        btn.classList.add('region-active');
        // Mirror to mobile sheet
        document.querySelectorAll('#mobile-regions .filter-btn').forEach(b => {{
          b.classList.toggle('active', b.dataset.region === activeRegion);
        }});
        update();
      }});
    }});

    // ── Search ──
    search.addEventListener('input', () => {{
      searchQuery = search.value.trim().toLowerCase();
      loadedCount = PAGE_SIZE; focusedIdx = -1;
      update();
    }});

    // ── Load more ──
    loadMoreBtn.addEventListener('click', () => {{
      loadedCount += PAGE_SIZE;
      update();
      loadMoreBtn.scrollIntoView({{ behavior:'smooth', block:'center' }});
    }});

    // ── View toggle ──
    function setView(mode) {{
      mainEl.className = mode + '-view';
      ['list','grid','compact','briefing'].forEach(m =>
        document.getElementById('btn-'+m).classList.toggle('active', m===mode));
      // In briefing mode update results info to only count signal articles
      if (mode === 'briefing') {{
        const sigCount = cards.filter(c => c.dataset.signal === '1').length;
        resultsInfo.textContent = `Modo Briefing: ${{sigCount}} señales de alta relevancia`;
      }}
    }}
    document.getElementById('btn-list').addEventListener('click', () => setView('list'));
    document.getElementById('btn-grid').addEventListener('click', () => setView('grid'));
    document.getElementById('btn-compact').addEventListener('click', () => setView('compact'));
    document.getElementById('btn-briefing').addEventListener('click', () => setView('briefing'));

    // ── Bookmarks ──
    function initBookmarks() {{
      const saved = ls(SAVED_KEY);
      document.querySelectorAll('.save-btn').forEach(btn => {{
        if (saved.includes(btn.dataset.id)) btn.classList.add('saved');
        btn.addEventListener('click', e => {{
          e.stopPropagation();
          let s = ls(SAVED_KEY);
          if (s.includes(btn.dataset.id)) {{ s = s.filter(x => x !== btn.dataset.id); btn.classList.remove('saved'); }}
          else {{ s.push(btn.dataset.id); btn.classList.add('saved'); }}
          lsSet(SAVED_KEY, s);
          if (showSavedOnly) update();
        }});
      }});
    }}

    // ── Read tracking ──
    function initReadTracking() {{
      const read = ls(READ_KEY);
      cards.forEach(card => {{
        if (read.includes(card.dataset.id)) card.classList.add('read');
        card.querySelectorAll('a[href]').forEach(a => {{
          a.addEventListener('click', () => {{
            let r = ls(READ_KEY);
            if (!r.includes(card.dataset.id)) {{ r.push(card.dataset.id); lsSet(READ_KEY, r); }}
            card.classList.add('read');
          }});
        }});
      }});
    }}

    // ── Saved-only filter toggle ──
    const btnSaved = document.getElementById('btn-saved');
    btnSaved.addEventListener('click', () => {{
      showSavedOnly = !showSavedOnly;
      btnSaved.classList.toggle('saved-active', showSavedOnly);
      loadedCount = PAGE_SIZE; focusedIdx = -1;
      update();
    }});

    // ── Clear filters ──
    document.getElementById('btn-clear-filters').addEventListener('click', () => {{
      activeFilter = 'all'; activeRegion = 'all'; showSavedOnly = false;
      searchQuery = ''; search.value = ''; loadedCount = PAGE_SIZE; focusedIdx = -1;
      filterBtns.forEach(b => b.classList.remove('active','all-active'));
      document.querySelector('[data-filter="all"]').classList.add('all-active');
      regionBtns.forEach(b => b.classList.remove('region-active'));
      document.querySelector('[data-region="all"]').classList.add('region-active');
      btnSaved.classList.remove('saved-active');
      update();
    }});

    // ── Share filter URL ──
    document.getElementById('btn-share-filter').addEventListener('click', async () => {{
      const btn = document.getElementById('btn-share-filter');
      try {{
        await navigator.clipboard.writeText(location.href);
      }} catch (e) {{
        const inp = document.createElement('input');
        inp.value = location.href; document.body.appendChild(inp); inp.select();
        document.execCommand('copy'); document.body.removeChild(inp);
      }}
      btn.textContent = '✓ Copiado'; btn.classList.add('copied');
      setTimeout(() => {{ btn.textContent = '🔗 Compartir'; btn.classList.remove('copied'); }}, 2000);
    }});

    // ── Back to top + auto-hide header on mobile ──
    const btt    = document.getElementById('back-to-top');
    const header = document.querySelector('header');
    const toolbar= document.querySelector('.toolbar');
    let lastY = 0;
    window.addEventListener('scroll', () => {{
      const y = window.scrollY;
      btt.style.display = y > 400 ? 'block' : 'none';
      // Auto-hide header when scrolling down on mobile
      if (window.innerWidth <= 600) {{
        if (y > lastY && y > 80) {{
          header.style.transform = 'translateY(-100%)';
          header.style.transition = 'transform .25s';
        }} else {{
          header.style.transform = '';
        }}
      }}
      lastY = y;
    }}, {{ passive: true }});
    btt.addEventListener('click', () => window.scrollTo({{ top:0, behavior:'smooth' }}));

    // ── Keyboard shortcuts ──
    document.addEventListener('keydown', e => {{
      const tag = document.activeElement.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA') {{
        if (e.key === 'Escape') {{ search.blur(); search.value=''; searchQuery=''; loadedCount=PAGE_SIZE; update(); }}
        return;
      }}
      const visible = cards.filter(c => !c.classList.contains('hidden'));
      switch(e.key) {{
        case '/':
          e.preventDefault(); search.focus(); break;
        case 'j': case 'J':
          e.preventDefault();
          focusedIdx = Math.min(visible.length-1, focusedIdx+1);
          cards.forEach(c => c.classList.remove('kbd-focus'));
          if (visible[focusedIdx]) {{ visible[focusedIdx].classList.add('kbd-focus'); visible[focusedIdx].scrollIntoView({{behavior:'smooth',block:'center'}}); }}
          break;
        case 'k': case 'K':
          e.preventDefault();
          focusedIdx = Math.max(0, focusedIdx-1);
          cards.forEach(c => c.classList.remove('kbd-focus'));
          if (visible[focusedIdx]) {{ visible[focusedIdx].classList.add('kbd-focus'); visible[focusedIdx].scrollIntoView({{behavior:'smooth',block:'center'}}); }}
          break;
        case 'o': case 'O': case 'Enter':
          if (focusedIdx >= 0 && visible[focusedIdx]) {{
            window.open(visible[focusedIdx].dataset.url, '_blank');
          }}
          break;
        case 'b': case 'B':
          if (focusedIdx >= 0 && visible[focusedIdx]) {{
            visible[focusedIdx].querySelector('.save-btn')?.click();
          }}
          break;
        case '1': setView('list'); break;
        case '2': setView('grid'); break;
        case '3': setView('compact'); break;
        case '4': setView('briefing'); break;
      }}
    }});

    // ── Mobile bottom sheet ──
    const mFab     = document.getElementById('mobile-fab');
    const mSheet   = document.getElementById('mobile-sheet');
    const mOverlay = document.getElementById('mobile-overlay');
    const mClose   = document.getElementById('mobile-sheet-close');

    function buildMobileFilters() {{
      const catContainer = document.getElementById('mobile-cats');
      const regContainer = document.getElementById('mobile-regions');
      // Clone category buttons
      filterBtns.forEach(btn => {{
        const b = btn.cloneNode(true);
        b.addEventListener('click', () => {{
          activeFilter = b.dataset.filter; loadedCount = PAGE_SIZE;
          filterBtns.forEach(x => x.classList.remove('active','all-active'));
          document.querySelectorAll('#mobile-cats .filter-btn').forEach(x => x.classList.remove('active','all-active'));
          const orig = document.querySelector(`[data-filter="${{b.dataset.filter}}"]`);
          if (orig) orig.classList.add(activeFilter==='all'?'all-active':'active');
          b.classList.add(activeFilter==='all'?'all-active':'active');
          closeSheet(); update();
        }});
        catContainer.appendChild(b);
      }});
      // Clone region buttons
      regionBtns.forEach(btn => {{
        const b = btn.cloneNode(true);
        b.className = 'filter-btn';
        b.dataset.region = btn.dataset.region;
        b.addEventListener('click', () => {{
          activeRegion = b.dataset.region; loadedCount = PAGE_SIZE;
          regionBtns.forEach(x => x.classList.remove('region-active'));
          document.querySelectorAll('#mobile-regions .filter-btn').forEach(x => x.classList.remove('active','all-active'));
          document.querySelector(`[data-region="${{b.dataset.region}}"]`)?.classList.add('region-active');
          b.classList.add('active');
          closeSheet(); update();
        }});
        regContainer.appendChild(b);
      }});
    }}

    function openSheet() {{ mSheet.classList.add('open'); mOverlay.classList.add('open'); document.body.style.overflow='hidden'; }}
    function closeSheet() {{ mSheet.classList.remove('open'); mOverlay.classList.remove('open'); document.body.style.overflow=''; }}

    mFab.addEventListener('click', openSheet);
    mClose.addEventListener('click', closeSheet);
    mOverlay.addEventListener('click', closeSheet);

    // ── Init ──
    readURL();
    buildMobileFilters();
    initBookmarks();
    initReadTracking();
    // Apply URL-restored filter state to UI
    if (activeFilter !== 'all') {{
      const btn = document.querySelector(`[data-filter="${{activeFilter}}"]`);
      if (btn) {{ filterBtns.forEach(b=>b.classList.remove('active','all-active')); btn.classList.add('active'); }}
    }}
    if (activeRegion !== 'all') {{
      const btn = document.querySelector(`[data-region="${{activeRegion}}"]`);
      if (btn) {{ regionBtns.forEach(b=>b.classList.remove('region-active')); btn.classList.add('region-active'); }}
    }}
    if (showSavedOnly) btnSaved.classList.add('saved-active');
    update();
  </script>
</body>
</html>"""

    index_path = os.path.join(DOCS_DIR, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Site generated: {index_path} ({len(articles)} articles)")

    generate_feed(articles)
    generate_sitemap(articles)
    generate_digest(articles)
    from generate_newsletter import generate_newsletter
    generate_newsletter(articles)


if __name__ == "__main__":
    with open(os.path.join(os.path.dirname(__file__), "articles.json")) as f:
        articles = json.load(f)
    generate_site(articles)
