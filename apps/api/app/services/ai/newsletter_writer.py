"""AI-powered editorial newsletter generation."""
import logging
from datetime import datetime, timedelta, timezone
from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_settings
from app.models.article import Article

logger = logging.getLogger(__name__)
settings = get_settings()

PROFILE_PROMPTS = {
    "investor": """You are the editor of InsurTech Intelligence, a premium newsletter for insurance
investors, VCs, and M&A professionals. Write a compelling daily/weekly digest focused on:
- Funding rounds, valuations, and M&A activity
- Market size data and growth metrics
- New market opportunities and competitive dynamics
- Regulatory changes that affect investment thesis
Use analytical tone, include specific numbers when available, highlight investment implications.""",

    "founder": """You are the editor of InsurTech Intelligence, a newsletter for insurtech founders
and product builders. Write a practical, inspiring digest focused on:
- Product launches and go-to-market strategies
- Technology innovations and implementation lessons
- Partnership announcements and distribution strategies
- Regulatory updates that affect product development
Use energetic, practical tone with actionable insights. Include "what this means for you" framing.""",

    "general": """You are the editor of InsurTech Intelligence, a newsletter for insurance
professionals and curious general readers. Write an accessible, engaging digest focused on:
- Big industry trends and what's changing
- Consumer-facing innovations in insurance
- Companies and people shaping the future of insurance
- Explainers on new insurance models
Use clear, jargon-free language. Make complex topics easy to understand.""",
}

SECTION_LABELS = {
    "funding-ma": "Funding & M&A",
    "ai-insurance": "AI in Insurance",
    "embedded-insurance": "Embedded Insurance",
    "regulatory-policy": "Regulatory Update",
    "product-launches": "Product Launches",
    "cyber-insurance": "Cyber Insurance",
    "health-tech": "Health InsurTech",
    "claims-tech": "Claims Tech",
    "underwriting-tech": "Underwriting Innovation",
    "climate-parametric": "Climate & Parametric",
}


async def generate_newsletter(
    db: AsyncSession,
    profile: str,
    frequency: str,
    edition_number: int = 1,
) -> dict:
    """
    Generate a full newsletter edition for a given reader profile.
    Returns: {"subject": str, "html_content": str}
    """
    # Fetch top articles for this profile
    days_back = 1 if frequency == "daily" else 7
    since = datetime.now(timezone.utc) - timedelta(days=days_back)

    result = await db.execute(
        select(Article)
        .where(
            Article.is_published == True,  # noqa: E712
            Article.is_duplicate == False,  # noqa: E712
            Article.is_processed == True,  # noqa: E712
            Article.reader_profiles.contains([profile]),
            Article.scraped_at >= since,
        )
        .order_by(Article.relevance_score.desc(), Article.published_at.desc())
        .limit(30)
    )
    articles = result.scalars().all()

    if not articles:
        logger.warning(f"No articles found for newsletter {profile}/{frequency}")
        return {}

    # Group by topic
    topic_groups: dict[str, list[Article]] = {}
    for article in articles:
        for topic in (article.topics or []):
            if topic not in topic_groups:
                topic_groups[topic] = []
            if len(topic_groups[topic]) < 4:
                topic_groups[topic].append(article)

    # Build context for AI
    article_summaries = []
    seen_ids = set()
    for article in articles[:20]:
        if article.id not in seen_ids:
            seen_ids.add(article.id)
            article_summaries.append(
                f"- [{article.title}]({article.url})\n  {article.summary_ai or article.content_raw or ''}"[:300]
            )

    articles_text = "\n".join(article_summaries)
    date_str = datetime.now(timezone.utc).strftime("%B %d, %Y")
    edition_label = "Daily" if frequency == "daily" else "Weekly"

    if not settings.openai_api_key:
        return _fallback_newsletter(profile, frequency, date_str, articles)

    try:
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.chat.completions.create(
            model=settings.openai_model_newsletter,
            messages=[
                {"role": "system", "content": PROFILE_PROMPTS[profile]},
                {
                    "role": "user",
                    "content": (
                        f"Create the {edition_label} InsurTech Intelligence newsletter for {date_str}.\n\n"
                        f"Here are the top articles to cover:\n{articles_text}\n\n"
                        f"Write a cohesive editorial newsletter with:\n"
                        f"1. A compelling opening (2-3 sentences on the week's theme)\n"
                        f"2. 3-5 story sections, each with a headline, 2-3 paragraph analysis, and why it matters\n"
                        f"3. A brief closing note\n"
                        f"Format as clean HTML suitable for email (use <h2>, <p>, <a href>, <strong> tags).\n"
                        f"Include article links inline. Keep total length under 1500 words."
                    ),
                },
            ],
            max_tokens=2500,
            temperature=0.7,
        )
        content = response.choices[0].message.content.strip()

        subject_response = await client.chat.completions.create(
            model=settings.openai_model_summarize,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Write a compelling email subject line (max 60 chars) for this insurtech "
                        f"newsletter aimed at {profile}s dated {date_str}. "
                        f"First article: {articles[0].title if articles else 'InsurTech news'}. "
                        f"Output only the subject line text."
                    ),
                }
            ],
            max_tokens=30,
            temperature=0.8,
        )
        subject = subject_response.choices[0].message.content.strip().strip('"')

        return {
            "subject": f"[InsurTech Intelligence] {subject}",
            "html_content": _wrap_email_html(content, profile, date_str, edition_label),
        }

    except Exception as e:
        logger.error(f"Newsletter generation failed: {e}")
        return _fallback_newsletter(profile, frequency, date_str, articles)


