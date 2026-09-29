"""One user must never be able to read another user's cases, documents or activity."""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _login(name: str) -> dict[str, str]:
    email = f"{name}-{uuid.uuid4().hex[:8]}@example.com"
    created = client.post("/api/v1/users", json={"full_name": f"Test {name}", "email": email, "password": "password123"})
    assert created.status_code == 201, created.text
    token = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def setup() -> dict[str, str]:
    owner, other = _login("owner"), _login("other")
    case = client.post("/api/v1/cases", headers=owner, json={
        "title": "Lease dispute", "case_number": "CV-1", "client_name": "Acme",
        "opposing_party": "Beta", "court": "District", "description": "Test case",
    })
    assert case.status_code == 201, case.text
    case_id = case.json()["id"]
    doc = client.post(
        "/api/v1/documents/upload", headers=owner, data={"case_id": case_id},
        files={"file": ("lease.txt", b"The Tenant shall maintain liability insurance.", "text/plain")},
    )
    assert doc.status_code == 200, doc.text
    return {"case": case_id, "doc": doc.json()["id"], **{f"owner_{k}": v for k, v in owner.items()},
            **{f"other_{k}": v for k, v in other.items()}}


def _headers(setup: dict[str, str], who: str) -> dict[str, str]:
    return {"Authorization": setup[f"{who}_Authorization"]}


@pytest.mark.parametrize("method,path", [
    ("get", "/api/v1/cases/{case}/search?query=insurance"),
    ("post", "/api/v1/ai/cases/{case}/synthesis"),
    ("get", "/api/v1/audit-logs/cases/{case}"),
    ("get", "/api/v1/audit-logs/documents/{doc}"),
    ("get", "/api/v1/documents/{doc}"),
])
def test_other_users_cannot_access(setup: dict[str, str], method: str, path: str) -> None:
    url = path.format(case=setup["case"], doc=setup["doc"])
    assert getattr(client, method)(url, headers=_headers(setup, "other")).status_code == 404
    assert getattr(client, method)(url, headers=_headers(setup, "owner")).status_code == 200


def test_user_list_needs_admin(setup: dict[str, str]) -> None:
    assert client.get("/api/v1/users").status_code == 401
    assert client.get("/api/v1/users", headers=_headers(setup, "owner")).status_code == 403
