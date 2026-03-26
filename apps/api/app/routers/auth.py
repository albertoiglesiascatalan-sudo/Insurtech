import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.subscription import Subscription
from app.schemas.user import UserCreate, UserLogin, UserOut, Token
from app.auth import hash_password, verify_password, create_access_token, require_user

router = APIRouter(prefix="/auth", tags=["auth"])


class GoogleAuthIn(BaseModel):
    email: str
    name: str | None = None
    google_id: str
    image: str | None = None


@router.post("/register", response_model=Token, status_code=201)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=data.email,
        name=data.name,
        hashed_password=hash_password(data.password),
        reader_profile=data.reader_profile,
        verification_token=secrets.token_urlsafe(32),
    )
    db.add(user)
    await db.flush()

    # Create default subscription
    sub = Subscription(
        user_id=user.id,
        reader_profiles=[data.reader_profile],
        unsubscribe_token=secrets.token_urlsafe(32),
    )
    db.add(sub)
    await db.commit()
    await db.refresh(user)

    token = create_access_token({"sub": user.id})
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=Token)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user or not user.hashed_password or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": user.id})
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.post("/google", response_model=Token)
async def google_auth(data: GoogleAuthIn, db: AsyncSession = Depends(get_db)):
    """Create or login a user authenticated via Google OAuth."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user:
        # First Google login — create user (verified, no password)
        user = User(
            email=data.email,
            name=data.name,
            is_verified=True,
            reader_profile="general",
        )
        db.add(user)
        await db.flush()
        sub = Subscription(
            user_id=user.id,
            reader_profiles=["general"],
            unsubscribe_token=secrets.token_urlsafe(32),
        )
        db.add(sub)
        await db.commit()
        await db.refresh(user)
    else:
        # Update name/image if changed
        if data.name and not user.name:
            user.name = data.name
        if not user.is_verified:
            user.is_verified = True
        await db.commit()
        await db.refresh(user)

    token = create_access_token({"sub": user.id})
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(require_user)):
    return UserOut.model_validate(user)
