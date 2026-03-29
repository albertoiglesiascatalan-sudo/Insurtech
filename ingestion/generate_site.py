"""Generates static HTML + RSS feed for GitHub Pages from articles list."""
import os
import json
from datetime import datetime, timezone, timedelta
from collections import Counter

from xml.sax.saxutils import escape as xml_escape

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


def _card(a: dict, featured: bool = False) -> str:
    category = a.get("category", "General")
    summary  = a.get("summary", "")
    read_min = _read_minutes(a["title"] + " " + summary)
    new_badge = '<span class="badge-new">Nuevo</span>' if _is_new(a.get("published_at", "")) else ""
    twitter_url, linkedin_url = _share_urls(a["title"], a["url"])
    searchable = f"{a['title']} {summary} {a['source']}".lower().replace('"', '')
    article_id = a.get("id", "")

    region = "ibero" if a.get("source", "") in IBERO_SOURCES else "global"
    extra_class = " card-featured" if featured else ""
    return f"""
    <article class="card{extra_class}" data-category="{category}" data-region="{region}" data-search="{searchable}" data-id="{article_id}">
      <div class="card-meta">
        <span class="card-source">{a['source']}</span>
        <span class="card-dot">·</span>
        <span class="card-date">{_date(a['published_at'])}</span>
        <span class="card-dot">·</span>
        <span class="card-read">{read_min} min</span>
        {new_badge}
        <span class="card-tag">{category}</span>
      </div>
      <h2 class="card-title">
        <a href="{a['url']}" target="_blank" rel="noopener">{a['title']}</a>
      </h2>
      {"<p class='card-summary'>" + summary + "</p>" if summary else ""}
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
    """Generate RSS feed XML."""
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
        items.append(f"""  <item>
    <title>{xml_escape(a['title'])}</title>
    <link>{xml_escape(a['url'])}</link>
    <description>{desc}</description>
    <pubDate>{pub_rfc}</pubDate>
    <guid>{xml_escape(a['url'])}</guid>
    <category>{xml_escape(a.get('category', 'General'))}</category>
  </item>""")

    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
  <title>InsurTech Intelligence</title>
  <link>{SITE_URL}</link>
  <description>Noticias globales de insurtech, actualizadas cada 6 horas.</description>
  <language>en</language>
  <lastBuildDate>{now_rfc}</lastBuildDate>
  <atom:link href="{SITE_URL}/feed.xml" rel="self" type="application/rss+xml"/>
{chr(10).join(items)}
</channel>
</rss>"""
    feed_path = os.path.join(DOCS_DIR, "feed.xml")
    with open(feed_path, "w", encoding="utf-8") as f:
        f.write(feed)
    print(f"RSS feed generated: {feed_path}")


