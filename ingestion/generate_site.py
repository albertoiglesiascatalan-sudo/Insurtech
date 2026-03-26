"""Generates static HTML for GitHub Pages from articles list."""
import os
import json
from datetime import datetime

DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "docs")


def _date(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).strftime("%b %d, %Y")
    except Exception:
        return ""


def _card(a: dict) -> str:
    return f"""
    <article class="card">
      <div class="card-meta">{a['source']} · {_date(a['published_at'])}</div>
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
    updated = datetime.utcnow().strftime("%b %d, %Y at %H:%M UTC")
    cards_html = "\n".join(_card(a) for a in articles)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>InsurTech Intelligence</title>
  <meta name="description" content="Noticias globales de insurtech con resúmenes en español generados por IA, actualizadas cada 6 horas." />
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
      padding: 2rem 1rem;
      text-align: center;
    }}
    header h1 {{ font-size: 2rem; font-weight: 700; letter-spacing: -0.5px; }}
    header p  {{ margin-top: .5rem; color: #a0aec0; font-size: .95rem; }}
    .updated  {{ margin-top: .75rem; font-size: .8rem; color: #718096; }}
    main {{
      max-width: 860px;
      margin: 2rem auto;
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
    .card-meta  {{ font-size: .78rem; color: #718096; margin-bottom: .5rem; text-transform: uppercase; letter-spacing: .5px; }}
    .card-title {{ font-size: 1.15rem; font-weight: 600; margin-bottom: .75rem; line-height: 1.4; }}
    .card-title a {{ color: #1a1a2e; text-decoration: none; }}
    .card-title a:hover {{ color: #4a6fa5; }}
    .card-summary {{ font-size: .92rem; color: #4a5568; margin-bottom: 1rem; }}
    .card-link  {{ font-size: .85rem; color: #4a6fa5; font-weight: 500; text-decoration: none; }}
    .card-link:hover {{ text-decoration: underline; }}
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
  </header>

  <main>
    {cards_html if articles else '<p style="text-align:center;color:#718096;padding:3rem">Sin artículos por ahora. Vuelve pronto.</p>'}
  </main>

  <footer>
    InsurTech Intelligence · Impulsado por IA · Actualizado cada 6 horas
  </footer>
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
