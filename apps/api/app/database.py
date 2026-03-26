from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings


class Base(DeclarativeBase):
    pass


_engine = None
_session_factory = None


def _get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.environment == "development",
            pool_size=10,
            max_overflow=20,
        )
    return _engine


def _get_session_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            _get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


class _LazySessionLocal:
    """Callable proxy so `AsyncSessionLocal()` still works across the codebase."""
    def __call__(self, *args, **kwargs):
        return _get_session_factory()(*args, **kwargs)


AsyncSessionLocal = _LazySessionLocal()


async def get_db():
    async with _get_session_factory()() as session:
        try:
            yield session
        finally:
            await session.close()
