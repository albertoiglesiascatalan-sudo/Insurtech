import secrets
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.subscription import Subscription
from app.schemas.subscription import SubscriptionCreate, SubscriptionUpdate, SubscriptionOut
from app.auth import hash_password, create_access_token
from app.schemas.user import Token, UserOut

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.post("", response_model=dict, status_code=201)
async def subscribe(data: SubscriptionCreate, db: AsyncSession = Depends(get_db)):
    """Public subscription endpoint — creates user + subscription if not exists."""
    existing = await db.execute(select(User).where(User.email == data.email))
    user = existing.scalar_one_or_none()

    if not user:
        user = User(
            email=data.email,
            name=data.name,
            reader_profile=data.reader_profile,
            verification_token=secrets.token_urlsafe(32),
        )
        db.add(user)
        await db.flush()

        sub = Subscription(
            user_id=user.id,
            topics=data.topics,
            regions=data.regions,
            reader_profiles=[data.reader_profile],
            frequency=data.frequency,
            unsubscribe_token=secrets.token_urlsafe(32),
        )
        db.add(sub)
        await db.commit()
        return {"message": "Subscribed successfully. Check your email for confirmation."}

    # User exists — update subscription
    sub_result = await db.execute(select(Subscription).where(Subscription.user_id == user.id))
    sub = sub_result.scalar_one_or_none()
    if sub:
        sub.is_active = True
    else:
        sub = Subscription(
            user_id=user.id,
            topics=data.topics,
            regions=data.regions,
            reader_profiles=[data.reader_profile],
            frequency=data.frequency,
            unsubscribe_token=secrets.token_urlsafe(32),
        )
        db.add(sub)
    await db.commit()
    return {"message": "Subscription updated."}


@router.get("/unsubscribe/{token}", response_model=dict)
async def unsubscribe(token: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Subscription).where(Subscription.unsubscribe_token == token))
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Invalid token")
    sub.is_active = False
    await db.commit()
    return {"message": "Unsubscribed successfully."}


@router.patch("/me", response_model=SubscriptionOut)
async def update_my_subscription(
    data: SubscriptionUpdate,
    db: AsyncSession = Depends(get_db),
    # user: User = Depends(require_user),  # Enable when auth is wired
):
    raise HTTPException(status_code=501, detail="Auth required")
