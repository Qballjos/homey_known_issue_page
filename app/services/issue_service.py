import re
import json
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.issue import Issue
from app.models.timeline import IssueUpdate
from app.models.product import Product, ProductVersion
from app.models.subscription import Subscription
from app.models.audit import AuditLog
from app.models.user import User
from app.schemas.issue import IssueCreate, IssueUpdateSchema
from app.config import settings
from app.email.service import send_email
from app.email.templates import get_issue_update_email


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text or "issue"


def generate_unique_slug(db: Session, title: str, exclude_id: Optional[str] = None) -> str:
    base_slug = slugify(title)
    slug = base_slug
    counter = 1
    while True:
        query = db.query(Issue).filter(Issue.slug == slug)
        if exclude_id:
            query = query.filter(Issue.id != exclude_id)
        if not query.first():
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1


def record_audit(
    db: Session,
    action: str,
    entity_id: str,
    user: Optional[User] = None,
    details: Optional[dict] = None
):
    audit = AuditLog(
        user_id=user.id if user else None,
        user_email=user.email if user else "system",
        action=action,
        entity_type="issue",
        entity_id=entity_id,
        details=json.dumps(details or {}, default=str),
    )
    db.add(audit)


def get_or_create_product(db: Session, name: str) -> Product:
    clean_name = name.strip()
    prod = db.query(Product).filter(func.lower(Product.name) == clean_name.lower()).first()
    if not prod:
        prod = Product(name=clean_name, slug=slugify(clean_name))
        db.add(prod)
        db.flush()
    return prod


def get_or_create_version(db: Session, product: Product, version_str: str) -> ProductVersion:
    clean_ver = version_str.strip()
    ver = (
        db.query(ProductVersion)
        .filter(
            ProductVersion.product_id == product.id,
            func.lower(ProductVersion.version_string) == clean_ver.lower()
        )
        .first()
    )
    if not ver:
        ver = ProductVersion(product_id=product.id, version_string=clean_ver)
        db.add(ver)
        db.flush()
    return ver


def create_issue(db: Session, data: IssueCreate, user: Optional[User] = None) -> Issue:
    slug = generate_unique_slug(db, data.title)
    now = datetime.now(timezone.utc)

    issue = Issue(
        title=data.title.strip(),
        slug=slug,
        summary=data.summary.strip(),
        description=data.description.strip(),
        status=data.status,
        severity=data.severity,
        visibility=data.visibility,
        workaround=data.workaround.strip() if data.workaround else None,
        expected_fix=data.expected_fix.strip() if data.expected_fix else None,
        fixed_version=data.fixed_version.strip() if data.fixed_version else None,
        min_subscribers_threshold=data.min_subscribers_threshold,
        auto_publish_on_threshold=data.auto_publish_on_threshold,
        first_reported_at=now,
        confirmed_at=now,
        last_updated_at=now,
    )

    if data.status.lower() == "resolved":
        issue.resolved_at = now

    db.add(issue)
    db.flush()

    # Associate products and versions
    for p_name in data.product_names:
        if p_name.strip():
            prod = get_or_create_product(db, p_name)
            issue.products.append(prod)

    for v_str in data.version_strings:
        if v_str.strip() and issue.products:
            ver = get_or_create_version(db, issue.products[0], v_str)
            issue.versions.append(ver)

    # Initial timeline update
    initial_update = IssueUpdate(
        issue_id=issue.id,
        title="Issue Confirmed",
        description="The issue has been confirmed by our technical team.",
        status_at_update=issue.status,
        update_date=now,
        notified_subscribers=False,
    )
    db.add(initial_update)

    record_audit(
        db,
        action="ISSUE_CREATED",
        entity_id=issue.id,
        user=user,
        details={"title": issue.title, "status": issue.status, "visibility": issue.visibility}
    )

    db.commit()
    db.refresh(issue)
    return issue


