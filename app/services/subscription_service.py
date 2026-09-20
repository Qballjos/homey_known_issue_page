from datetime import datetime, timezone
from typing import Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.subscription import Subscription
from app.models.issue import Issue
from app.auth.security import generate_secure_token
from app.email.service import send_email
from app.email.templates import get_confirmation_email
from app.config import settings
from app.services.issue_service import check_and_apply_threshold_publishing


def subscribe_to_issue(
    db: Session,
    issue: Issue,
    email: str
) -> Tuple[Subscription, str]:
    """
    Handle double opt-in subscription request.
    Returns (subscription, status_code_message).
    """
    clean_email = email.strip().lower()

    sub = (
        db.query(Subscription)
        .filter(Subscription.issue_id == issue.id, Subscription.email == clean_email)
        .first()
    )

    now = datetime.now(timezone.utc)

    if sub:
        if sub.status == "confirmed":
            return sub, "already_confirmed"
        # If pending or previously unsubscribed, refresh confirmation token and re-send
        sub.status = "pending"
        sub.confirmation_token = generate_secure_token(32)
        sub.created_at = now
    else:
        sub = Subscription(
            issue_id=issue.id,
            email=clean_email,
            status="pending",
            confirmation_token=generate_secure_token(32),
            unsubscribe_token=generate_secure_token(32),
            created_at=now,
        )
        db.add(sub)

    db.commit()
    db.refresh(sub)

    # Dispatch confirmation email
    confirm_url = f"{settings.APP_URL}/subscribe/confirm?token={sub.confirmation_token}"
    subject, text_body, html_body = get_confirmation_email(issue.title, confirm_url)
    send_email(sub.email, subject, text_body, html_body)

    return sub, "confirmation_sent"


def confirm_subscription(db: Session, token: str) -> Tuple[bool, Optional[Subscription], str]:
    """Verify confirmation token and activate subscription."""
    if not token or not token.strip():
        return False, None, "Invalid token"

    sub = db.query(Subscription).filter(Subscription.confirmation_token == token.strip()).first()
    if not sub:
        return False, None, "Subscription not found or token expired"

    if sub.status == "confirmed":
        return True, sub, "Already confirmed"

    sub.status = "confirmed"
    sub.confirmed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(sub)

    # Check if this confirmation causes the issue to cross its auto-publishing threshold
    check_and_apply_threshold_publishing(db, sub.issue)

    return True, sub, "Subscription successfully confirmed"


def unsubscribe(db: Session, token: str) -> Tuple[bool, Optional[Subscription], str]:
    """Unsubscribe using the secure unsubscribe token."""
    if not token or not token.strip():
        return False, None, "Invalid token"

    sub = db.query(Subscription).filter(Subscription.unsubscribe_token == token.strip()).first()
    if not sub:
        return False, None, "Subscription not found"

    sub.status = "unsubscribed"
    sub.unsubscribed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(sub)

    return True, sub, "You have been successfully unsubscribed."


def get_issue_subscriber_counts(db: Session, issue_id: str) -> Dict[str, int]:
    """Returns granular subscription counts for an issue."""
    rows = (
        db.query(Subscription.status, func.count(Subscription.id))
        .filter(Subscription.issue_id == issue_id)
        .group_by(Subscription.status)
        .all()
    )
    counts = {"confirmed": 0, "pending": 0, "unsubscribed": 0}
    for status, count in rows:
        counts[status] = count
    counts["total"] = sum(counts.values())
    return counts


def get_admin_dashboard_stats(db: Session) -> Dict[str, Any]:
    """Calculate all high-level stats for the admin dashboard."""
    issues = db.query(Issue).all()

    total_issues = len(issues)
    active_issues = sum(1 for i in issues if i.status.lower() not in ("resolved", "closed"))
    
    status_counts = {
        "Investigating": 0,
        "Identified": 0,
        "Fix in development": 0,
        "Monitoring": 0,
        "Resolved": 0,
        "Closed": 0,
    }

    for i in issues:
        status_norm = i.status
        if status_norm in status_counts:
            status_counts[status_norm] += 1
        else:
            status_counts[status_norm] = status_counts.get(status_norm, 0) + 1

    sub_rows = (
        db.query(Subscription.status, func.count(Subscription.id))
        .group_by(Subscription.status)
        .all()
    )
    sub_counts = {"confirmed": 0, "pending": 0, "unsubscribed": 0}
    for status, count in sub_rows:
        sub_counts[status] = count
    sub_counts["total"] = sum(sub_counts.values())

    return {
        "total_issues": total_issues,
        "active_issues": active_issues,
        "investigating": status_counts.get("Investigating", 0),
        "identified": status_counts.get("Identified", 0),
        "fix_in_development": status_counts.get("Fix in development", 0),
        "monitoring": status_counts.get("Monitoring", 0),
        "resolved": status_counts.get("Resolved", 0),
        "closed": status_counts.get("Closed", 0),
        "subscribers": sub_counts,
    }
