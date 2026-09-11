import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TicketCreate(BaseModel):
    subject: str
    message: str
    customer_name: str
    customer_email: str


class TicketOut(BaseModel):
    id: uuid.UUID
    subject: str
    message: str
    status: str
    response: Optional[str] = None
    responded_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StatusUpdate(BaseModel):
    status: str


class ResponseUpdate(BaseModel):
    response: str


class DocOut(BaseModel):
    id: uuid.UUID
    title: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True