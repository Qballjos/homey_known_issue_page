from app.models.issue import Issue
from app.models.subscription import Subscription
from app.email.service import outbox


def test_double_opt_in_subscription_flow(client, db_session):
    issue = Issue(
        title="Matter commissioning failure",
        slug="matter-commissioning-failure",
        summary="Commissioning times out",
        description="Thread network joining failure",
        status="Investigating",
        severity="High",
        visibility="Public",
    )
    db_session.add(issue)
    db_session.commit()
    db_session.refresh(issue)

    # 1. User submits subscription
    outbox.clear()
    res_sub = client.post(
        f"/api/issues/{issue.id}/subscribe",
        json={"email": "alice@smarthome.test"}
    )
    assert res_sub.status_code == 200
    data = res_sub.json()
    assert data["status"] == "pending_confirmation"

    # Verify subscription in database is pending
    sub = db_session.query(Subscription).filter(
        Subscription.issue_id == issue.id,
        Subscription.email == "alice@smarthome.test"
    ).first()
    assert sub is not None
    assert sub.status == "pending"

    # Verify confirmation email was sent to outbox
    assert len(outbox) == 1
    assert outbox[0]["to"] == "alice@smarthome.test"
    assert "confirm" in outbox[0]["subject"].lower()
    assert sub.confirmation_token in outbox[0]["text"]

    # 2. User clicks confirmation link
    res_confirm = client.get(f"/subscribe/confirm?token={sub.confirmation_token}")
    assert res_confirm.status_code == 200
    assert "Subscription Confirmed" in res_confirm.text

    db_session.refresh(sub)
    assert sub.status == "confirmed"
    assert sub.confirmed_at is not None

    # 3. Subscribing again when already confirmed
    res_sub_again = client.post(
        f"/api/issues/{issue.id}/subscribe",
        json={"email": "alice@smarthome.test"}
    )
    assert res_sub_again.status_code == 200
    assert res_sub_again.json()["status"] == "already_subscribed"

    # 4. User unsubscriptions
    res_unsub = client.get(f"/unsubscribe/{sub.unsubscribe_token}")
    assert res_unsub.status_code == 200
    assert "You have been unsubscribed" in res_unsub.text

    db_session.refresh(sub)
    assert sub.status == "unsubscribed"
    assert sub.unsubscribed_at is not None


def test_invalid_confirmation_and_unsub_tokens(client):
    res1 = client.get("/subscribe/confirm?token=completely-invalid-token")
    assert res1.status_code == 400

    res2 = client.get("/unsubscribe/completely-invalid-token")
    assert res2.status_code == 400
