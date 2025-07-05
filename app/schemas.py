from pydantic import BaseModel, ConfigDict
from datetime import date, datetime


class CampaignBase(BaseModel):
    session_name: str
    description: str | None = None
    map_name: str
    start_date: date
    start_time: datetime


class CampaignCreate(CampaignBase):
    pass


class Campaign(CampaignBase):
    session_id: int

    model_config = ConfigDict(from_attributes=True)
