"""Seed sample articles for demo/development purposes."""
import asyncio
from datetime import datetime, timezone, timedelta
from app.database import AsyncSessionLocal
from app.models.article import Article
from app.models.source import Source
from sqlalchemy import select
from slugify import slugify

SAMPLE_ARTICLES = [
    {
        "title": "Lemonade Reports Record Q3 Revenue as AI Claims Processing Hits 95% Automation Rate",
        "url": "https://coverager.com/lemonade-q3-revenue-ai-claims",
        "content_raw": "Lemonade Inc. announced record third-quarter revenue of $113.8 million, a 19% year-over-year increase, driven by its AI-first approach to claims processing. The company's AI system, Jim, now handles 95% of claims automatically with an average settlement time of 3 minutes.",
        "summary_ai": "Lemonade posts record Q3 revenue of $113.8M (+19% YoY) as AI claims automation reaches 95%, settling most claims in under 3 minutes.",
        "image_url": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800",
        "author": "Editorial Team",
        "topics": ["ai-insurance", "claims-tech"],
        "regions": ["US"],
        "reader_profiles": ["investor", "founder"],
        "sentiment": "positive",
        "relevance_score": 0.93,
        "source_name": "Coverager",
        "days_ago": 1,
    },
    {
        "title": "Embedded Insurance Market to Reach $722 Billion by 2030, Driven by BNPL and EV Partnerships",
        "url": "https://www.insurtechmagazine.com/embedded-insurance-market-2030",
        "content_raw": "A new report from Juniper Research projects the embedded insurance market will reach $722 billion in gross written premiums by 2030, up from $63 billion in 2023. Growth is primarily driven by buy-now-pay-later platforms integrating return protection and electric vehicle manufacturers bundling comprehensive coverage.",
        "summary_ai": "Embedded insurance GWP projected to hit $722B by 2030 (from $63B today), fuelled by BNPL return protection and EV manufacturer bundles.",
        "image_url": "https://images.unsplash.com/photo-1563013544-824ae1b704d3?w=800",
        "author": "Research Desk",
        "topics": ["embedded-insurance", "partnerships"],
        "regions": ["global"],
        "reader_profiles": ["investor", "general"],
        "sentiment": "positive",
        "relevance_score": 0.96,
        "source_name": "InsurTech Magazine",
        "days_ago": 1,
    },
    {
        "title": "Wefox Raises €110M Series D to Expand Pan-European Digital Insurance Distribution",
        "url": "https://techcrunch.com/wefox-series-d-europe",
        "content_raw": "Berlin-based insurtech Wefox has secured €110 million in a Series D funding round led by Mubadala Investment Company, with participation from existing investors including Target Global and OMERS Ventures. The capital will fund expansion into five new European markets and the development of its AI-powered broker platform.",
        "summary_ai": "Wefox raises €110M Series D led by Mubadala to expand into 5 new EU markets and build out its AI broker platform.",
        "image_url": "https://images.unsplash.com/photo-1559526324-4b87b5e36e44?w=800",
        "author": "TC Staff",
        "topics": ["funding-ma", "distribution"],
        "regions": ["EU"],
        "reader_profiles": ["investor", "founder"],
        "sentiment": "positive",
        "relevance_score": 0.91,
        "source_name": "TechCrunch",
        "days_ago": 2,
    },
    {
        "title": "EIOPA Publishes New Guidelines on AI Use in Motor Insurance Pricing",
        "url": "https://www.eiopa.europa.eu/ai-motor-insurance-pricing-guidelines",
        "content_raw": "The European Insurance and Occupational Pensions Authority (EIOPA) has published comprehensive guidelines on the use of artificial intelligence in motor insurance pricing, requiring insurers to ensure AI models are explainable, non-discriminatory, and subject to regular human oversight. The guidelines take effect in Q2 2025.",
        "summary_ai": "EIOPA mandates explainability, fairness, and human oversight for AI pricing models in motor insurance — effective Q2 2025.",
        "image_url": "https://images.unsplash.com/photo-1450101499163-c8848c66ca85?w=800",
        "author": "EIOPA",
        "topics": ["regulatory-policy", "ai-insurance", "auto-insurance"],
        "regions": ["EU"],
        "reader_profiles": ["founder", "investor"],
        "sentiment": "neutral",
        "relevance_score": 0.88,
        "source_name": "EIOPA",
        "days_ago": 2,
    },
    {
        "title": "Parametric Flood Insurance Startup FloodFlash Launches in Germany and Netherlands",
        "url": "https://www.instech.london/floodflash-germany-netherlands",
        "content_raw": "UK-based parametric flood insurer FloodFlash has launched commercial operations in Germany and the Netherlands, marking its first expansion into continental Europe. The company uses IoT sensors installed at customer premises to trigger automatic claims payments when water depth exceeds a pre-agreed threshold.",
        "summary_ai": "FloodFlash expands parametric flood coverage to Germany and the Netherlands using IoT sensors for instant, threshold-triggered payouts.",
        "image_url": "https://images.unsplash.com/photo-1547683905-f686c993aae5?w=800",
        "author": "InsurTech London",
        "topics": ["climate-parametric", "product-launches"],
        "regions": ["EU"],
        "reader_profiles": ["founder", "investor", "general"],
        "sentiment": "positive",
        "relevance_score": 0.89,
        "source_name": "Instech London",
        "days_ago": 3,
    },
    {
        "title": "Cyber Insurance Premiums Fall 15% in 2024 Amid Improved Corporate Security Postures",
        "url": "https://www.dig-in.com/cyber-insurance-premiums-2024",
        "content_raw": "Cyber insurance premiums declined an average of 15% globally in 2024 as improved security postures, widespread MFA adoption, and better ransomware defences reduced loss ratios for insurers. The Swiss Re Institute reports that the cyber insurance market reached $15 billion in GWP despite the price decrease.",
        "summary_ai": "Cyber insurance premiums drop 15% in 2024 as MFA adoption and ransomware defences improve loss ratios; market still grows to $15B GWP.",
        "image_url": "https://images.unsplash.com/photo-1510511459019-5dda7724fd87?w=800",
        "author": "Digital Insurance Staff",
        "topics": ["cyber-insurance"],
        "regions": ["global"],
        "reader_profiles": ["investor", "founder"],
        "sentiment": "positive",
        "relevance_score": 0.87,
        "source_name": "Digital Insurance",
        "days_ago": 3,
    },
    {
        "title": "Root Insurance Partners with Uber to Offer Pay-Per-Mile Coverage for Rideshare Drivers",
        "url": "https://www.pymnts.com/root-insurance-uber-partnership",
        "content_raw": "Root Insurance has announced a strategic partnership with Uber to offer usage-based, pay-per-mile insurance coverage to rideshare drivers in 12 US states. The product uses telematics data from the Uber app to calculate premiums dynamically, with drivers paying only when they are actively accepting rides.",
        "summary_ai": "Root and Uber partner to launch per-mile rideshare driver insurance in 12 US states, dynamically priced using Uber telematics data.",
        "image_url": "https://images.unsplash.com/photo-1449965408869-eaa3f722e40d?w=800",
        "author": "PYMNTS",
        "topics": ["embedded-insurance", "auto-insurance", "partnerships"],
        "regions": ["US"],
        "reader_profiles": ["founder", "general"],
        "sentiment": "positive",
        "relevance_score": 0.85,
        "source_name": "PYMNTS",
        "days_ago": 4,
    },
    {
        "title": "Grab Financial Launches Micro-Health Insurance for Gig Workers Across Southeast Asia",
        "url": "https://fintechnews.sg/grab-micro-health-insurance-gig-workers",
        "content_raw": "Grab Financial Group has launched a micro-health insurance product specifically designed for gig economy workers in Singapore, Malaysia, and Indonesia. The product offers hospitalization coverage starting from $0.50 per day, activated via the Grab super-app, with instant eligibility and no health checks required.",
        "summary_ai": "Grab launches micro-health insurance for gig workers in SG, MY, and ID — coverage from $0.50/day, activated in-app with no health checks.",
        "image_url": "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=800",
        "author": "Fintech News Singapore",
        "topics": ["health-tech", "embedded-insurance", "product-launches"],
        "regions": ["APAC"],
        "reader_profiles": ["founder", "investor", "general"],
        "sentiment": "positive",
        "relevance_score": 0.9,
        "source_name": "Fintech News Singapore",
        "days_ago": 4,
    },
    {
        "title": "Swiss Re Institute: Climate Change to Drive $183 Billion Annual Increase in P&C Insurance Losses by 2035",
        "url": "https://www.swissre.com/institute/climate-pc-losses-2035",
        "content_raw": "Swiss Re Institute's latest sigma report forecasts that climate change will drive an additional $183 billion in annual property and casualty insurance losses by 2035, primarily from increased frequency and severity of extreme weather events. The report calls for accelerated adoption of parametric products and public-private risk partnerships.",
        "summary_ai": "Swiss Re projects +$183B/year in P&C climate losses by 2035, urging faster uptake of parametric insurance and public-private risk-sharing.",
        "image_url": "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=800",
        "author": "Swiss Re Institute",
        "topics": ["climate-parametric", "pc-innovation"],
        "regions": ["global"],
        "reader_profiles": ["investor", "general"],
        "sentiment": "negative",
        "relevance_score": 0.94,
        "source_name": "Swiss Re Institute",
        "days_ago": 5,
    },
    {
        "title": "Alan Health Achieves Profitability for First Time with 580,000 Members Across France, Spain and Belgium",
        "url": "https://techcrunch.com/alan-health-profitability-580k-members",
        "content_raw": "French health insurtech Alan has announced its first full quarter of profitability, with 580,000 members across France, Spain, and Belgium and revenues of €450 million annualized. The company's AI-powered care navigation platform reduced unnecessary specialist visits by 23% while improving member satisfaction scores.",
        "summary_ai": "Alan Health reaches profitability with 580K members and €450M ARR; AI care navigation cuts unnecessary specialist visits 23%.",
        "image_url": "https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=800",
        "author": "TC Staff",
        "topics": ["health-tech", "ai-insurance"],
        "regions": ["EU"],
        "reader_profiles": ["investor", "founder"],
        "sentiment": "positive",
        "relevance_score": 0.92,
        "source_name": "TechCrunch",
        "days_ago": 5,
    },
    {
        "title": "NAIC Approves Model Bulletin on AI Governance for Life Insurers",
        "url": "https://www.insurancejournal.com/naic-ai-governance-life-insurance",
        "content_raw": "The National Association of Insurance Commissioners (NAIC) has approved a model bulletin establishing AI governance requirements for life insurers, including mandatory algorithmic bias testing, model documentation standards, and consumer disclosure obligations. Seven states are expected to adopt the bulletin within 12 months.",
        "summary_ai": "NAIC approves AI governance model bulletin for life insurers covering bias testing, model docs, and consumer disclosures — 7 states expected to adopt.",
        "image_url": "https://images.unsplash.com/photo-1568992687947-868a62a9f521?w=800",
        "author": "Insurance Journal",
        "topics": ["regulatory-policy", "life-insurance", "ai-insurance"],
        "regions": ["US"],
        "reader_profiles": ["founder", "investor"],
        "sentiment": "neutral",
        "relevance_score": 0.86,
        "source_name": "Insurance Journal",
        "days_ago": 6,
    },
    {
        "title": "Tractable Raises $65M to Bring AI Vehicle Damage Assessment to Emerging Markets",
        "url": "https://www.insurtechmagazine.com/tractable-65m-emerging-markets",
        "content_raw": "Tractable, the AI computer vision company specializing in accident and disaster recovery, has raised $65 million in a growth equity round to expand its vehicle damage assessment technology to markets in Southeast Asia, Latin America, and Sub-Saharan Africa. The company's AI can assess vehicle damage from photos within seconds.",
        "summary_ai": "Tractable raises $65M to expand AI photo-based vehicle damage assessment to SE Asia, LATAM, and Sub-Saharan Africa.",
        "image_url": "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?w=800",
        "author": "Editorial",
        "topics": ["auto-insurance", "claims-tech", "ai-insurance", "funding-ma"],
        "regions": ["global", "APAC", "LATAM", "MEA"],
        "reader_profiles": ["investor", "founder"],
        "sentiment": "positive",
        "relevance_score": 0.91,
        "source_name": "InsurTech Magazine",
        "days_ago": 6,
    },
    {
        "title": "Munich Re and Google Cloud Partner to Create Industry-First Reinsurance Pricing AI",
        "url": "https://www.theinsurer.com/munich-re-google-cloud-reinsurance-ai",
        "content_raw": "Munich Re and Google Cloud have announced a multi-year strategic partnership to develop an AI-powered reinsurance pricing model that incorporates real-time climate data, satellite imagery, and natural language processing of legal contracts. The system is expected to reduce pricing cycle times from weeks to hours.",
        "summary_ai": "Munich Re and Google Cloud build AI reinsurance pricing using real-time climate data and satellite imagery — cutting pricing cycles from weeks to hours.",
        "image_url": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=800",
        "author": "The Insurer Staff",
        "topics": ["ai-insurance", "underwriting-tech", "partnerships"],
        "regions": ["EU", "global"],
        "reader_profiles": ["investor"],
        "sentiment": "positive",
        "relevance_score": 0.93,
        "source_name": "The Insurer",
        "days_ago": 7,
    },
    {
        "title": "Nubank Launches Embedded Life Insurance for 90 Million Brazilian Customers",
        "url": "https://www.fintechfutures.com/nubank-life-insurance-brazil",
        "content_raw": "Brazilian neobank Nubank has launched a life insurance product embedded directly in its app for its 90 million customers, offering coverage from BRL 50,000 to BRL 1 million with instant issuance and premium starting at BRL 9.90/month. The product is underwritten by Chubb and distributed without any human agents.",
        "summary_ai": "Nubank embeds Chubb-underwritten life insurance for 90M Brazilian customers — instant issuance, BRL 9.90/month starting premium, zero agents.",
        "image_url": "https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=800",
        "author": "Fintech Futures",
        "topics": ["life-insurance", "embedded-insurance", "product-launches"],
        "regions": ["LATAM"],
        "reader_profiles": ["investor", "founder", "general"],
        "sentiment": "positive",
        "relevance_score": 0.9,
        "source_name": "Fintech Futures",
        "days_ago": 7,
    },
    {
        "title": "Oscar Health Introduces GenAI Prior Authorization Tool Cutting Approval Times by 70%",
        "url": "https://www.dig-in.com/oscar-health-genai-prior-authorization",
        "content_raw": "Oscar Health has deployed a generative AI tool for prior authorization processing that has reduced average approval times from 3.2 days to under 22 hours, a 70% reduction. The system analyzes clinical guidelines, member history, and provider notes simultaneously, flagging edge cases for human review.",
        "summary_ai": "Oscar Health's GenAI prior auth tool cuts approval times 70% (3.2 days → 22 hrs) by simultaneously analyzing clinical guidelines, history, and notes.",
        "image_url": "https://images.unsplash.com/photo-1576091160550-2173dba999ef?w=800",
        "author": "Digital Insurance",
        "topics": ["health-tech", "ai-insurance", "claims-tech"],
        "regions": ["US"],
        "reader_profiles": ["founder", "investor"],
        "sentiment": "positive",
        "relevance_score": 0.88,
        "source_name": "Digital Insurance",
        "days_ago": 8,
    },
]


