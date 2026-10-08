import pytest

from tests.conftest import PASSWORD


async def test_admin_requires_login(client):
    response = await client.get("/admin/products/list")

    assert response.status_code == 302
    assert response.headers["location"].endswith("/admin/login")


async def test_admin_login(client):
    response = await client.post("/admin/login", data={"username": "admin", "password": PASSWORD})
    assert response.status_code == 302

    response = await client.get("/admin/products/list")
    assert response.status_code == 200
    assert "Самосвал" in response.text


@pytest.mark.parametrize(
    ("username", "password"),
    [
        ("admin", "wrong-password"),
        ("unknown", PASSWORD),
        # роль USER не даёт доступа в админку
        ("user", PASSWORD),
        ("blocked", PASSWORD),
    ],
)
async def test_admin_login_rejected(client, username, password):
    response = await client.post("/admin/login", data={"username": username, "password": password})

    assert response.status_code == 400
    assert (await client.get("/admin/products/list")).status_code == 302


async def test_registration_is_closed(client):
    response = await client.post("/auth/register", data={"username": "x", "password": "y"})

    assert response.status_code in (404, 405)