def update_issue(
    db: Session,
    issue: Issue,
    data: IssueUpdateSchema,
    user: Optional[User] = None
) -> Issue:
    now = datetime.now(timezone.utc)
    old_status = issue.status
    old_visibility = issue.visibility

    if data.title is not None and data.title.strip() != issue.title:
        issue.title = data.title.strip()
        issue.slug = generate_unique_slug(db, issue.title, exclude_id=issue.id)

    if data.summary is not None:
        issue.summary = data.summary.strip()
    if data.description is not None:
        issue.description = data.description.strip()
    if data.status is not None:
        issue.status = data.status
        if issue.status.lower() == "resolved" and not issue.resolved_at:
            issue.resolved_at = now
    if data.severity is not None:
        issue.severity = data.severity
    if data.visibility is not None:
        issue.visibility = data.visibility
    if data.workaround is not None:
        issue.workaround = data.workaround.strip() if data.workaround else None
    if data.expected_fix is not None:
        issue.expected_fix = data.expected_fix.strip() if data.expected_fix else None
    if data.fixed_version is not None:
        issue.fixed_version = data.fixed_version.strip() if data.fixed_version else None
    if data.min_subscribers_threshold is not None:
        issue.min_subscribers_threshold = data.min_subscribers_threshold
    if data.auto_publish_on_threshold is not None:
        issue.auto_publish_on_threshold = data.auto_publish_on_threshold

    if data.product_names is not None:
        issue.products.clear()
        for p_name in data.product_names:
            if p_name.strip():
                issue.products.append(get_or_create_product(db, p_name))

    if data.version_strings is not None:
        issue.versions.clear()
        for v_str in data.version_strings:
            if v_str.strip() and issue.products:
                issue.versions.append(get_or_create_version(db, issue.products[0], v_str))

    issue.last_updated_at = now

    audit_details = {}
    if old_status != issue.status:
        audit_details["status_change"] = f"{old_status} -> {issue.status}"
    if old_visibility != issue.visibility:
        audit_details["visibility_change"] = f"{old_visibility} -> {issue.visibility}"

    record_audit(
        db,
        action="ISSUE_UPDATED",
        entity_id=issue.id,
        user=user,
        details=audit_details or {"updated_fields": list(data.model_dump(exclude_unset=True).keys())}
    )

    db.commit()
    db.refresh(issue)
    return issue


def add_timeline_update(
    db: Session,
    issue: Issue,
    title: str,
    description: str,
    notify_subscribers: bool = True,
    new_status: Optional[str] = None,
    user: Optional[User] = None
) -> Tuple[IssueUpdate, int]:
    now = datetime.now(timezone.utc)
    
    if new_status and new_status != issue.status:
        old_status = issue.status
        issue.status = new_status
        if issue.status.lower() == "resolved" and not issue.resolved_at:
            issue.resolved_at = now
        record_audit(
            db,
            action="STATUS_CHANGED",
            entity_id=issue.id,
            user=user,
            details={"from": old_status, "to": new_status}
        )

    issue.last_updated_at = now

    update = IssueUpdate(
        issue_id=issue.id,
        title=title.strip(),
        description=description.strip(),
        status_at_update=issue.status,
        update_date=now,
        notified_subscribers=notify_subscribers,
    )
    db.add(update)
    db.flush()

    record_audit(
        db,
        action="UPDATE_ADDED",
        entity_id=issue.id,
        user=user,
        details={"update_title": title, "notify_subscribers": notify_subscribers}
    )

    db.commit()
    db.refresh(issue)

    notified_count = 0
    if notify_subscribers:
        notified_count = dispatch_update_notification(db, issue, update)

    return update, notified_count


def dispatch_update_notification(db: Session, issue: Issue, update: IssueUpdate) -> int:
    subscribers = (
        db.query(Subscription)
        .filter(Subscription.issue_id == issue.id, Subscription.status == "confirmed")
        .all()
    )

    issue_url = f"{settings.APP_URL}/issues/{issue.slug}"

    sent_count = 0
    for sub in subscribers:
        unsub_url = f"{settings.APP_URL}/unsubscribe/{sub.unsubscribe_token}"
        subject, text_body, html_body = get_issue_update_email(
            issue_title=issue.title,
            issue_status=issue.status,
            update_title=update.title,
            update_description=update.description,
            issue_url=issue_url,
            unsubscribe_url=unsub_url,
        )
        if send_email(sub.email, subject, text_body, html_body):
            sent_count += 1

    return sent_count


def check_and_apply_threshold_publishing(db: Session, issue: Issue) -> bool:
    if issue.visibility in ("Draft", "Internal") and issue.auto_publish_on_threshold:
        confirmed_count = (
            db.query(Subscription)
            .filter(Subscription.issue_id == issue.id, Subscription.status == "confirmed")
            .count()
        )
        if confirmed_count >= issue.min_subscribers_threshold:
            issue.visibility = "Public"
            issue.last_updated_at = datetime.now(timezone.utc)
            record_audit(
                db,
                action="AUTO_PUBLISHED_THRESHOLD",
                entity_id=issue.id,
                details={"threshold": issue.min_subscribers_threshold, "subscribers": confirmed_count}
            )
            db.commit()
            return True
    return False
