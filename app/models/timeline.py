import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


def generate_uuid():
    return str(uuid.uuid4())


def now_utc():
    return datetime.now(timezone.utc)


class IssueUpdate(Base):
    __tablename__ = "issue_updates"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    issue_id = Column(String(36), ForeignKey("issues.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status_at_update = Column(String(50), nullable=True)
    update_date = Column(DateTime, default=now_utc, nullable=False)
    created_at = Column(DateTime, default=now_utc, nullable=False)
    notified_subscribers = Column(Boolean, default=False, nullable=False)

    issue = relationship("Issue", back_populates="updates")
