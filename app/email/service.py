import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Dict, Any
from app.config import settings

logger = logging.getLogger("email_service")

# In-memory outbox for testing, inspection, and development without active SMTP
outbox: List[Dict[str, Any]] = []


def send_email(to_email: str, subject: str, text_body: str, html_body: str) -> bool:
    """Send an email using configured SMTP, or fallback to the in-memory outbox."""
    logger.info(f"Preparing email to: {to_email} | Subject: {subject}")

    # Record to outbox for inspection/tests
    email_record = {
        "to": to_email,
        "subject": subject,
        "text": text_body,
        "html": html_body,
    }
    outbox.append(email_record)

    if not settings.SMTP_HOST:
        logger.info(f"SMTP not configured. Email to {to_email} captured in outbox (total {len(outbox)}).")
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM
        msg["To"] = to_email

        part1 = MIMEText(text_body, "plain", "utf-8")
        part2 = MIMEText(html_body, "html", "utf-8")
        msg.attach(part1)
        msg.attach(part2)

        if settings.SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15)
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15)
            if settings.SMTP_TLS:
                server.starttls()

        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)

        server.sendmail(settings.SMTP_FROM, [to_email], msg.as_string())
        server.quit()
        logger.info(f"Email successfully delivered to {to_email} via {settings.SMTP_HOST}")
        return True
    except Exception as exc:
        logger.error(f"Failed to send email to {to_email} via SMTP: {exc}")
        return False
