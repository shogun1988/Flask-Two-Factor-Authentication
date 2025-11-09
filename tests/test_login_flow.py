import uuid


def register_user(client, username: str, password: str):
    return client.post(
        "/register",
        data={"username": username, "password": password, "confirm": password},
        follow_redirects=True,
    )


def test_wrong_password_stays_on_login(client):
    # Arrange: register a user
    uname = f"user_{uuid.uuid4().hex[:8]}"
    pwd = "CorrectPass123!"
    resp = register_user(client, uname, pwd)
    assert resp.status_code == 200
    # Registration flow logs the user in; log out to simulate a fresh login attempt
    client.get("/logout", follow_redirects=True)

    # Act: attempt login with wrong password
    resp = client.post(
        "/login",
        data={"username": uname, "password": "WrongPass!"},
        follow_redirects=True,
    )

    # Assert: should remain on login page with error flash
    assert resp.status_code == 200
    body = resp.data.decode()
    assert "Please sign in" in body  # login page heading
    assert "Invalid username and/or password." in body


def test_unknown_user_shows_register_prompt(client):
    # Act: attempt login with non-existent user
    resp = client.post(
        "/login",
        data={"username": "no_such_user", "password": "anything"},
        follow_redirects=True,
    )

    # Assert: should remain on login page with not registered message
    assert resp.status_code == 200
    body = resp.data.decode()
    assert "Please sign in" in body
    assert "You are not registered. Please register." in body
