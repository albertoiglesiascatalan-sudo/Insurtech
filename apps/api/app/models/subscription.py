from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    topics: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    regions: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    reader_profiles: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    frequency: Mapped[str] = mapped_column(String(20), default="weekly")  # daily | weekly
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    unsubscribe_token: Mapped[str | None] = mapped_column(String(200))
    subscribed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    last_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship("User", back_populates="subscription")  # noqa: F821
