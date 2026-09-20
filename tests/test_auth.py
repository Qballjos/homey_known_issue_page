from app.config import settings


def test_admin_login_success(client, admin_user):
    response = client.post(
        "/admin/login",
        data={"email": "testadmin@example.com", "password": "adminSecret123!"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/admin"
    assert settings.SESSION_COOKIE_NAME in response.cookies


def test_admin_login_failure(client, admin_user):
    response = client.post(
        "/admin/login",
        data={"email": "testadmin@example.com", "password": "wrongPassword!"},
        follow_redirects=False,
    )
    assert response.status_code == 401
    assert "Invalid email address or password" in response.text


def test_admin_dashboard_protected_unauthenticated(client):
    response = client.get("/admin", follow_redirects=False)
    assert response.status_code == 303
    assert "/admin/login" in response.headers["location"]


def test_admin_dashboard_authenticated(client, admin_cookies):
    client.cookies.update(admin_cookies)
    response = client.get("/admin")
    assert response.status_code == 200
    assert "System Status Overview" in response.text


def test_admin_logout(client, admin_cookies):
    client.cookies.update(admin_cookies)
    response = client.get("/admin/logout", follow_redirects=False)
    assert response.status_code == 303
    assert "/admin/login" in response.headers["location"]
    # Verify set-cookie in response deleted or expired cookie
    set_cookie_header = response.headers.get("set-cookie", "")
    assert settings.SESSION_COOKIE_NAME in set_cookie_header
    assert ('""' in set_cookie_header or "Max-Age=0" in set_cookie_header or 'deleted' in set_cookie_header)
