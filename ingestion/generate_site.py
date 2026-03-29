"""Generates static HTML for GitHub Pages from articles list."""
import os
import json
from datetime import datetime
from collections import Counter

DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "docs")

CATEGORIES = [
    "Tecnología", "Regulación", "Inversión", "Vida y Salud",
    "Automóvil", "Catástrofes", "Fraude", "Embebido", "General",
]


def _date(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).strftime("%d %b %Y")
    except Exception:
        return ""


def _card(a: dict) -> str:
    category = a.get("category", "General")
    title = a['title'].replace('"', '&quot;')
    summary = a.get('summary', '')
    searchable = f"{a['title']} {summary} {a['source']}".lower().replace('"', '')
    return f"""
    <article class="card" data-category="{category}" data-search="{searchable}">
      <div class="card-meta">
        <span class="card-source">{a['source']}</span>
        <span class="card-dot">·</span>
        <span class="card-date">{_date(a['published_at'])}</span>
        <span class="card-tag">{category}</span>
      </div>
      <h2 class="card-title">
        <a href="{a['url']}" target="_blank" rel="noopener">{a['title']}</a>
      </h2>
      {"<p class='card-summary'>" + summary + "</p>" if summary else ""}
      <a href="{a['url']}" target="_blank" rel="noopener" class="card-link">
        Leer artículo completo →
      </a>
    </article>"""


