from pydantic import BaseModel
from typing import Optional
from .ticket import TicketData

class UploadResponse(BaseModel):
    id: str
    status: str

class ResultResponse(BaseModel):
    id: str
    status: str
    data: Optional[TicketData] = None
    ics_url: Optional[str] = None
    error: Optional[str] = None

class ProcessResponse(BaseModel):
    id: str
    status: str
    data: Optional[TicketData] = None
    ics_url: Optional[str] = None
    error: Optional[str] = None
