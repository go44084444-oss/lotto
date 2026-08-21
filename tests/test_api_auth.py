def test_register_returns_access_token(client) -> None:
    resp = client.post("/auth/register", json={"email": "a@example.com", "password": "hunter2"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_register_duplicate_email_returns_409(client) -> None:
    client.post("/auth/register", json={"email": "dup@example.com", "password": "hunter2"})
    resp = client.post("/auth/register", json={"email": "dup@example.com", "password": "other"})
    assert resp.status_code == 409


def test_login_with_correct_password_returns_token(client) -> None:
    client.post("/auth/register", json={"email": "login@example.com", "password": "hunter2"})
    resp = client.post("/auth/login", json={"email": "login@example.com", "password": "hunter2"})
    assert resp.status_code == 200
    assert resp.json()["access_token"]


def test_login_with_wrong_password_returns_401(client) -> None:
    client.post("/auth/register", json={"email": "login2@example.com", "password": "hunter2"})
    resp = client.post("/auth/login", json={"email": "login2@example.com", "password": "wrong"})
    assert resp.status_code == 401


def test_login_with_unknown_email_returns_401(client) -> None:
    resp = client.post("/auth/login", json={"email": "nobody@example.com", "password": "x"})
    assert resp.status_code == 401
