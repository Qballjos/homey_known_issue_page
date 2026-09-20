from app.models.issue import Issue


def test_health_check(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


def test_public_api_get_issues(client, db_session):
    issue1 = Issue(
        title="Matter LED strip blinking",
        slug="matter-led-strip-blinking",
        summary="LED strips flash once per minute",
        description="PWM timing glitch",
        status="Investigating",
        severity="Low",
        visibility="Public",
    )
    issue2 = Issue(
        title="Matter bulb unreachable",
        slug="matter-bulb-unreachable",
        summary="Bulbs show offline",
        description="Thread router disconnect",
        status="Monitoring",
        severity="Medium",
        visibility="Public",
    )
    db_session.add_all([issue1, issue2])
    db_session.commit()

    res = client.get("/api/issues")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2

    # Test filtering by status
    res_filtered = client.get("/api/issues?status=Monitoring")
    assert res_filtered.status_code == 200
    assert len(res_filtered.json()) == 1
    assert res_filtered.json()[0]["slug"] == "matter-bulb-unreachable"


def test_api_issue_crud_authorization(client, admin_headers, db_session):
    # 1. Unauthenticated creation should fail with 401
    res_unauth = client.post(
        "/api/issues",
        json={
            "title": "Unauthorized issue attempt",
            "summary": "Should be blocked",
            "description": "No auth header provided",
        }
    )
    assert res_unauth.status_code == 401

    # 2. Authenticated creation should succeed
    res_create = client.post(
        "/api/issues",
        headers=admin_headers,
        json={
            "title": "API Created Issue",
            "summary": "Created via REST API",
            "description": "Full description via REST API",
            "status": "Investigating",
            "severity": "High",
            "visibility": "Public",
            "product_names": ["Homey Pro", "Homey Bridge"],
            "version_strings": ["v13.5.0"],
        }
    )
    assert res_create.status_code == 201
    created = res_create.json()
    issue_id = created["id"]
    assert created["slug"] == "api-created-issue"

    # 3. GET /api/issues/{id} by slug or ID
    res_get = client.get(f"/api/issues/{created['slug']}")
    assert res_get.status_code == 200
    assert res_get.json()["title"] == "API Created Issue"

    # 4. PUT /api/issues/{id}
    res_update = client.put(
        f"/api/issues/{issue_id}",
        headers=admin_headers,
        json={"status": "Fix in development", "workaround": "Restart gateway"}
    )
    assert res_update.status_code == 200
    assert res_update.json()["status"] == "Fix in development"
    assert res_update.json()["workaround"] == "Restart gateway"

    # 5. POST /api/issues/{id}/updates
    res_timeline = client.post(
        f"/api/issues/{issue_id}/updates",
        headers=admin_headers,
        json={
            "title": "Fix verified in staging",
            "description": "All test vectors passed.",
            "notify_subscribers": False
        }
    )
    assert res_timeline.status_code == 201
    assert res_timeline.json()["title"] == "Fix verified in staging"

    # 6. GET /api/admin/stats
    res_stats = client.get("/api/admin/stats", headers=admin_headers)
    assert res_stats.status_code == 200
    stats = res_stats.json()
    assert stats["total_issues"] >= 1

    # 7. DELETE /api/issues/{id}
    res_delete = client.delete(f"/api/issues/{issue_id}", headers=admin_headers)
    assert res_delete.status_code == 200

    # Ensure deleted
    res_deleted = client.get(f"/api/issues/{issue_id}")
    assert res_deleted.status_code == 404
