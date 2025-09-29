from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime

class TimeInfo(BaseModel):
    datetime: str
    timezone: str

class LocationInfo(BaseModel):
    name: str
    address: Optional[str] = ""

class DetailsInfo(BaseModel):
    seat: Optional[str] = None
    gate: Optional[str] = None
    reference: Optional[str] = None

class TicketData(BaseModel):
    id: str
    type: Literal["flight", "train", "concert", "theater", "generic"]
    title: str
    start: TimeInfo
    end: Optional[TimeInfo] = None
    location: LocationInfo
    details: DetailsInfo
    confidence: float