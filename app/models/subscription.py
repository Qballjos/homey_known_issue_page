import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


def generate_uuid():
    return str(uuid.uuid4())


def now_utc():
    return datetime.now(timezone.utc)


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        UniqueConstraint("issue_id", "email", name="uq_issue_email"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    issue_id = Column(String(36), ForeignKey("issues.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    
    # Status: pending, confirmed, unsubscribed
    status = Column(String(50), default="pending", nullable=False, index=True)
    confirmation_token = Column(String(128), unique=True, index=True, nullable=False)
    unsubscribe_token = Column(String(128), unique=True, index=True, nullable=False)

    created_at = Column(DateTime, default=now_utc, nullable=False)
    confirmed_at = Column(DateTime, nullable=True)
    unsubscribed_at = Column(DateTime, nullable=True)

    issue = relationship("Issue", back_populates="subscriptions")
