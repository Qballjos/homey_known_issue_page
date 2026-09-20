import re
from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional


EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class SubscribeRequest(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        clean = v.strip().lower()
        if not EMAIL_REGEX.match(clean):
            raise ValueError("Invalid email format")
        return clean


class SubscribeResponse(BaseModel):
    message: str
    status: str
    email: str


class ConfirmRequest(BaseModel):
    token: str


class UnsubscribeRequest(BaseModel):
    token: str


class SubscriptionStats(BaseModel):
    total: int
    confirmed: int
    pending: int
    unsubscribed: int


class AdminStatsResponse(BaseModel):
    total_issues: int
    active_issues: int
    investigating: int
    identified: int
    fix_in_development: int
    monitoring: int
    resolved: int
    closed: int
    subscribers: SubscriptionStats
