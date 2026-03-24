"""Resend email sender for newsletters."""
import logging
import resend
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.subscription import Subscription
from app.models.newsletter import Newsletter, NewsletterLog
from app.services.ai.newsletter_writer import generate_newsletter

logger = logging.getLogger(__name__)
settings = get_settings()


async def send_newsletter_batch(profile: str, frequency: str):
    """Generate and send newsletter to all matching subscribers."""
    resend.api_key = settings.resend_api_key

    async with AsyncSessionLocal() as db:
        # Generate newsletter content
        result = await db.execute(
            select(Newsletter)
            .where(Newsletter.reader_profile == profile, Newsletter.edition_type == frequency)
            .order_by(Newsletter.edition_number.desc())
            .limit(1)
        )
        last = result.scalar_one_or_none()
        edition_number = (last.edition_number + 1) if last else 1

        newsletter_data = await generate_newsletter(db, profile, frequency, edition_number)
        if not newsletter_data:
            logger.warning(f"No content generated for {profile}/{frequency}")
            return

        newsletter = Newsletter(
            subject=newsletter_data["subject"],
            html_content=newsletter_data["html_content"],
            reader_profile=profile,
            edition_type=frequency,
            edition_number=edition_number,
        )
        db.add(newsletter)
        await db.flush()

        # Fetch active subscribers for this profile
        subs_result = await db.execute(
            select(Subscription, User)
            .join(User, User.id == Subscription.user_id)
            .where(
                Subscription.is_active == True,  # noqa: E712
                Subscription.frequency == frequency,
                Subscription.reader_profiles.contains([profile]),
                User.is_active == True,  # noqa: E712
            )
        )
        rows = subs_result.all()

        sent = 0
        for sub, user in rows:
            html = newsletter_data["html_content"].replace(
                "{{unsubscribe_url}}",
                f"{settings.app_url}/unsubscribe/{sub.unsubscribe_token}",
            )
            try:
                resp = resend.Emails.send({
                    "from": f"{settings.resend_from_name} <{settings.resend_from_email}>",
                    "to": [user.email],
                    "subject": newsletter_data["subject"],
                    "html": html,
                })
                log = NewsletterLog(
                    newsletter_id=newsletter.id,
                    user_id=user.id,
                    resend_id=resp.get("id"),
                )
                db.add(log)
                sent += 1
            except Exception as e:
                logger.error(f"Failed to send to {user.email}: {e}")

        from datetime import datetime, timezone
        newsletter.sent_at = datetime.now(timezone.utc)
        await db.commit()

    logger.info(f"Newsletter {profile}/{frequency} #{edition_number} sent to {sent} subscribers")


async def send_verification_email(email: str, token: str):
    """Send email verification."""
    resend.api_key = settings.resend_api_key
    verify_url = f"{settings.app_url}/verify-email?token={token}"
    try:
        resend.Emails.send({
            "from": f"{settings.resend_from_name} <{settings.resend_from_email}>",
            "to": [email],
            "subject": "Confirm your InsurTech Intelligence subscription",
            "html": f"""
            <p>Welcome to <strong>InsurTech Intelligence</strong>!</p>
            <p>Click the link below to confirm your subscription:</p>
            <p><a href="{verify_url}">Confirm subscription →</a></p>
            <p style="color:#999;font-size:12px;">If you didn't sign up, ignore this email.</p>
            """,
        })
    except Exception as e:
        logger.error(f"Failed to send verification to {email}: {e}")