async def seed_articles():
    async with AsyncSessionLocal() as db:
        # Get sources mapping
        result = await db.execute(select(Source))
        sources = {s.name: s.id for s in result.scalars().all()}

        existing = await db.execute(select(Article.url))
        existing_urls = {r[0] for r in existing.fetchall()}

        added = 0
        for data in SAMPLE_ARTICLES:
            if data["url"] in existing_urls:
                continue

            source_name = data.pop("source_name")
            days_ago = data.pop("days_ago")
            source_id = sources.get(source_name, 1)

            slug = slugify(data["title"])[:550]

            article = Article(
                title=data["title"],
                slug=slug,
                url=data["url"],
                source_id=source_id,
                content_raw=data.get("content_raw"),
                summary_ai=data.get("summary_ai"),
                image_url=data.get("image_url"),
                author=data.get("author"),
                published_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
                embedding=None,
                is_duplicate=False,
                is_processed=True,
                topics=data.get("topics", []),
                regions=data.get("regions", []),
                reader_profiles=data.get("reader_profiles", []),
                sentiment=data.get("sentiment"),
                relevance_score=data.get("relevance_score", 0.8),
            )
            db.add(article)
            added += 1

        await db.commit()
        print(f"✓ Seeded {added} sample articles")


if __name__ == "__main__":
    asyncio.run(seed_articles())