def generate_site(articles: list):
    os.makedirs(DOCS_DIR, exist_ok=True)
    updated = datetime.utcnow().strftime("%d %b %Y · %H:%M UTC")
    cards_html = "\n".join(_card(a) for a in articles)

    counts = Counter(a.get("category", "General") for a in articles)
    filter_buttons = '\n    '.join(
        f'<button class="filter-btn" data-filter="{c}">{c} <span class="count">{counts[c]}</span></button>'
        for c in CATEGORIES if counts[c] > 0
    )

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>InsurTech Intelligence</title>
  <meta name="description" content="Noticias globales de insurtech, actualizadas cada 6 horas." />
  <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    /* ── Colour tokens ── */
    :root {{
      --bg: #f4f6f9;
      --surface: #ffffff;
      --border: #e2e8f0;
      --text: #1a1a2e;
      --text-muted: #64748b;
      --accent: #4a6fa5;
      --header-bg: #1a1a2e;
      --tag-bg: #eef2ff;
      --tag-color: #4a6fa5;
      --count-bg: rgba(255,255,255,0.15);
    }}
    @media (prefers-color-scheme: dark) {{
      :root {{
        --bg: #0f1117;
        --surface: #1a1d27;
        --border: #2d3148;
        --text: #e2e8f0;
        --text-muted: #8892a4;
        --accent: #7aa2d4;
        --header-bg: #0d0f18;
        --tag-bg: #1e2340;
        --tag-color: #7aa2d4;
        --count-bg: rgba(0,0,0,0.25);
      }}
    }}

    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.6;
    }}

    /* ── Header ── */
    header {{
      background: var(--header-bg);
      color: white;
      padding: 2rem 1rem 1.5rem;
      text-align: center;
    }}
    header h1 {{ font-size: 2rem; font-weight: 700; letter-spacing: -0.5px; }}
    header p   {{ margin-top: .4rem; color: #a0aec0; font-size: .92rem; }}
    .updated   {{ margin-top: .5rem; font-size: .78rem; color: #718096; }}

    /* ── Translate widget ── */
    #google_translate_element {{ margin-top: 1.1rem; display: flex; justify-content: center; }}
    .goog-te-gadget {{ font-family: inherit !important; color: transparent !important; font-size: 0 !important; }}
    .goog-te-gadget-simple {{
      background: transparent !important;
      border: 1.5px solid rgba(255,255,255,0.2) !important;
      border-radius: 20px !important;
      padding: .35rem 1rem !important;
      font-size: .8rem !important;
      font-family: inherit !important;
      cursor: pointer !important;
    }}
    .goog-te-gadget-simple .goog-te-menu-value {{ color: #a0aec0 !important; }}
    .goog-te-gadget-simple .goog-te-menu-value span:first-child {{ color: white !important; font-weight: 500 !important; }}
    .goog-te-gadget-simple .goog-te-menu-value span[style] {{ color: rgba(255,255,255,0.2) !important; }}
    .goog-te-gadget-simple img {{ display: none !important; }}
    .goog-te-banner-frame {{ display: none !important; }}
    body {{ top: 0 !important; }}

    /* ── Toolbar (search + filters + view toggle) ── */
    .toolbar {{
      max-width: 900px;
      margin: 1.5rem auto 0;
      padding: 0 1rem;
      display: flex;
      flex-direction: column;
      gap: .75rem;
    }}
    .search-row {{
      display: flex;
      align-items: center;
      gap: .6rem;
    }}
    #search {{
      flex: 1;
      padding: .5rem 1rem;
      border: 1.5px solid var(--border);
      border-radius: 20px;
      background: var(--surface);
      color: var(--text);
      font-size: .88rem;
      font-family: inherit;
      outline: none;
      transition: border-color .15s;
    }}
    #search:focus {{ border-color: var(--accent); }}
    #search::placeholder {{ color: var(--text-muted); }}
    .view-toggle {{
      display: flex;
      gap: .3rem;
    }}
    .view-btn {{
      background: var(--surface);
      border: 1.5px solid var(--border);
      border-radius: 8px;
      padding: .4rem .55rem;
      cursor: pointer;
      color: var(--text-muted);
      transition: all .15s;
      line-height: 1;
      font-size: 1rem;
    }}
    .view-btn.active {{ border-color: var(--accent); color: var(--accent); }}
    .filters {{
      display: flex;
      flex-wrap: wrap;
      gap: .45rem;
    }}
    .filter-btn {{
      background: var(--surface);
      border: 1.5px solid var(--border);
      border-radius: 20px;
      padding: .3rem .85rem;
      font-size: .8rem;
      font-weight: 500;
      color: var(--text-muted);
      cursor: pointer;
      transition: all .15s;
      display: flex;
      align-items: center;
      gap: .35rem;
    }}
    .filter-btn:hover {{ border-color: var(--accent); color: var(--accent); }}
    .filter-btn.active, .filter-btn.all-active {{
      background: var(--accent);
      border-color: var(--accent);
      color: white;
    }}
    .filter-btn .count {{
      font-size: .72rem;
      background: var(--count-bg);
      border-radius: 10px;
      padding: .05rem .4rem;
      font-weight: 600;
    }}
    .filter-btn.active .count, .filter-btn.all-active .count {{
      background: rgba(255,255,255,0.25);
    }}

    /* ── Cards grid ── */
    main {{
      max-width: 900px;
      margin: 1.25rem auto 2rem;
      padding: 0 1rem;
      display: grid;
      gap: 1rem;
    }}
    main.list-view {{ grid-template-columns: 1fr; }}
    main.grid-view {{ grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); }}
    .card {{
      background: var(--surface);
      border-radius: 12px;
      padding: 1.4rem;
      border: 1px solid var(--border);
      transition: box-shadow .2s, transform .15s;
    }}
    .card:hover {{ box-shadow: 0 4px 20px rgba(0,0,0,.08); transform: translateY(-1px); }}
    .card.hidden {{ display: none; }}
    .card-meta {{
      display: flex;
      align-items: center;
      gap: .4rem;
      flex-wrap: wrap;
      margin-bottom: .55rem;
    }}
    .card-source {{ font-size: .75rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: .5px; font-weight: 600; }}
    .card-dot    {{ color: var(--border); font-size: .75rem; }}
    .card-date   {{ font-size: .75rem; color: var(--text-muted); }}
    .card-tag {{
      font-size: .7rem;
      font-weight: 600;
      background: var(--tag-bg);
      color: var(--tag-color);
      border-radius: 10px;
      padding: .12rem .5rem;
      margin-left: auto;
    }}
    .card-title {{ font-size: 1.05rem; font-weight: 600; margin-bottom: .6rem; line-height: 1.45; }}
    .card-title a {{ color: var(--text); text-decoration: none; }}
    .card-title a:hover {{ color: var(--accent); }}
    .card-summary {{ font-size: .88rem; color: var(--text-muted); margin-bottom: .9rem; }}
    .card-link {{ font-size: .82rem; color: var(--accent); font-weight: 500; text-decoration: none; }}
    .card-link:hover {{ text-decoration: underline; }}
    .no-results {{
      text-align: center;
      color: var(--text-muted);
      padding: 3rem;
      display: none;
      grid-column: 1/-1;
    }}

    footer {{
      text-align: center;
      padding: 2rem;
      font-size: .8rem;
      color: var(--text-muted);
      border-top: 1px solid var(--border);
    }}
    @media (max-width: 600px) {{
      header h1 {{ font-size: 1.5rem; }}
      .card {{ padding: 1rem; }}
      main.grid-view {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>InsurTech Intelligence</h1>
    <p>Noticias globales de insurtech · {len(articles)} artículos</p>
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
  </div>

  <main class="list-view" id="main">
    {cards_html if articles else '<p style="text-align:center;color:var(--text-muted);padding:3rem">Sin artículos por ahora.</p>'}
    <p class="no-results" id="no-results">No hay artículos que coincidan.</p>
  </main>

  <footer>
    InsurTech Intelligence · Impulsado por IA · Actualizado cada 6 horas
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
    const cards     = Array.from(document.querySelectorAll('.card'));
    const filterBtns = Array.from(document.querySelectorAll('.filter-btn'));
    const search    = document.getElementById('search');
    const noResults = document.getElementById('no-results');
    const mainEl    = document.getElementById('main');
    let activeFilter = 'all';
    let searchQuery  = '';

    function update() {{
      let visible = 0;
      cards.forEach(card => {{
        const matchFilter = activeFilter === 'all' || card.dataset.category === activeFilter;
        const matchSearch = !searchQuery || card.dataset.search.includes(searchQuery);
        const show = matchFilter && matchSearch;
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

    search.addEventListener('input', () => {{
      searchQuery = search.value.trim().toLowerCase();
      update();
    }});

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
  </script>
</body>
</html>"""

    index_path = os.path.join(DOCS_DIR, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Site generated: {index_path} ({len(articles)} articles)")


if __name__ == "__main__":
    with open(os.path.join(os.path.dirname(__file__), "articles.json")) as f:
        articles = json.load(f)
    generate_site(articles)
