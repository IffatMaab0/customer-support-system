from uuid import UUID
from datetime import datetime
import uuid

from pydantic import BaseModel, EmailStr



class TicketCreate(BaseModel):
    subject: str
    message: str


class TicketListOut(BaseModel):
    id: uuid.UUID
    subject: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True



class CustomerOut(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr

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




class ClaimTicket(BaseModel):
    agent_id: uuid.UUID


class AgentOut(BaseModel):
    id: uuid.UUID
    name: str
    email: str

    class Config:
        from_attributes = True




class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    name: str
    email: EmailStr


class MeResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    role: str



class AdminTicketOut(BaseModel):
    id: UUID
    subject: str
    message: str
    status: str
    response: str | None
    created_at: datetime
    customer_name: str
    customer_email: str
    agent_name: str | None

    class Config:
        from_attributes = True        



