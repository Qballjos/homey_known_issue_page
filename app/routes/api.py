from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from app.database import get_db
from app.models.issue import Issue
from app.models.product import Product
from app.models.user import User
from app.schemas.issue import (
    IssueCreate,
    IssueUpdateSchema,
    IssueSummaryOut,
    IssueDetailOut,
    TimelineUpdateCreate,
    TimelineUpdateOut,
)
from app.schemas.subscription import (
    SubscribeRequest,
    SubscribeResponse,
    ConfirmRequest,
    UnsubscribeRequest,
    AdminStatsResponse,
)
from app.auth.dependencies import require_admin_api
from app.services.issue_service import (
    create_issue,
    update_issue,
    add_timeline_update,
    record_audit,
)
from app.services.subscription_service import (
    subscribe_to_issue,
    confirm_subscription,
    unsubscribe,
    get_admin_dashboard_stats,
)

router = APIRouter(prefix="/api", tags=["REST API"])


# ============================================================================
# Issues Endpoints
# ============================================================================

@router.get("/issues", response_model=List[IssueSummaryOut])
def get_issues(
    q: Optional[str] = None,
    status: Optional[str] = None,
    product: Optional[str] = None,
    visibility: str = "Public",
    db: Session = Depends(get_db)
):
    """List issues filtered by search query, status, product, or visibility."""
    query = db.query(Issue)

    if visibility:
        query = query.filter(Issue.visibility == visibility)

    if status:
        query = query.filter(Issue.status == status)

    if q and q.strip():
        search_pattern = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Issue.title.ilike(search_pattern),
                Issue.summary.ilike(search_pattern),
                Issue.description.ilike(search_pattern),
            )
        )

    if product and product.strip():
        query = query.join(Issue.products).filter(Product.name == product.strip())

    issues = query.order_by(desc(Issue.last_updated_at)).all()
    
    # Attach computed subscriber count
    result = []
    for iss in issues:
        iss_out = IssueSummaryOut.model_validate(iss)
        iss_out.subscribers_count = iss.confirmed_subscribers_count
        result.append(iss_out)
    return result


@router.get("/issues/{id_or_slug}", response_model=IssueDetailOut)
def get_issue(id_or_slug: str, db: Session = Depends(get_db)):
    """Retrieve full issue detail by ID or Slug."""
    issue = db.query(Issue).filter(Issue.id == id_or_slug).first()
    if not issue:
        issue = db.query(Issue).filter(Issue.slug == id_or_slug).first()

    if not issue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")

    detail = IssueDetailOut.model_validate(issue)
    detail.subscribers_count = issue.confirmed_subscribers_count
    return detail


@router.post("/issues", response_model=IssueDetailOut, status_code=status.HTTP_201_CREATED)
def create_new_issue(
    data: IssueCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin_api)
):
    """Create a new issue (Admin only)."""
    issue = create_issue(db, data, user=admin)
    detail = IssueDetailOut.model_validate(issue)
    detail.subscribers_count = issue.confirmed_subscribers_count
    return detail


@router.put("/issues/{issue_id}", response_model=IssueDetailOut)
def update_existing_issue(
    issue_id: str,
    data: IssueUpdateSchema,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin_api)
):
    """Update an existing issue (Admin only)."""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")

    updated = update_issue(db, issue, data, user=admin)
    detail = IssueDetailOut.model_validate(updated)
    detail.subscribers_count = updated.confirmed_subscribers_count
    return detail


@router.delete("/issues/{issue_id}", status_code=status.HTTP_200_OK)
def delete_existing_issue(
    issue_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin_api)
):
    """Delete an issue (Admin only)."""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")

    record_audit(
        db,
        action="ISSUE_DELETED",
        entity_id=issue.id,
        user=admin,
        details={"title": issue.title}
    )
    db.delete(issue)
    db.commit()
    return {"message": "Issue successfully deleted", "id": issue_id}


@router.post("/issues/{issue_id}/updates", response_model=TimelineUpdateOut, status_code=status.HTTP_201_CREATED)
def post_timeline_update(
    issue_id: str,
    data: TimelineUpdateCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin_api)
):
    """Add a timeline update and optionally notify subscribers (Admin only)."""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")

    update, notified_count = add_timeline_update(
        db=db,
        issue=issue,
        title=data.title,
        description=data.description,
        notify_subscribers=data.notify_subscribers,
        new_status=data.status_update,
        user=admin,
    )
    return update


# ============================================================================
# Subscription Endpoints (Double Opt-In)
# ============================================================================

@router.post("/issues/{issue_id}/subscribe", response_model=SubscribeResponse)
def subscribe_endpoint(
    issue_id: str,
    payload: SubscribeRequest,
    db: Session = Depends(get_db)
):
    """
    Subscribe to an issue with Double Opt-In.
    Sends a verification email with a secure confirmation token.
    """
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        # Check by slug
        issue = db.query(Issue).filter(Issue.slug == issue_id).first()

    if not issue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")

    sub, status_msg = subscribe_to_issue(db, issue, payload.email)

    if status_msg == "already_confirmed":
        return SubscribeResponse(
            message="You are already actively subscribed to updates for this issue.",
            status="already_subscribed",
            email=payload.email
        )

    return SubscribeResponse(
        message="Verification email sent. Please check your inbox and click the confirmation link to activate updates.",
        status="pending_confirmation",
        email=payload.email
    )


@router.post("/subscriptions/confirm")
def confirm_subscription_endpoint(
    payload: ConfirmRequest,
    db: Session = Depends(get_db)
):
    """Confirm email subscription using confirmation token."""
    success, sub, message = confirm_subscription(db, payload.token)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    return {
        "status": "success",
        "message": message,
        "issue_id": sub.issue_id,
        "email": sub.email
    }


@router.post("/subscriptions/unsubscribe")
def unsubscribe_endpoint(
    payload: UnsubscribeRequest,
    db: Session = Depends(get_db)
):
    """Unsubscribe using token."""
    success, sub, message = unsubscribe(db, payload.token)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    return {
        "status": "success",
        "message": message,
        "issue_id": sub.issue_id,
        "email": sub.email
    }


# ============================================================================
# Admin Stats Endpoint
# ============================================================================

@router.get("/admin/stats", response_model=AdminStatsResponse)
def get_admin_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin_api)
):
    """Get high-level dashboard statistics (Admin only)."""
    return get_admin_dashboard_stats(db)
