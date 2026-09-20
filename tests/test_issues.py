from app.models.issue import Issue
from app.models.subscription import Subscription
from app.auth.security import generate_secure_token
from app.services.issue_service import check_and_apply_threshold_publishing


def test_create_issue_via_admin(client, admin_cookies, db_session):
    client.cookies.update(admin_cookies)
    response = client.post(
        "/admin/issues/new",
        data={
            "title": "Zigbee motion sensor timeout",
            "summary": "Motion sensors fail to report occupancy events",
            "description": "Battery powered sensors drop parent routing table entries.",
            "status": "Investigating",
            "severity": "High",
            "visibility": "Public",
            "product_names": "Homey Pro, Homey Bridge",
            "version_strings": "OS 13.5.0",
            "workaround": "Press sync button once every 24h",
            "expected_fix": "Mesh table routing patch",
            "fixed_version": "",
            "min_subscribers_threshold": "0",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Zigbee motion sensor timeout" in response.text

    issue = db_session.query(Issue).filter(Issue.slug == "zigbee-motion-sensor-timeout").first()
    assert issue is not None
    assert issue.status == "Investigating"
    assert issue.severity == "High"
    assert len(issue.products) == 2
    assert len(issue.updates) == 1  # Initial confirmation update created


def test_draft_issue_visibility(client, admin_cookies, db_session):
    client.cookies.update(admin_cookies)
    client.post(
        "/admin/issues/new",
        data={
            "title": "Internal testing bug not for public",
            "summary": "Confidential hardware glitch",
            "description": "Engineering reproduction underway.",
            "status": "Investigating",
            "severity": "Low",
            "visibility": "Draft",
            "product_names": "Homey Pro",
            "version_strings": "",
            "min_subscribers_threshold": "0",
        },
        follow_redirects=True,
    )

    issue = db_session.query(Issue).filter(Issue.slug == "internal-testing-bug-not-for-public").first()
    assert issue is not None
    assert issue.visibility == "Draft"

    # Public client cannot see it on index
    public_client = client
    public_client.cookies.clear()
    res_public = public_client.get("/")
    assert "Internal testing bug not for public" not in res_public.text

    # Detail page returns 404 for unauthenticated public user
    res_detail = public_client.get(f"/issues/{issue.slug}")
    assert res_detail.status_code == 404


def test_issue_status_resolved_sets_resolved_at(client, admin_cookies, db_session):
    client.cookies.update(admin_cookies)
    client.post(
        "/admin/issues/new",
        data={
            "title": "Bluetooth pairing crash",
            "summary": "App crashes when discovering BLE devices",
            "description": "Stack overflow in discovery handler.",
            "status": "Investigating",
            "severity": "Critical",
            "visibility": "Public",
            "product_names": "Homey Pro",
            "min_subscribers_threshold": "0",
        },
        follow_redirects=True,
    )
    issue = db_session.query(Issue).filter(Issue.slug == "bluetooth-pairing-crash").first()
    assert issue.resolved_at is None

    # Update status to Resolved
    client.post(
        f"/admin/issues/{issue.id}/updates",
        data={
            "title": "Fixed in Firmware v13.5.2",
            "description": "The discovery buffer was resized and verified.",
            "new_status": "Resolved",
        },
        follow_redirects=True,
    )
    db_session.refresh(issue)
    assert issue.status == "Resolved"
    assert issue.resolved_at is not None


def test_auto_publish_on_threshold(db_session):
    issue = Issue(
        title="Hidden issue waiting for threshold",
        slug="hidden-issue-waiting-for-threshold",
        summary="Some summary",
        description="Detailed description",
        status="Investigating",
        severity="Medium",
        visibility="Internal",
        min_subscribers_threshold=3,
        auto_publish_on_threshold=True,
    )
    db_session.add(issue)
    db_session.flush()

    # Add 2 confirmed subscribers (below threshold of 3)
    for i in range(2):
        sub = Subscription(
            issue_id=issue.id,
            email=f"sub{i}@test.com",
            status="confirmed",
            confirmation_token=generate_secure_token(16),
            unsubscribe_token=generate_secure_token(16),
        )
        db_session.add(sub)
    db_session.commit()

    published = check_and_apply_threshold_publishing(db_session, issue)
    assert published is False
    assert issue.visibility == "Internal"

    # Add 3rd subscriber (reaching threshold of 3)
    sub3 = Subscription(
        issue_id=issue.id,
        email="sub3@test.com",
        status="confirmed",
        confirmation_token=generate_secure_token(16),
        unsubscribe_token=generate_secure_token(16),
    )
    db_session.add(sub3)
    db_session.commit()

    published = check_and_apply_threshold_publishing(db_session, issue)
    assert published is True
    assert issue.visibility == "Public"