def _thermometer(articles: list) -> str:
    """Weekly pulse widget — counts by category over last 7 days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    week = []
    for a in articles:
        try:
            pub = datetime.fromisoformat(a.get("published_at", ""))
            if pub.tzinfo is None:
                pub = pub.replace(tzinfo=timezone.utc)
            if pub >= cutoff:
                week.append(a)
        except Exception:
            pass

    if not week:
        return ""

    counts = Counter(a.get("category", "General") for a in week)
    ibero  = sum(1 for a in week if a.get("source", "") in IBERO_SOURCES)
    total  = len(week)

    metrics = [
        ("💰", "Inversión",   counts.get("Inversión", 0),   "Rondas y M&A"),
        ("⚖️",  "Regulación", counts.get("Regulación", 0),  "Noticias regulatorias"),
        ("🚀", "Tecnología",  counts.get("Tecnología", 0),  "Lanzamientos tech"),
        ("🌎", "Iberoamérica",ibero,                         "Noticias España/Latam"),
    ]

    bars = ""
    for icon, label, n, desc in metrics:
        pct = min(100, int(n / max(total, 1) * 100 * 4))  # scale to make it visible
        pct = max(4, pct)
        bars += f"""
      <div class="therm-row">
        <span class="therm-icon">{icon}</span>
        <div class="therm-info">
          <span class="therm-label">{label}</span>
          <span class="therm-desc">{desc}</span>
        </div>
        <div class="therm-bar-wrap">
          <div class="therm-bar" style="width:{pct}%"></div>
        </div>
        <span class="therm-n">{n}</span>
      </div>"""

    return f"""
  <section class="thermometer">
    <div class="therm-header">
      <span class="therm-title">🌡️ Termómetro Insurtech</span>
      <span class="therm-sub">Últimos 7 días · {total} artículos analizados</span>
    </div>
    <div class="therm-body">{bars}
    </div>
  </section>"""


def _startup_card(articles: list) -> str:
    """Pick the most recent Inversión article as Startup de la semana."""
    candidates = [a for a in articles if a.get("category") == "Inversión"]
    if not candidates:
        return ""
    a = candidates[0]
    summary = a.get("summary", "")
    twitter_url, linkedin_url = _share_urls(a["title"], a["url"])
    return f"""
  <section class="startup-card">
    <div class="startup-label">🚀 Startup / Deal de la semana</div>
    <h3 class="startup-title">
      <a href="{a['url']}" target="_blank" rel="noopener">{a['title']}</a>
    </h3>
    {"<p class='startup-summary'>" + summary + "</p>" if summary else ""}
    <div class="startup-footer">
      <span class="startup-source">{a['source']} · {_date(a['published_at'])}</span>
      <div class="card-share">
        <a href="{twitter_url}" target="_blank" rel="noopener" class="share-btn share-x" title="Compartir en X">𝕏</a>
        <a href="{linkedin_url}" target="_blank" rel="noopener" class="share-btn share-li" title="Compartir en LinkedIn">in</a>
      </div>
    </div>
  </section>"""


def generate_site(articles: list):
    os.makedirs(DOCS_DIR, exist_ok=True)
    updated = datetime.utcnow().strftime("%d %b %Y · %H:%M UTC")
    new_count = sum(1 for a in articles if _is_new(a.get("published_at", "")))

    thermometer_html = _thermometer(articles)
    startup_html     = _startup_card(articles)
    ibero_count      = sum(1 for a in articles if a.get("source", "") in IBERO_SOURCES)

    featured = articles[0] if articles else None
    rest     = articles[1:] if articles else []

    counts = Counter(a.get("category", "General") for a in articles)
    filter_buttons = '\n      '.join(
        f'<button class="filter-btn" data-filter="{c}">{c} <span class="count">{counts[c]}</span></button>'
        for c in CATEGORIES if counts[c] > 0
    )

    featured_html = _card(featured, featured=True) if featured else ""
    cards_html    = "\n".join(_card(a) for a in rest)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>InsurTech Intelligence</title>
  <meta name="description" content="Noticias globales de insurtech, actualizadas cada 6 horas." />
  <link rel="alternate" type="application/rss+xml" title="InsurTech Intelligence RSS" href="{SITE_URL}/feed.xml" />
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
    .toolbar {{ max-width: 900px; margin: 1.5rem auto 0; padding: 0 1rem; display: flex; flex-direction: column; gap: .7rem; }}
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
    .card-summary {{ font-size: .88rem; color: var(--muted); margin-bottom: .9rem; }}
    .card-actions {{ display: flex; align-items: center; justify-content: space-between; }}
    .card-link {{ font-size: .82rem; color: var(--accent); font-weight: 500; text-decoration: none; }}
    .card-link:hover {{ text-decoration: underline; }}
    .card-share {{ display: flex; gap: .4rem; align-items: center; }}
    .share-btn {{ display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; border-radius: 6px; font-size: .75rem; font-weight: 700; text-decoration: none; border: 1.5px solid var(--border); background: var(--surface); color: var(--muted); cursor: pointer; transition: all .15s; }}
    .share-btn:hover {{ border-color: var(--accent); color: var(--accent); }}
    .save-btn.saved {{ background: var(--accent); border-color: var(--accent); color: white; }}
    .no-results {{ text-align: center; color: var(--muted); padding: 3rem; display: none; grid-column: 1/-1; }}

    /* Thermometer */
    .thermometer {{
      max-width: 900px; margin: 1.25rem auto 0; padding: 0 1rem;
    }}
    .thermometer > div {{
      background: var(--surface); border: 1px solid var(--border);
      border-radius: 12px; padding: 1.1rem 1.4rem;
    }}
    .therm-header {{ display: flex; align-items: baseline; justify-content: space-between; margin-bottom: .9rem; flex-wrap: wrap; gap: .3rem; }}
    .therm-title {{ font-size: .95rem; font-weight: 700; color: var(--text); }}
    .therm-sub   {{ font-size: .75rem; color: var(--muted); }}
    .therm-row   {{ display: flex; align-items: center; gap: .7rem; margin-bottom: .55rem; }}
    .therm-icon  {{ font-size: 1rem; width: 1.4rem; text-align: center; flex-shrink: 0; }}
    .therm-info  {{ display: flex; flex-direction: column; width: 110px; flex-shrink: 0; }}
    .therm-label {{ font-size: .78rem; font-weight: 600; color: var(--text); line-height: 1.2; }}
    .therm-desc  {{ font-size: .68rem; color: var(--muted); line-height: 1.2; }}
    .therm-bar-wrap {{ flex: 1; background: var(--border); border-radius: 4px; height: 7px; overflow: hidden; }}
    .therm-bar  {{ height: 100%; background: var(--accent); border-radius: 4px; transition: width .4s; }}
    .therm-n    {{ font-size: .82rem; font-weight: 700; color: var(--accent); width: 1.8rem; text-align: right; flex-shrink: 0; }}

    /* Startup de la semana */
    .startup-card {{
      max-width: 900px; margin: 1rem auto 0; padding: 0 1rem;
    }}
    .startup-card > section, .startup-card {{
      background: linear-gradient(135deg, #1a1a2e 0%, #2d3561 100%);
      border-radius: 12px; padding: 1.4rem; color: white;
    }}
    @media (prefers-color-scheme: dark) {{
      .startup-card {{ background: linear-gradient(135deg, #0d0f18 0%, #1e2340 100%); }}
    }}
    .startup-label {{ font-size: .75rem; font-weight: 700; color: #a0aec0; text-transform: uppercase; letter-spacing: .5px; margin-bottom: .5rem; }}
    .startup-title {{ font-size: 1.1rem; font-weight: 700; line-height: 1.4; margin-bottom: .6rem; }}
    .startup-title a {{ color: white; text-decoration: none; }}
    .startup-title a:hover {{ text-decoration: underline; }}
    .startup-summary {{ font-size: .88rem; color: #a0aec0; margin-bottom: .9rem; line-height: 1.5; }}
    .startup-footer {{ display: flex; align-items: center; justify-content: space-between; }}
    .startup-source {{ font-size: .75rem; color: #718096; }}
    .startup-card .share-btn {{ border-color: rgba(255,255,255,.2); color: #a0aec0; background: transparent; }}
    .startup-card .share-btn:hover {{ border-color: white; color: white; }}

    footer {{ text-align: center; padding: 2rem; font-size: .8rem; color: var(--muted); border-top: 1px solid var(--border); }}
    footer a {{ color: var(--accent); text-decoration: none; }}

    @media (max-width: 600px) {{
      header h1 {{ font-size: 1.5rem; }}
      .card {{ padding: 1rem; }}
      main.grid-view {{ grid-template-columns: 1fr; }}
      .rss-link {{ display: none; }}
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
      <span class="stat"><strong>40</strong> fuentes monitorizadas</span>
      <span class="stat"><strong>{ibero_count}</strong> noticias iberoamérica</span>
    </div>
    <div class="updated">Actualizado el {updated}</div>
    <div id="google_translate_element"></div>
  </header>

  <div class="toolbar">
    <div class="search-row">
      <input id="search" type="search" placeholder="Buscar artículos..." autocomplete="off" />
      <div class="view-toggle">
        <button class="view-btn active" id="btn-list" title="Vista lista">&#9776;</button>
        <button class="view-btn" id="btn-grid" title="Vista grid">&#9638;</button>
      </div>
    </div>
    <div class="filters">
      <button class="filter-btn all-active" data-filter="all">Todos <span class="count">{len(articles)}</span></button>
      {filter_buttons}
    </div>
    <div class="filters region-filters">
      <button class="region-btn region-active" data-region="all">🌍 Todo el mundo</button>
      <button class="region-btn" data-region="ibero">🌎 Iberoamérica <span class="count">{ibero_count}</span></button>
      <button class="region-btn" data-region="global">🌐 Global <span class="count">{len(articles) - ibero_count}</span></button>
      <a href="{SITE_URL}/feed.xml" class="rss-link" target="_blank">&#x2609; RSS</a>
    </div>
  </div>

  {thermometer_html}
  {startup_html}

  <div class="subscribe-bar">
    <form class="subscribe-form" action="https://buttondown.email/api/emails/embed-subscribe/insurtechintelligence" method="post" target="_blank">
      <span>📬 Recibe las noticias en tu email:</span>
      <input type="email" name="email" placeholder="tu@email.com" required />
      <button type="submit">Suscribirse gratis</button>
    </form>
  </div>

  <main class="list-view" id="main">
    {featured_html}
    {cards_html if articles else '<p style="text-align:center;color:var(--muted);padding:3rem">Sin artículos por ahora.</p>'}
    <p class="no-results" id="no-results">No hay artículos que coincidan.</p>
  </main>

  <footer>
    InsurTech Intelligence · Impulsado por IA · <a href="{SITE_URL}/feed.xml">RSS Feed</a>
  </footer>

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
    // ── Filters + Search ──
    const cards       = Array.from(document.querySelectorAll('.card'));
    const filterBtns  = Array.from(document.querySelectorAll('.filter-btn'));
    const regionBtns  = Array.from(document.querySelectorAll('.region-btn'));
    const search      = document.getElementById('search');
    const noResults   = document.getElementById('no-results');
    const mainEl      = document.getElementById('main');
    let activeFilter  = 'all';
    let activeRegion  = 'all';
    let searchQuery   = '';

    function update() {{
      let visible = 0;
      cards.forEach(card => {{
        const matchFilter = activeFilter === 'all' || card.dataset.category === activeFilter;
        const matchRegion = activeRegion === 'all' || card.dataset.region === activeRegion;
        const matchSearch = !searchQuery || card.dataset.search.includes(searchQuery);
        const show = matchFilter && matchRegion && matchSearch;
        card.classList.toggle('hidden', !show);
        if (show) visible++;
      }});
      noResults.style.display = visible === 0 ? 'block' : 'none';
    }}

    filterBtns.forEach(btn => {{
      btn.addEventListener('click', () => {{
        activeFilter = btn.dataset.filter;
        filterBtns.forEach(b => b.classList.remove('active', 'all-active'));
        btn.classList.add(activeFilter === 'all' ? 'all-active' : 'active');
        update();
      }});
    }});

    regionBtns.forEach(btn => {{
      btn.addEventListener('click', () => {{
        activeRegion = btn.dataset.region;
        regionBtns.forEach(b => b.classList.remove('region-active'));
        btn.classList.add('region-active');
        update();
      }});
    }});
    search.addEventListener('input', () => {{ searchQuery = search.value.trim().toLowerCase(); update(); }});

    // ── View toggle ──
    document.getElementById('btn-list').addEventListener('click', () => {{
      mainEl.className = 'list-view';
      document.getElementById('btn-list').classList.add('active');
      document.getElementById('btn-grid').classList.remove('active');
    }});
    document.getElementById('btn-grid').addEventListener('click', () => {{
      mainEl.className = 'grid-view';
      document.getElementById('btn-grid').classList.add('active');
      document.getElementById('btn-list').classList.remove('active');
    }});

    // ── Bookmarks (localStorage) ──
    const SAVED_KEY = 'insurtech_saved';
    function getSaved() {{ try {{ return JSON.parse(localStorage.getItem(SAVED_KEY) || '[]'); }} catch {{ return []; }} }}
    function setSaved(ids) {{ localStorage.setItem(SAVED_KEY, JSON.stringify(ids)); }}

    function initBookmarks() {{
      const saved = getSaved();
      document.querySelectorAll('.save-btn').forEach(btn => {{
        const id = btn.dataset.id;
        if (saved.includes(id)) btn.classList.add('saved');
        btn.addEventListener('click', () => {{
          let s = getSaved();
          if (s.includes(id)) {{ s = s.filter(x => x !== id); btn.classList.remove('saved'); }}
          else {{ s.push(id); btn.classList.add('saved'); }}
          setSaved(s);
        }});
      }});
    }}
    initBookmarks();
  </script>
</body>
</html>"""

    index_path = os.path.join(DOCS_DIR, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Site generated: {index_path} ({len(articles)} articles)")

    generate_feed(articles)


if __name__ == "__main__":
    with open(os.path.join(os.path.dirname(__file__), "articles.json")) as f:
        articles = json.load(f)
    generate_site(articles)
