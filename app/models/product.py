import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.database import Base


def generate_uuid():
    return str(uuid.uuid4())


def now_utc():
    return datetime.now(timezone.utc)


issue_products = Table(
    "issue_products",
    Base.metadata,
    Column("issue_id", String(36), ForeignKey("issues.id", ondelete="CASCADE"), primary_key=True),
    Column("product_id", String(36), ForeignKey("products.id", ondelete="CASCADE"), primary_key=True),
)

issue_versions = Table(
    "issue_versions",
    Base.metadata,
    Column("issue_id", String(36), ForeignKey("issues.id", ondelete="CASCADE"), primary_key=True),
    Column("version_id", String(36), ForeignKey("product_versions.id", ondelete="CASCADE"), primary_key=True),
)


class Product(Base):
    __tablename__ = "products"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=now_utc, nullable=False)

    versions = relationship("ProductVersion", back_populates="product", cascade="all, delete-orphan")
    issues = relationship("Issue", secondary=issue_products, back_populates="products")


class ProductVersion(Base):
    __tablename__ = "product_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    version_string = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=now_utc, nullable=False)

    product = relationship("Product", back_populates="versions")
    issues = relationship("Issue", secondary=issue_versions, back_populates="versions")
