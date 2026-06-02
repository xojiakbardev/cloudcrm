"""End-to-end API tests covering auth, CRM CRUD, dashboard, and infrastructure."""


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_login_success(client):
    resp = client.post(
        "/api/auth/login",
        data={"username": "admin@cloudcrm.dev", "password": "admin123"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["user"]["email"] == "admin@cloudcrm.dev"


def test_login_wrong_password(client):
    resp = client.post(
        "/api/auth/login",
        data={"username": "admin@cloudcrm.dev", "password": "wrong"},
    )
    assert resp.status_code == 401


def test_customers_require_auth(client):
    resp = client.get("/api/customers")
    assert resp.status_code == 401


def test_customer_crud(client, auth_headers):
    # Create
    resp = client.post(
        "/api/customers",
        json={"name": "Test Co", "email": "t@test.uz", "status": "lead"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    cid = resp.json()["id"]

    # Read list
    resp = client.get("/api/customers", headers=auth_headers)
    assert resp.status_code == 200
    assert any(c["id"] == cid for c in resp.json())

    # Update
    resp = client.put(
        f"/api/customers/{cid}",
        json={"name": "Test Co", "email": "t@test.uz", "status": "active"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "active"

    # Delete
    resp = client.delete(f"/api/customers/{cid}", headers=auth_headers)
    assert resp.status_code == 204


def test_deal_creation_validates_customer(client, auth_headers):
    resp = client.post(
        "/api/deals",
        json={"title": "X", "amount": 100, "stage": "new", "customer_id": 99999},
        headers=auth_headers,
    )
    assert resp.status_code == 404


def test_dashboard_stats(client, auth_headers):
    resp = client.get("/api/dashboard/stats", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "total_customers" in body
    assert "deals_by_stage" in body


def test_infrastructure_ping_and_topology(client, auth_headers):
    # Ping is public and registers/updates this instance.
    resp = client.get("/api/infrastructure/ping")
    assert resp.status_code == 200
    assert "served_by" in resp.json()

    # Topology should include the core nodes.
    resp = client.get("/api/infrastructure/topology", headers=auth_headers)
    assert resp.status_code == 200
    node_types = {n["type"] for n in resp.json()["nodes"]}
    assert {"gateway", "loadbalancer", "database"}.issubset(node_types)
