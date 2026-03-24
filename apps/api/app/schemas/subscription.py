from datetime import datetime
from pydantic import BaseModel


class SubscriptionCreate(BaseModel):
    email: str
    name: str | None = None
    reader_profile: str = "general"
    topics: list[str] = []
    regions: list[str] = []
    frequency: str = "weekly"


class SubscriptionUpdate(BaseModel):
    topics: list[str] | None = None
    regions: list[str] | None = None
    reader_profiles: list[str] | None = None
    frequency: str | None = None
    is_active: bool | None = None


class SubscriptionOut(BaseModel):
    id: int
    topics: list[str]
    regions: list[str]
    reader_profiles: list[str]
    frequency: str
    is_active: bool
    subscribed_at: datetime
    last_sent_at: datetime | None = None

    model_config = {"from_attributes": True}
