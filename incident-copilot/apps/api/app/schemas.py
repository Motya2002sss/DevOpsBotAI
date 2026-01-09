from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class IncidentCreate(BaseModel):
    title: str = Field(..., max_length=300)
    severity: str = Field(default="info")  # info|warn|crit
    service: str | None = None
    environment: str | None = None


class IncidentOut(BaseModel):
    id: UUID
    title: str
    severity: str
    status: str
    service: str | None
    environment: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SignalOut(BaseModel):
    id: UUID
    incident_id: UUID
    type: str
    source: str
    timestamp: datetime
    payload: dict

    class Config:
        from_attributes = True

