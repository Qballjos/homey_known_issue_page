from app.models.issue import Issue
from app.models.subscription import Subscription
from app.auth.security import generate_secure_token
from app.email.service import outbox


def test_timeline_update_notifies_confirmed_subscribers(client, admin_cookies, db_session):
    issue = Issue(
        title="Z-Wave range degradation",
        slug="zwave-range-degradation",
        summary="Signal strength drops in 800-series nodes",
        description="Attenuation issue detected in radio driver.",
        status="Investigating",
        severity="Medium",
        visibility="Public",
    )
    db_session.add(issue)
    db_session.commit()

    # Create 2 confirmed subscribers, 1 pending, 1 unsubscribed
    sub1 = Subscription(
        issue_id=issue.id,
        email="user1@example.com",
        status="confirmed",
        confirmation_token=generate_secure_token(16),
        unsubscribe_token="unsub-user-1",
    )
    sub2 = Subscription(
        issue_id=issue.id,
        email="user2@example.com",
        status="confirmed",
        confirmation_token=generate_secure_token(16),
        unsubscribe_token="unsub-user-2",
    )
    sub_pending = Subscription(
        issue_id=issue.id,
        email="pending@example.com",
        status="pending",
        confirmation_token=generate_secure_token(16),
        unsubscribe_token="unsub-pending",
    )
    sub_unsub = Subscription(
        issue_id=issue.id,
        email="unsub@example.com",
        status="unsubscribed",
        confirmation_token=generate_secure_token(16),
        unsubscribe_token="unsub-unsub",
    )
    db_session.add_all([sub1, sub2, sub_pending, sub_unsub])
    db_session.commit()

    outbox.clear()
    client.cookies.update(admin_cookies)

    # 1. Post timeline update with notifications enabled
    res = client.post(
        f"/admin/issues/{issue.id}/updates",
        data={
            "title": "Patch in testing lab",
            "description": "Z-Wave radio power output calibration completed.",
            "new_status": "Fix in development",
            "notify_subscribers": "true",
        },
        follow_redirects=True,
    )
    assert res.status_code == 200

    # Verify emails in outbox
    recipients = [email["to"] for email in outbox]
    assert len(recipients) == 2
    assert "user1@example.com" in recipients
    assert "user2@example.com" in recipients
    assert "pending@example.com" not in recipients
    assert "unsub@example.com" not in recipients

    # Verify body contains status change, update content, and unsubscribe token
    email_for_user1 = next(e for e in outbox if e["to"] == "user1@example.com")
    assert "Fix in development" in email_for_user1["text"]
    assert "Patch in testing lab" in email_for_user1["text"]
    assert "unsub-user-1" in email_for_user1["text"]

    # 2. Post silent update (e.g. minor typo fix) with notify_subscribers unchecked
    outbox.clear()
    res_silent = client.post(
        f"/admin/issues/{issue.id}/updates",
        data={
            "title": "Internal documentation updated",
            "description": "Small typo fix in technical specs.",
        },
        follow_redirects=True,
    )
    assert res_silent.status_code == 200
    assert len(outbox) == 0
