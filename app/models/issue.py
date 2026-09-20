import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.product import issue_products, issue_versions


def generate_uuid():
    return str(uuid.uuid4())


def now_utc():
    return datetime.now(timezone.utc)


class Issue(Base):
    __tablename__ = "issues"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    slug = Column(String(200), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    
    # Statuses: Investigating, Identified, Fix in development, Monitoring, Resolved, Closed
    status = Column(String(50), default="Investigating", nullable=False, index=True)
    
    # Severities: Low, Medium, High, Critical
    severity = Column(String(50), default="Medium", nullable=False, index=True)
    
    # Visibility: Draft, Internal, Public, Resolved, Closed
    visibility = Column(String(50), default="Public", nullable=False, index=True)

    workaround = Column(Text, nullable=True)
    expected_fix = Column(Text, nullable=True)
    fixed_version = Column(String(100), nullable=True)

    first_reported_at = Column(DateTime, default=now_utc, nullable=False)
    confirmed_at = Column(DateTime, default=now_utc, nullable=False)
    last_updated_at = Column(DateTime, default=now_utc, onupdate=now_utc, nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    # Publishing threshold logic
    min_subscribers_threshold = Column(Integer, default=0, nullable=False)
    auto_publish_on_threshold = Column(Boolean, default=False, nullable=False)

    # Relationships
    products = relationship("Product", secondary=issue_products, back_populates="issues")
    versions = relationship("ProductVersion", secondary=issue_versions, back_populates="issues")
    updates = relationship(
        "IssueUpdate",
        back_populates="issue",
        cascade="all, delete-orphan",
        order_by="desc(IssueUpdate.update_date)"
    )
    subscriptions = relationship(
        "Subscription",
        back_populates="issue",
        cascade="all, delete-orphan"
    )

    @property
    def confirmed_subscribers_count(self) -> int:
        return sum(1 for s in self.subscriptions if s.status == "confirmed")
