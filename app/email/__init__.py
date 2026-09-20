from app.email.service import send_email, outbox
from app.email.templates import get_confirmation_email, get_issue_update_email

__all__ = ["send_email", "outbox", "get_confirmation_email", "get_issue_update_email"]
