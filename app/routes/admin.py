from typing import Optional, List
from fastapi import APIRouter, Request, Depends, HTTPException, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models.user import User
from app.models.issue import Issue
from app.models.timeline import IssueUpdate
from app.models.subscription import Subscription
from app.models.audit import AuditLog
from app.schemas.issue import IssueCreate, IssueUpdateSchema
from app.config import settings
from app.auth.security import verify_password, create_session_token
from app.auth.dependencies import require_admin_page, get_current_user_optional
from app.services.issue_service import (
    create_issue,
    update_issue,
    add_timeline_update,
    record_audit,
)
from app.services.subscription_service import get_admin_dashboard_stats

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")


def admin_context(request: Request, current_user: User, active_nav: str = "dashboard") -> dict:
    return {
        "request": request,
        "app_name": settings.APP_NAME,
        "current_user": current_user,
        "active_admin_nav": active_nav,
    }


# ============================================================================
# Authentication Routes
# ============================================================================

@router.get("/login", response_class=HTMLResponse)
def login_page(
    request: Request,
    next: Optional[str] = None,
    user=Depends(get_current_user_optional)
):
    if user and user.role == "admin":
        return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        request=request,
        name="admin/login.html",
        context={
            "request": request,
            "app_name": settings.APP_NAME,
            "next_url": next,
            "error": None,
        }
    )


@router.post("/login", response_class=HTMLResponse)
def handle_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    next: Optional[str] = None,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email.strip().lower()).first()

    if not user or not verify_password(password, user.password_hash) or not user.is_active:
        return templates.TemplateResponse(
            request=request,
            name="admin/login.html",
            context={
                "request": request,
                "app_name": settings.APP_NAME,
                "next_url": next,
                "email": email,
                "error": "Invalid email address or password.",
            },
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    # Generate secure signed session token
    token = create_session_token({"user_id": user.id, "email": user.email, "role": user.role})

    target_url = next if (next and next.startswith("/admin")) else "/admin"
    response = RedirectResponse(url=target_url, status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=86400 * 7,
    )
    return response


@router.get("/logout")
def handle_logout():
    response = RedirectResponse(url="/admin/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key=settings.SESSION_COOKIE_NAME)
    return response


# ============================================================================
# Admin Dashboard
# ============================================================================

@router.get("", response_class=HTMLResponse)
def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin_page)
):
    stats = get_admin_dashboard_stats(db)

    recent_updates = (
        db.query(IssueUpdate)
        .order_by(desc(IssueUpdate.created_at))
        .limit(5)
        .all()
    )

    recent_subscriptions = (
        db.query(Subscription)
        .order_by(desc(Subscription.created_at))
        .limit(6)
        .all()
    )

    ctx = admin_context(request, user, active_nav="dashboard")
    ctx.update({
        "stats": stats,
        "recent_updates": recent_updates,
        "recent_subscriptions": recent_subscriptions,
    })
    return templates.TemplateResponse(request=request, name="admin/dashboard.html", context=ctx)


# ============================================================================
# Issue Management
# ============================================================================

@router.get("/issues", response_class=HTMLResponse)
def list_issues(
    request: Request,
    q: Optional[str] = None,
    visibility: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin_page)
):
    query = db.query(Issue)

    if q and q.strip():
        search_pattern = f"%{q.strip()}%"
        query = query.filter(Issue.title.ilike(search_pattern) | Issue.summary.ilike(search_pattern))

    if visibility and visibility.strip():
        query = query.filter(Issue.visibility == visibility.strip())

    issues = query.order_by(desc(Issue.last_updated_at)).all()

    ctx = admin_context(request, user, active_nav="issues")
    ctx.update({
        "issues": issues,
        "search_query": q,
        "selected_visibility": visibility,
    })
    return templates.TemplateResponse(request=request, name="admin/issue_list.html", context=ctx)


@router.get("/issues/new", response_class=HTMLResponse)
def new_issue_form(
    request: Request,
    user: User = Depends(require_admin_page)
):
    ctx = admin_context(request, user, active_nav="new_issue")
    ctx.update({"issue": None})
    return templates.TemplateResponse(request=request, name="admin/issue_editor.html", context=ctx)


