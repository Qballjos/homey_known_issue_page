from typing import Optional
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from app.database import get_db
from app.models.issue import Issue
from app.models.product import Product
from app.models.subscription import Subscription
from app.config import settings
from app.auth.dependencies import get_current_user_optional
from app.services.subscription_service import confirm_subscription, unsubscribe

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def common_context(request: Request, current_user=None) -> dict:
    return {
        "request": request,
        "app_name": settings.APP_NAME,
        "current_user": current_user,
    }


@router.get("/", response_class=HTMLResponse)
def index_page(
    request: Request,
    q: Optional[str] = None,
    status: Optional[str] = None,
    product: Optional[str] = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional)
):
    query = db.query(Issue).filter(Issue.visibility == "Public")

    # Count total active public issues (not resolved/closed)
    active_count = (
        db.query(Issue)
        .filter(Issue.visibility == "Public", ~Issue.status.in_(["Resolved", "Closed"]))
        .count()
    )

    # Filter out resolved/closed on the main index unless specifically filtered
    if status:
        query = query.filter(Issue.status == status)
    else:
        query = query.filter(~Issue.status.in_(["Resolved", "Closed"]))

    if q and q.strip():
        search_pattern = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Issue.title.ilike(search_pattern),
                Issue.summary.ilike(search_pattern),
                Issue.description.ilike(search_pattern),
                Issue.workaround.ilike(search_pattern),
            )
        )

    if product and product.strip():
        query = query.join(Issue.products).filter(Product.name == product.strip())

    issues = query.order_by(desc(Issue.last_updated_at)).all()
    available_products = db.query(Product).order_by(Product.name).all()

    ctx = common_context(request, user)
    ctx.update({
        "issues": issues,
        "active_issues_count": active_count,
        "available_products": available_products,
        "search_query": q,
        "selected_status": status,
        "selected_product": product,
        "active_nav": "issues",
    })
    return templates.TemplateResponse(request=request, name="public/index.html", context=ctx)


@router.get("/issues/{slug}", response_class=HTMLResponse)
def issue_detail_page(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional)
):
    issue = db.query(Issue).filter(Issue.slug == slug).first()
    if not issue:
        issue = db.query(Issue).filter(Issue.id == slug).first()

    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    if issue.visibility in ("Draft", "Internal") and (not user or user.role != "admin"):
        raise HTTPException(status_code=404, detail="Issue not found")

    ctx = common_context(request, user)
    ctx.update({
        "issue": issue,
        "active_nav": "issues",
    })
    return templates.TemplateResponse(request=request, name="public/issue_detail.html", context=ctx)


@router.get("/resolved", response_class=HTMLResponse)
def resolved_archive_page(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional)
):
    resolved_issues = (
        db.query(Issue)
        .filter(or_(Issue.status == "Resolved", Issue.visibility == "Resolved"))
        .order_by(desc(Issue.resolved_at), desc(Issue.last_updated_at))
        .all()
    )

    ctx = common_context(request, user)
    ctx.update({
        "resolved_issues": resolved_issues,
        "active_nav": "resolved",
    })
    return templates.TemplateResponse(request=request, name="public/resolved.html", context=ctx)


@router.get("/subscribe/confirm", response_class=HTMLResponse)
def confirm_subscription_page(
    token: str,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional)
):
    success, sub, message = confirm_subscription(db, token)
    if not success or not sub:
        raise HTTPException(status_code=400, detail=message)

    ctx = common_context(request, user)
    ctx.update({
        "issue": sub.issue,
        "subscription": sub,
    })
    return templates.TemplateResponse(request=request, name="public/confirm_success.html", context=ctx)


@router.get("/unsubscribe/{token}", response_class=HTMLResponse)
def unsubscribe_page(
    token: str,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_optional)
):
    success, sub, message = unsubscribe(db, token)
    if not success or not sub:
        raise HTTPException(status_code=400, detail=message)

    ctx = common_context(request, user)
    ctx.update({
        "issue": sub.issue,
        "subscription": sub,
    })
    return templates.TemplateResponse(request=request, name="public/unsubscribe_success.html", context=ctx)


@router.get("/privacy", response_class=HTMLResponse)
def privacy_page(
    request: Request,
    user=Depends(get_current_user_optional)
):
    ctx = common_context(request, user)
    return templates.TemplateResponse(request=request, name="public/privacy.html", context=ctx)
