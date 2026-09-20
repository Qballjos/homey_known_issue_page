from app.models.issue import Issue
from app.main import RATE_LIMITS


def test_subscribe_rate_limiting(client, db_session):
    issue = Issue(
        title="Wi-Fi 6 dropouts",
        slug="wifi-6-dropouts",
        summary="Intermittent reconnects",
        description="WPA3 handshake failure",
        status="Investigating",
        severity="High",
        visibility="Public",
    )
    db_session.add(issue)
    db_session.commit()

    RATE_LIMITS.clear()

    # The subscription rate limit allows 15 requests/minute
    responses = []
    for i in range(18):
        res = client.post(
            f"/api/issues/{issue.id}/subscribe",
            json={"email": f"flood{i}@example.com"}
        )
        responses.append(res.status_code)

    assert 200 in responses
    assert 429 in responses
    assert responses[-1] == 429


def test_login_rate_limiting(client):
    RATE_LIMITS.clear()

    # Login rate limit allows 8 attempts/minute
    responses = []
    for i in range(10):
        res = client.post(
            "/admin/login",
            data={"email": f"attacker{i}@test.com", "password": "badpassword"}
        )
        responses.append(res.status_code)

    assert 401 in responses
    assert 429 in responses
    assert responses[-1] == 429