def _wrap_email_html(content: str, profile: str, date_str: str, edition: str) -> str:
    profile_labels = {"investor": "Investor Edition", "founder": "Founder Edition", "general": "General Edition"}
    label = profile_labels.get(profile, "")
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>InsurTech Intelligence</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color: #1a1a2e; margin: 0; padding: 0; background: #f5f5f5; }}
  .container {{ max-width: 680px; margin: 0 auto; background: #ffffff; }}
  .header {{ background: #1a1a2e; padding: 32px 40px; }}
  .header h1 {{ color: #00d4aa; margin: 0; font-size: 22px; font-weight: 700; letter-spacing: -0.5px; }}
  .header p {{ color: #8892b0; margin: 4px 0 0; font-size: 13px; }}
  .body {{ padding: 32px 40px; }}
  h2 {{ color: #1a1a2e; font-size: 18px; margin: 28px 0 8px; border-left: 3px solid #00d4aa; padding-left: 12px; }}
  p {{ line-height: 1.7; color: #444; font-size: 15px; margin: 0 0 16px; }}
  a {{ color: #00d4aa; text-decoration: none; font-weight: 500; }}
  .footer {{ background: #f9f9f9; padding: 24px 40px; border-top: 1px solid #eee; }}
  .footer p {{ font-size: 12px; color: #999; margin: 0; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>InsurTech Intelligence</h1>
    <p>{edition} Digest · {date_str} · {label}</p>
  </div>
  <div class="body">
    {content}
  </div>
  <div class="footer">
    <p>You're receiving this because you subscribed to InsurTech Intelligence.<br>
    <a href="{{{{unsubscribe_url}}}}">Unsubscribe</a> · <a href="https://insurtech.news">View in browser</a></p>
  </div>
</div>
</body>
</html>"""


def _fallback_newsletter(profile: str, frequency: str, date_str: str, articles: list) -> dict:
    items_html = "".join(
        f'<h2>{a.title}</h2><p>{a.summary_ai or a.content_raw or ""}</p>'
        f'<p><a href="{a.url}">Read more →</a></p>'
        for a in articles[:10]
    )
    content = f"<p>Here are this week's top insurtech stories:</p>{items_html}"
    return {
        "subject": f"[InsurTech Intelligence] {frequency.capitalize()} Digest - {date_str}",
        "html_content": _wrap_email_html(content, profile, date_str, frequency.capitalize()),
    }
