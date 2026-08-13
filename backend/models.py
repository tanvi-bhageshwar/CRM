from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field

StatusType = Literal["Open", "In Progress", "Closed"]
PriorityType = Literal["Low", "Medium", "High"]


class TicketCreate(BaseModel):
    customer_name: str = Field(min_length=1, max_length=200)
    customer_email: EmailStr
    subject: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=5000)
    priority: PriorityType = "Medium"


class TicketCreateResponse(BaseModel):
    ticket_id: str
    created_at: str


class TicketSummary(BaseModel):
    ticket_id: str
    customer_name: str
    subject: str
    status: StatusType
    priority: PriorityType
    created_at: str


class Note(BaseModel):
    note_text: str
    created_at: str


class TicketDetail(BaseModel):
    ticket_id: str
    customer_name: str
    customer_email: str
    subject: str
    description: str
    status: StatusType
    priority: PriorityType
    created_at: str
    updated_at: str
    notes: list[Note]


class TicketUpdate(BaseModel):
    status: Optional[StatusType] = None
    priority: Optional[PriorityType] = None
    notes: Optional[str] = None  # a new note to append, not a replacement


class TicketUpdateResponse(BaseModel):
    success: bool
    updated_at: str