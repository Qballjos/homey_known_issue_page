from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime


class ProductOut(BaseModel):
    id: str
    name: str
    slug: str

    model_config = ConfigDict(from_attributes=True)


class VersionOut(BaseModel):
    id: str
    version_string: str

    model_config = ConfigDict(from_attributes=True)


class TimelineUpdateOut(BaseModel):
    id: str
    title: str
    description: str
    status_at_update: Optional[str] = None
    update_date: datetime
    notified_subscribers: bool

    model_config = ConfigDict(from_attributes=True)


class IssueCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    summary: str = Field(..., min_length=5)
    description: str = Field(..., min_length=10)
    status: str = Field(default="Investigating")
    severity: str = Field(default="Medium")
    visibility: str = Field(default="Public")
    workaround: Optional[str] = None
    expected_fix: Optional[str] = None
    fixed_version: Optional[str] = None
    min_subscribers_threshold: int = 0
    auto_publish_on_threshold: bool = False
    product_names: List[str] = []
    version_strings: List[str] = []


class IssueUpdateSchema(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    severity: Optional[str] = None
    visibility: Optional[str] = None
    workaround: Optional[str] = None
    expected_fix: Optional[str] = None
    fixed_version: Optional[str] = None
    min_subscribers_threshold: Optional[int] = None
    auto_publish_on_threshold: Optional[bool] = None
    product_names: Optional[List[str]] = None
    version_strings: Optional[List[str]] = None


class TimelineUpdateCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    description: str = Field(..., min_length=5)
    notify_subscribers: bool = True
    status_update: Optional[str] = None


class IssueSummaryOut(BaseModel):
    id: str
    slug: str
    title: str
    summary: str
    status: str
    severity: str
    visibility: str
    first_reported_at: datetime
    confirmed_at: datetime
    last_updated_at: datetime
    resolved_at: Optional[datetime] = None
    fixed_version: Optional[str] = None
    products: List[ProductOut] = []
    versions: List[VersionOut] = []
    subscribers_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class IssueDetailOut(IssueSummaryOut):
    description: str
    workaround: Optional[str] = None
    expected_fix: Optional[str] = None
    updates: List[TimelineUpdateOut] = []

    model_config = ConfigDict(from_attributes=True)