@router.post("/issues/new")
def handle_new_issue(
    request: Request,
    title: str = Form(...),
    summary: str = Form(...),
    description: str = Form(...),
    status: str = Form("Investigating"),
    severity: str = Form("Medium"),
    visibility: str = Form("Public"),
    product_names: Optional[str] = Form(""),
    version_strings: Optional[str] = Form(""),
    workaround: Optional[str] = Form(None),
    expected_fix: Optional[str] = Form(None),
    fixed_version: Optional[str] = Form(None),
    min_subscribers_threshold: int = Form(0),
    auto_publish_on_threshold: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin_page)
):
    prods = [p.strip() for p in (product_names or "").split(",") if p.strip()]
    vers = [v.strip() for v in (version_strings or "").split(",") if v.strip()]

    data = IssueCreate(
        title=title,
        summary=summary,
        description=description,
        status=status,
        severity=severity,
        visibility=visibility,
        product_names=prods,
        version_strings=vers,
        workaround=workaround,
        expected_fix=expected_fix,
        fixed_version=fixed_version,
        min_subscribers_threshold=min_subscribers_threshold,
        auto_publish_on_threshold=bool(auto_publish_on_threshold),
    )

    issue = create_issue(db, data, user=user)
    return RedirectResponse(url=f"/admin/issues/{issue.id}/edit", status_code=303)


@router.get("/issues/{issue_id}/edit", response_class=HTMLResponse)
def edit_issue_form(
    issue_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin_page)
):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    ctx = admin_context(request, user, active_nav="issues")
    ctx.update({"issue": issue})
    return templates.TemplateResponse(request=request, name="admin/issue_editor.html", context=ctx)


@router.post("/issues/{issue_id}/edit")
def handle_edit_issue(
    issue_id: str,
    title: str = Form(...),
    summary: str = Form(...),
    description: str = Form(...),
    status: str = Form("Investigating"),
    severity: str = Form("Medium"),
    visibility: str = Form("Public"),
    product_names: Optional[str] = Form(""),
    version_strings: Optional[str] = Form(""),
    workaround: Optional[str] = Form(None),
    expected_fix: Optional[str] = Form(None),
    fixed_version: Optional[str] = Form(None),
    min_subscribers_threshold: int = Form(0),
    auto_publish_on_threshold: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin_page)
):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    prods = [p.strip() for p in (product_names or "").split(",") if p.strip()]
    vers = [v.strip() for v in (version_strings or "").split(",") if v.strip()]

    data = IssueUpdateSchema(
        title=title,
        summary=summary,
        description=description,
        status=status,
        severity=severity,
        visibility=visibility,
        product_names=prods,
        version_strings=vers,
        workaround=workaround,
        expected_fix=expected_fix,
        fixed_version=fixed_version,
        min_subscribers_threshold=min_subscribers_threshold,
        auto_publish_on_threshold=bool(auto_publish_on_threshold),
    )

    update_issue(db, issue, data, user=user)
    return RedirectResponse(url=f"/admin/issues/{issue.id}/edit", status_code=303)


@router.post("/issues/{issue_id}/updates")
def handle_add_timeline_update(
    issue_id: str,
    title: str = Form(...),
    description: str = Form(...),
    new_status: Optional[str] = Form(None),
    notify_subscribers: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin_page)
):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    should_notify = bool(notify_subscribers)
    status_change = new_status if (new_status and new_status.strip()) else None

    add_timeline_update(
        db=db,
        issue=issue,
        title=title,
        description=description,
        notify_subscribers=should_notify,
        new_status=status_change,
        user=user,
    )

    return RedirectResponse(url=f"/admin/issues/{issue.id}/edit", status_code=303)


@router.post("/issues/{issue_id}/delete")
def handle_delete_issue(
    issue_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin_page)
):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    record_audit(
        db,
        action="ISSUE_DELETED",
        entity_id=issue.id,
        user=user,
        details={"deleted_title": issue.title}
    )

    db.delete(issue)
    db.commit()

    return RedirectResponse(url="/admin/issues", status_code=303)


# ============================================================================
# Audit Logs
# ============================================================================

@router.get("/audit", response_class=HTMLResponse)
def view_audit_log(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin_page)
):
    logs = db.query(AuditLog).order_by(desc(AuditLog.created_at)).limit(100).all()

    ctx = admin_context(request, user, active_nav="audit")
    ctx.update({"audit_logs": logs})
    return templates.TemplateResponse(request=request, name="admin/audit_log.html", context=ctx)
