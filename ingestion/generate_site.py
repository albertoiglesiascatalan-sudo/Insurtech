"""Generates static HTML for GitHub Pages from articles list."""
import os
import json
from datetime import datetime

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
    return f"""
    <article class="card" data-category="{category}">
      <div class="card-meta">
        <span class="card-source">{a['source']}</span>
        <span class="card-date">{_date(a['published_at'])}</span>
        <span class="card-tag">{category}</span>
      </div>
      <h2 class="card-title">
        <a href="{a['url']}" target="_blank" rel="noopener">{a['title']}</a>
      </h2>
      <p class="card-summary">{a.get('summary', '')}</p>
      <a href="{a['url']}" target="_blank" rel="noopener" class="card-link">
        Leer artículo completo →
      </a>
    </article>"""


def generate_site(articles: list):
    os.makedirs(DOCS_DIR, exist_ok=True)
    updated = datetime.utcnow().strftime("%d %b %Y a las %H:%M UTC")
    cards_html = "\n".join(_card(a) for a in articles)

    # Only show categories that have at least one article
    used_categories = {a.get("category", "General") for a in articles}
    filter_buttons = '\n    '.join(
        f'<button class="filter-btn" data-filter="{c}">{c}</button>'
        for c in CATEGORIES if c in used_categories
    )

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>InsurTech Intelligence</title>
  <meta name="description" content="Noticias globales de insurtech con resúmenes en español generados por IA, actualizadas cada 6 horas." />
  <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
  <meta http-equiv="Pragma" content="no-cache" />
  <meta http-equiv="Expires" content="0" />
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f8f9fa;
      color: #1a1a2e;
      line-height: 1.6;
    }}
    header {{
      background: #1a1a2e;
      color: white;
      padding: 2rem 1rem 1.5rem;
      text-align: center;
    }}
    header h1 {{ font-size: 2rem; font-weight: 700; letter-spacing: -0.5px; }}
    header p  {{ margin-top: .5rem; color: #a0aec0; font-size: .95rem; }}
    .updated  {{ margin-top: .75rem; font-size: .8rem; color: #718096; }}
    #google_translate_element {{
      margin-top: 1.25rem;
      display: flex;
      justify-content: center;
    }}
    .goog-te-gadget {{ font-family: inherit !important; color: transparent !important; }}
    .goog-te-gadget-simple {{
      background: transparent !important;
      border: 1.5px solid rgba(255,255,255,0.25) !important;
      border-radius: 20px !important;
      padding: .4rem 1rem !important;
      font-size: .82rem !important;
      font-family: inherit !important;
      cursor: pointer !important;
    }}
    .goog-te-gadget-simple .goog-te-menu-value {{
      color: #a0aec0 !important;
      letter-spacing: .3px;
    }}
    .goog-te-gadget-simple .goog-te-menu-value span:first-child {{
      color: white !important;
      font-weight: 500 !important;
    }}
    .goog-te-gadget-simple img {{ display: none !important; }}
    .goog-te-gadget-simple .goog-te-menu-value span[style] {{ color: rgba(255,255,255,0.3) !important; }}
    .filters {{
      max-width: 860px;
      margin: 1.5rem auto 0;
      padding: 0 1rem;
      display: flex;
      flex-wrap: wrap;
      gap: .5rem;
    }}
    .filter-btn {{
      background: white;
      border: 1.5px solid #e2e8f0;
      border-radius: 20px;
      padding: .35rem .9rem;
      font-size: .82rem;
      font-weight: 500;
      color: #4a5568;
      cursor: pointer;
      transition: all .15s;
    }}
    .filter-btn:hover {{ border-color: #4a6fa5; color: #4a6fa5; }}
    .filter-btn.active {{
      background: #1a1a2e;
      border-color: #1a1a2e;
      color: white;
    }}
    .filter-btn.all-btn {{
      background: #1a1a2e;
      border-color: #1a1a2e;
      color: white;
    }}
    main {{
      max-width: 860px;
      margin: 1.25rem auto 2rem;
      padding: 0 1rem;
      display: grid;
      gap: 1.25rem;
    }}
    .card {{
      background: white;
      border-radius: 10px;
      padding: 1.5rem;
      border: 1px solid #e2e8f0;
      transition: box-shadow .2s;
    }}
    .card:hover {{ box-shadow: 0 4px 20px rgba(0,0,0,.08); }}
    .card.hidden {{ display: none; }}
    .card-meta {{
      display: flex;
      align-items: center;
      gap: .5rem;
      flex-wrap: wrap;
      margin-bottom: .6rem;
    }}
    .card-source {{ font-size: .78rem; color: #718096; text-transform: uppercase; letter-spacing: .5px; }}
    .card-date   {{ font-size: .78rem; color: #a0aec0; }}
    .card-tag {{
      font-size: .72rem;
      font-weight: 600;
      background: #eef2ff;
      color: #4a6fa5;
      border-radius: 10px;
      padding: .15rem .55rem;
      margin-left: auto;
    }}
    .card-title {{ font-size: 1.15rem; font-weight: 600; margin-bottom: .75rem; line-height: 1.4; }}
    .card-title a {{ color: #1a1a2e; text-decoration: none; }}
    .card-title a:hover {{ color: #4a6fa5; }}
    .card-summary {{ font-size: .92rem; color: #4a5568; margin-bottom: 1rem; }}
    .card-link  {{ font-size: .85rem; color: #4a6fa5; font-weight: 500; text-decoration: none; }}
    .card-link:hover {{ text-decoration: underline; }}
    .no-results {{
      text-align: center;
      color: #718096;
      padding: 3rem;
      display: none;
    }}
    footer {{
      text-align: center;
      padding: 2rem;
      font-size: .82rem;
      color: #a0aec0;
    }}
    @media (max-width: 600px) {{
      header h1 {{ font-size: 1.5rem; }}
      .card {{ padding: 1rem; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>InsurTech Intelligence</h1>
    <p>Noticias globales de insurtech · Resúmenes en español con IA · {len(articles)} artículos</p>
    <div class="updated">Actualizado el {updated}</div>
    <div id="google_translate_element"></div>
  </header>

  <div class="filters">
    <button class="filter-btn all-btn" data-filter="all">Todos</button>
    {filter_buttons}
  </div>

  <main>
    {cards_html if articles else '<p style="text-align:center;color:#718096;padding:3rem">Sin artículos por ahora. Vuelve pronto.</p>'}
    <p class="no-results" id="no-results">No hay artículos en esta categoría.</p>
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
    const btns = document.querySelectorAll('.filter-btn');
    const cards = document.querySelectorAll('.card');
    const noResults = document.getElementById('no-results');

    btns.forEach(btn => {{
      btn.addEventListener('click', () => {{
        const filter = btn.dataset.filter;
        btns.forEach(b => b.classList.remove('active', 'all-btn'));
        btn.classList.add(filter === 'all' ? 'all-btn' : 'active');

        let visible = 0;
        cards.forEach(card => {{
          const show = filter === 'all' || card.dataset.category === filter;
          card.classList.toggle('hidden', !show);
          if (show) visible++;
        }});
        noResults.style.display = visible === 0 ? 'block' : 'none';
      }});
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
