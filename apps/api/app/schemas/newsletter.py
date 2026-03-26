from datetime import datetime
from pydantic import BaseModel


class NewsletterOut(BaseModel):
    id: int
    subject: str
    reader_profile: str
    edition_type: str
    edition_number: int
    sent_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
